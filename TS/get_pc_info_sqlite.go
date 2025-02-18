package main

import (
	"database/sql"
	"fmt"
	"log"
	"os/exec"
	"regexp"
	"time"

	_ "github.com/mattn/go-sqlite3"
)

// Struct to hold system info
type SystemInfo struct {
	SerialNumber   string
	Processor      string
	WindowsVersion string
	DisplayVersion string
	Manufacturer   string
	Model          string
	TotalRAM       string
	RAMSlots       string
	RAMPerSlot     string
	RAMSpeed       string
	RAMType        string
	IPAddress      string
	MACAddress     string
	Timestamp      string
}

// Function to run commands in the system (e.g., to get system info)
func runCommand(cmd []string) (string, error) {
	output, err := exec.Command(cmd[0], cmd[1:]...).CombinedOutput()
	return string(output), err
}

// Function to format the timestamp as YYYY-MM-DD HH:MM:SS
func formatTimestamp() string {
	return time.Now().Format("2006-01-02 15:04:05")
}

// Function to retrieve system information
func getSystemInfo() (*SystemInfo, error) {
	var systemInfo SystemInfo
	var err error

	serialNumber, err := runCommand([]string{"wmic", "bios", "get", "serialnumber"})
	if err != nil {
		return nil, err
	}
	systemInfo.SerialNumber = serialNumber

	processor, err := runCommand([]string{"wmic", "cpu", "get", "name"})
	if err != nil {
		return nil, err
	}
	systemInfo.Processor = processor

	windowsVersion, err := runCommand([]string{"wmic", "os", "get", "caption"})
	if err != nil {
		return nil, err
	}
	systemInfo.WindowsVersion = windowsVersion

	displayVersion, err := runCommand([]string{
		"reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "/v", "DisplayVersion"})
	if err != nil {
		return nil, err
	}
	r, _ := regexp.Compile(`DisplayVersion\s+REG_SZ\s+(\S+)`)
	match := r.FindStringSubmatch(displayVersion)
	if len(match) > 1 {
		systemInfo.DisplayVersion = match[1]
	}

	manufacturer, err := runCommand([]string{"wmic", "computersystem", "get", "manufacturer"})
	if err != nil {
		return nil, err
	}
	systemInfo.Manufacturer = manufacturer

	model, err := runCommand([]string{"wmic", "computersystem", "get", "model"})
	if err != nil {
		return nil, err
	}
	systemInfo.Model = model

	totalRAM, err := runCommand([]string{"wmic", "memorychip", "get", "capacity"})
	if err != nil {
		return nil, err
	}
	systemInfo.TotalRAM = totalRAM

	ramSpeed, err := runCommand([]string{"wmic", "memorychip", "get", "speed"})
	if err != nil {
		return nil, err
	}
	systemInfo.RAMSpeed = ramSpeed

	ramType, err := runCommand([]string{"wmic", "memorychip", "get", "SMBIOSMemoryType"})
	if err != nil {
		return nil, err
	}
	systemInfo.RAMType = ramType

	slotOutput, err := runCommand([]string{"wmic", "memorychip", "get", "devicelocator"})
	if err != nil {
		return nil, err
	}
	systemInfo.RAMSlots = slotOutput

	ipConfigOutput, err := runCommand([]string{"ipconfig", "/all"})
	if err != nil {
		return nil, err
	}

	// Extract IP and MAC address using regex
	rIP := regexp.MustCompile(`Ethernet adapter.*?IPv4 Address[ .]*: (\d+\.\d+\.\d+\.\d+)`)
	rMAC := regexp.MustCompile(`Ethernet adapter.*?Physical.*?([\w-]{17})`)
	ipMatch := rIP.FindStringSubmatch(ipConfigOutput)
	macMatch := rMAC.FindStringSubmatch(ipConfigOutput)

	if len(ipMatch) > 1 {
		systemInfo.IPAddress = ipMatch[1]
	}
	if len(macMatch) > 1 {
		systemInfo.MACAddress = macMatch[1]
	}

	systemInfo.Timestamp = formatTimestamp()

	return &systemInfo, nil
}

// Function to save system info to the SQLite database
func saveToSQLite(systemInfo *SystemInfo, db *sql.DB) error {
	query := `INSERT INTO pc_info_inv (
		serial_number, processor, windows_version, display_version, 
		manufacturer, model, total_ram, ram_slots, ram_per_slot, 
		ram_speed, ram_type, ip_address, mac_address, timestamp
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`

	_, err := db.Exec(query, systemInfo.SerialNumber, systemInfo.Processor, systemInfo.WindowsVersion,
		systemInfo.DisplayVersion, systemInfo.Manufacturer, systemInfo.Model, systemInfo.TotalRAM,
		systemInfo.RAMSlots, systemInfo.RAMPerSlot, systemInfo.RAMSpeed, systemInfo.RAMType,
		systemInfo.IPAddress, systemInfo.MACAddress, systemInfo.Timestamp)
	if err != nil {
		return err
	}
	fmt.Println("✅ Data saved to SQLite")
	return nil
}

func main() {
	// Open the SQLite database (it will create the file if it doesn't exist)
	db, err := sql.Open("sqlite3", "./pc_info.db")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Create table if it doesn't exist
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS pc_info_inv (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			serial_number TEXT,
			processor TEXT,
			windows_version TEXT,
			display_version TEXT,
			manufacturer TEXT,
			model TEXT,
			total_ram TEXT,
			ram_slots TEXT,
			ram_per_slot TEXT,
			ram_speed TEXT,
			ram_type TEXT,
			ip_address TEXT,
			mac_address TEXT,
			timestamp TEXT
		)
	`)
	if err != nil {
		log.Fatal(err)
	}

	// Get system information
	systemInfo, err := getSystemInfo()
	if err != nil {
		log.Fatal(err)
	}

	// Save the system info to SQLite
	err = saveToSQLite(systemInfo, db)
	if err != nil {
		log.Fatal(err)
	}
}
