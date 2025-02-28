package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"
	"bufio"
	
	"github.com/skip2/go-qrcode"
	_ "github.com/mattn/go-sqlite3"
 	//_ "modernc.org/sqlite"
)

// Configuration holds the application settings loaded from app.config
type Configuration struct {
	DBFilename string
	DBPath     string
	// Add other configuration parameters as needed
}

// LoadConfig reads configuration from app.config file
func LoadConfig() (Configuration, error) {
	config := Configuration{
		// Default values if config file doesn't exist or specific keys are missing
		DBFilename: "hardware_info2.db",
		DBPath:     ".",
	}

	// Try to open the app.config file
	data, err := os.ReadFile("app.config")
	if err != nil {
		return config, fmt.Errorf("warning: could not read app.config: %v (using defaults)", err)
	}

	// Parse the config file (key=value format)
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue // Skip empty lines and comments
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue // Skip invalid lines
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])

		// Assign values to corresponding config fields
		switch key {
		case "DB_FILENAME":
			config.DBFilename = value
		case "DB_PATH":
			config.DBPath = value
		// Add more cases for additional parameters
		}
	}

	return config, nil
}

type SystemInfo struct {
	Username             string `json:"Username"`
	Hostname             string `json:"Hostname"`
	SerialNumber         string `json:"SerialNumber"`
	Processor            string `json:"Processor"`
	WindowsVersion       string `json:"WindowsVersion"`
	WindowsDisplayVersion string `json:"WindowsDisplayVersion"`
	Manufacturer         string `json:"Manufacturer"`
	Model                string `json:"Model"`
	TotalRAM             string `json:"TotalRAM"`
	NumRamSlots          string `json:"NumRamSlots"`
	RamPerSlot           string `json:"RamPerSlot"`
	RamSpeed             string `json:"RamSpeed"`
	RamType              string `json:"RamType"`
	IPAddress            string `json:"IPAddress"`
	MacAddress           string `json:"MacAddress"`
	//FormattedMac         string `json:"FormattedMac"`
	CitrixName           string `json:"CitrixName"`
	CitrixVersion        string `json:"CitrixVersion"`
	CollectionDate       string `json:"CollectionDate"`
}

// RAM type mapping
var ramTypeMap = map[string]string{
	"20": "DDR",
	"21": "DDR2",
	"24": "DDR3",
	"26": "DDR4",
	"29": "DDR5",
}

// RunCommand executes a Windows command and returns the output as a string
func RunCommand(cmdArgs ...string) string {
	cmd := exec.Command("cmd", append([]string{"/C"}, cmdArgs...)...)
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error executing command:", err)
		return "Unknown"
	}
	return strings.TrimSpace(out.String())
}

// ExtractValue extracts values from command output
func ExtractValue(output string) string {
	lines := strings.Split(output, "\n")
	if len(lines) > 1 {
		return strings.TrimSpace(lines[1])
	}
	return "Unknown"
}

// SearchRegistry searches the Windows registry for software information
func SearchRegistry(hive, path, searchPattern string) (string, string) {
	output := RunCommand("reg", "query", fmt.Sprintf("%s\\%s", hive, path), "/s")
	if output == "Unknown" {
		return "Not found", "Not found"
	}

	lines := strings.Split(output, "\n")
	var displayName, displayVersion string

	for _, line := range lines {
		lowerLine := strings.ToLower(line)
		if strings.Contains(lowerLine, "displayname") && strings.Contains(lowerLine, strings.ToLower(searchPattern)) {
			parts := strings.SplitN(line, "REG_SZ", 2)
			if len(parts) > 1 {
				displayName = strings.TrimSpace(parts[1])
			}
		}
		if strings.Contains(lowerLine, "displayversion") && displayName != "" {
			parts := strings.SplitN(line, "REG_SZ", 2)
			if len(parts) > 1 {
				displayVersion = strings.TrimSpace(parts[1])
			}
		}
		if displayName != "" && displayVersion != "" {
			return displayName, displayVersion
		}
	}

	return "Not found", "Not found"
}

// GatherInfo collects system details
func (s *SystemInfo) GatherInfo() {
	// Get logged-in username
	s.Username = os.Getenv("USERNAME")

	// Get basic system information
	s.Hostname = ExtractValue(RunCommand("wmic", "computersystem", "get", "name"))
	s.SerialNumber = ExtractValue(RunCommand("wmic", "bios", "get", "serialnumber"))
	s.Processor = ExtractValue(RunCommand("wmic", "cpu", "get", "name"))
	s.WindowsVersion = ExtractValue(RunCommand("wmic", "os", "get", "caption"))

	// Get Windows display version
	displayVersionOutput := RunCommand("reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "/v", "DisplayVersion")
	re := regexp.MustCompile(`DisplayVersion\s+REG_SZ\s+(\S+)`)
	matches := re.FindStringSubmatch(displayVersionOutput)
	if len(matches) > 1 {
		s.WindowsDisplayVersion = matches[1]
	} else {
		s.WindowsDisplayVersion = "Unknown"
	}

	s.Manufacturer = ExtractValue(RunCommand("wmic", "computersystem", "get", "manufacturer"))
	s.Model = ExtractValue(RunCommand("wmic", "computersystem", "get", "model"))

	// Gather RAM information
	s.GatherRamInfo()

	// Gather Network Information
	s.GatherNetworkInfo()

	// Get Citrix information
	s.CitrixName, s.CitrixVersion = SearchRegistry(
		"HKLM",
		"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
		"Citrix Workspace",
	)
	
	// Set collection date
	s.CollectionDate = time.Now().Format("2006-01-02 15:04:05")
}

// GatherRamInfo collects RAM details
func (s *SystemInfo) GatherRamInfo() {
	capacityOutput := RunCommand("wmic", "memorychip", "get", "capacity")
	speedOutput := RunCommand("wmic", "memorychip", "get", "speed")
	typeOutput := RunCommand("wmic", "memorychip", "get", "SMBIOSMemoryType")
	slotOutput := RunCommand("wmic", "memorychip", "get", "devicelocator")

	// Process RAM slots
	slotLines := strings.Split(strings.TrimSpace(slotOutput), "\n")
	if len(slotLines) > 1 {
		s.NumRamSlots = fmt.Sprintf("%d", len(slotLines)-1) // Exclude header row
	} else {
		s.NumRamSlots = "Unknown"
	}

	// Process RAM capacities
	totalRamInGB := 0
	var ramCapacities []string
	capacities := strings.Fields(capacityOutput)
	for _, cap := range capacities {
		if cap != "Capacity" { // Ignore header
			capInt, err := strconv.ParseInt(cap, 10, 64)
			if err == nil {
				capGB := int(capInt / (1024 * 1024 * 1024)) // Convert bytes to GB
				totalRamInGB += capGB
				ramCapacities = append(ramCapacities, fmt.Sprintf("%d GB", capGB))
			}
		}
	}
	s.TotalRAM = fmt.Sprintf("%d GB", totalRamInGB)
	s.RamPerSlot = strings.Join(ramCapacities, " | ")

	// Process RAM speed and type
	s.RamSpeed = ExtractValue(speedOutput)

	typeLines := strings.Split(strings.TrimSpace(typeOutput), "\n")
	if len(typeLines) > 1 {
		// Get the first memory type (assuming all are the same)
		memTypeStr := strings.TrimSpace(typeLines[1])
		if ramType, ok := ramTypeMap[memTypeStr]; ok {
			s.RamType = ramType
		} else {
			s.RamType = "Unknown Type: " + memTypeStr
		}
	} else {
		s.RamType = "Unknown"
	}
}

// GatherNetworkInfo collects IP and MAC address details
func (s *SystemInfo) GatherNetworkInfo() {
	ipConfigOutput := RunCommand("ipconfig", "/all")

	// Extract IPv4 address
	ipMatch := regexp.MustCompile(`IPv4 Address[ .]*: (\d+\.\d+\.\d+\.\d+)`).FindStringSubmatch(ipConfigOutput)
	if len(ipMatch) > 1 {
		s.IPAddress = ipMatch[1]
	} else {
		s.IPAddress = "Not found"
	}

	// Extract MAC address
	macMatch := regexp.MustCompile(`Physical Address[ .]*: ([\w-]{17})`).FindStringSubmatch(ipConfigOutput)
	if len(macMatch) > 1 {
		s.MacAddress = macMatch[1]
		
		// Format MAC address as 54E1.AD9D.24CE
		macWithoutSeparators := strings.ReplaceAll(macMatch[1], "-", "")
		if len(macWithoutSeparators) == 12 {
			s.MacAddress = fmt.Sprintf("%s.%s.%s", 
				macWithoutSeparators[0:4], 
				macWithoutSeparators[4:8], 
				macWithoutSeparators[8:12])
		} else {
			s.MacAddress = "Invalid format"
		}
	} else {
		s.MacAddress = "Not found"
		//s.FormattedMac = "Not found"
	}
}

// GetAllInfo prints all system information as a formatted string
func (s *SystemInfo) GetAllInfo() {
	fmt.Printf("Uasername: %s\nHostname: %s\nSerialNumber: %s\nProcessor: %s\nWindowsVersion: %s\nDisplayVersion: %s\nManufacturer: %s\nModel: %s\nTotal RAM: %s\nRAM Slots: %s\nRAM Per Slot: %s\nRAM Speed: %s\nRAM Type: %s\nIP Address: %s\nMAC Address: %s\nCitrix Name: %s\nCitrix Version: %s\nCollection Date: %s\n",
		s.Username, s.Hostname, s.SerialNumber, s.Processor, s.WindowsVersion, s.WindowsDisplayVersion,
		s.Manufacturer, s.Model, s.TotalRAM, s.NumRamSlots, s.RamPerSlot, s.RamSpeed, s.RamType,
		s.IPAddress, s.MacAddress, s.CitrixName, s.CitrixVersion, s.CollectionDate)
}

// Generate a QR code with system information
func (s *SystemInfo) GenerateQRCode() error {
	// Convert SystemInfo to JSON
	jsonData, err := json.Marshal(s)
	if err != nil {
		return fmt.Errorf("failed to convert to JSON: %v", err)
	}
	
	// Generate QR code
	qr, err := qrcode.New(string(jsonData), qrcode.Medium)
	if err != nil {
		return fmt.Errorf("failed to generate QR code: %v", err)
	}
	
	// Print QR code to terminal
	fmt.Println(qr.ToSmallString(false))
	
	// Get temporary directory
	tempDir := os.TempDir()
	
	// Create filename using Hostname_SerialNumber format
	// Clean up the hostname and serial number to avoid invalid filename characters
	cleanHostname := strings.ReplaceAll(s.Hostname, " ", "_")
	cleanSerialNumber := strings.ReplaceAll(s.SerialNumber, " ", "_")
	
	// Replace any other potentially problematic characters
	reg := regexp.MustCompile(`[\\/:*?"<>|]`)
	cleanHostname = reg.ReplaceAllString(cleanHostname, "_")
	cleanSerialNumber = reg.ReplaceAllString(cleanSerialNumber, "_")
	
	filename := fmt.Sprintf("%s_%s.png", cleanHostname, cleanSerialNumber)
	
	// Build the full path
	fullPath := filepath.Join(tempDir, filename)
	
	// Save as PNG file
	err = qr.WriteFile(256, fullPath)
	if err != nil {
		return fmt.Errorf("failed to save QR code as PNG: %v", err)
	}
	
	fmt.Printf("QR code saved as %s\n", fullPath)
	return nil
}




// SaveSystemInfo inserts system information into the SQLite database
func (s *SystemInfo) SaveToDatabase(config Configuration) error {
	// Build database file path from configuration
	dbPath := filepath.Join(config.DBPath, config.DBFilename)
	
	// Connect to SQLite database (or create if not exists)
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return fmt.Errorf("error connecting to database: %v", err)
	}
	defer db.Close()

	// Create table if not exists
	createTableSQL := `CREATE TABLE IF NOT EXISTS system_info (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		Username TEXT,
		Hostname TEXT,
		SerialNumber TEXT UNIQUE,
		Processor TEXT,
		WindowsVersion TEXT,
		WindowsDisplayVersion TEXT,
		Manufacturer TEXT,
		Model TEXT,
		TotalRAM TEXT,
		NumRamSlots TEXT,
		RamPerSlot TEXT,
		RamSpeed TEXT,
		RamType TEXT,
		IPAddress TEXT,
		MacAddress TEXT,
		CitrixName TEXT,
		CitrixVersion TEXT,
		CollectionDate TEXT
	);`

	_, err = db.Exec(createTableSQL)
	if err != nil {
		return fmt.Errorf("error creating table: %v", err)
	}

	// Insert data into the table
	insertSQL := `INSERT INTO system_info 
		(Username, Hostname, SerialNumber, Processor, WindowsVersion, WindowsDisplayVersion, Manufacturer, Model, 
		TotalRAM, NumRamSlots, RamPerSlot, RamSpeed, RamType, IPAddress, MacAddress, CitrixName, CitrixVersion, CollectionDate) 
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(SerialNumber) DO NOTHING;` // Prevent duplicate entries
		

	_, err = db.Exec(insertSQL,
		// Initial values
		s.Username, s.Hostname, s.SerialNumber, s.Processor,
		s.WindowsVersion, s.WindowsDisplayVersion, s.Manufacturer, s.Model,
		s.TotalRAM, s.NumRamSlots, s.RamPerSlot, s.RamSpeed, s.RamType,
		s.IPAddress, s.MacAddress, s.CitrixName,
		s.CitrixVersion, s.CollectionDate,
		
	)

	if err != nil {
		return fmt.Errorf("error inserting/updating data: %v", err)
	}

	fmt.Printf("Data saved to database successfully at %s!\n", dbPath)
	return nil
}

func clearScreen() {
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		cmd = exec.Command("cmd", "/c", "cls") // Windows
	} else {
		cmd = exec.Command("clear") // Linux/macOS
	}
	cmd.Stdout = os.Stdout
	cmd.Run()
}

func rebootSystemx() {
	fmt.Printf("Word Rebooting.................")
}


func rebootSystem() {
	var cmd *exec.Cmd

	if runtime.GOOS == "windows" {
		cmd = exec.Command("shutdown", "/r", "/t", "0") // Windows reboot command
	} else {
		cmd = exec.Command("sudo", "reboot") // Linux/Mac reboot command
	}

	err := cmd.Run()
	if err != nil {
		fmt.Println("Failed to reboot:", err)
	} else {
		fmt.Println("System rebooting...")
	}
}


func main() {
	clearScreen()
	
	// Load configuration from app.config
	config, err := LoadConfig()
	if err != nil {
		fmt.Println(err) // Just print the warning, continue with defaults
	}
	
	fmt.Printf("Using database: %s/%s\n", config.DBPath, config.DBFilename)
	
	// Gather system information
	fmt.Println("Gathering system information...")
	sysInfo := SystemInfo{}
	sysInfo.GatherInfo()
	
	// Convert SystemInfo to JSON and print it to console
	jsonData, err := json.MarshalIndent(sysInfo, "", "  ") // Pretty-print JSON
	if err != nil {
		fmt.Println("Error converting to JSON:", err)
		return
	}
	fmt.Println("Collected System Information:")
	fmt.Println(string(jsonData))
	
	// Generate and display QR code
	fmt.Println("\nGenerating QR code...")
	err = sysInfo.GenerateQRCode()
	if err != nil {
		fmt.Printf("Error generating QR code: %v\n", err)
	}
	
	// Save to database using configuration settings
	fmt.Println("\nSaving information to database...")
	err = sysInfo.SaveToDatabase(config)
	if err != nil {
		fmt.Printf("Error saving to database: %v\n", err)
	}
	
	fmt.Println("\nAll tasks completed!")



	// ========= REBOOT ========================
	reader := bufio.NewReader(os.Stdin)

	for {
		fmt.Print("Press 'y' to reboot, 'n' to exit console : ")
		os.Stdout.Sync() // Force immediate output

		input, _ := reader.ReadString('\n')
		input = strings.TrimSpace(strings.ToLower(input)) // Normalize input

		if input == "y" {
			fmt.Println("Rebooting now...")
			rebootSystem()
			break
		} else if input == "n" {
			fmt.Println("Exit Console")
			break
		} else {
			fmt.Println("Invalid input. Please press 'y' to reboot or 'n' to exit.")
		}
	}




}