package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"regexp"
	"runtime"
	"strconv"
	"strings"
)

type SystemInfo struct {
	Username            string
	Hostname            string
	SerialNumber        string
	Processor           string
	OSVersion           string
	OSDisplayVersion    string
	Manufacturer        string
	Model               string
	TotalRAM            string
	NumRamSlots         string
	RamPerSlot          string
	RamSpeed            string
	RamType             string
	IPAddress           string
	MacAddress          string
	FormattedMac        string
	CitrixInfo          string
}

// RunCommand executes a command and returns the output as a string
func RunCommand(name string, cmdArgs ...string) string {
	cmd := exec.Command(name, cmdArgs...)
	var out bytes.Buffer
	cmd.Stdout = &out
	err := cmd.Run()
	if err != nil {
		fmt.Println("Error executing command:", err)
		return "Unknown"
	}
	return strings.TrimSpace(out.String())
}

// GatherInfo collects system details
func (s *SystemInfo) GatherInfo() {
	// Get logged-in username
	s.Username = os.Getenv("USER")
	if s.Username == "" {
		s.Username = os.Getenv("USERNAME") // For Windows
	}

	// Get hostname
	hostname, err := os.Hostname()
	if err == nil {
		s.Hostname = hostname
	} else {
		s.Hostname = "Unknown"
	}

	// OS-specific information gathering
	switch runtime.GOOS {
	case "windows":
		s.GatherWindowsInfo()
	case "darwin":
		s.GatherMacOSInfo()
	case "linux":
		s.GatherLinuxInfo()
	default:
		fmt.Printf("Unsupported operating system: %s\n", runtime.GOOS)
	}
}

func (s *SystemInfo) GatherWindowsInfo() {
	// Use Windows-specific commands (wmic, reg, etc.)
	s.SerialNumber = extractValue(RunCommand("cmd", "/C", "wmic", "bios", "get", "serialnumber"))
	s.Processor = extractValue(RunCommand("cmd", "/C", "wmic", "cpu", "get", "name"))
	s.OSVersion = extractValue(RunCommand("cmd", "/C", "wmic", "os", "get", "caption"))
	s.Manufacturer = extractValue(RunCommand("cmd", "/C", "wmic", "computersystem", "get", "manufacturer"))
	s.Model = extractValue(RunCommand("cmd", "/C", "wmic", "computersystem", "get", "model"))

	// Get Windows display version
	displayVersionOutput := RunCommand("cmd", "/C", "reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "/v", "DisplayVersion")
	re := regexp.MustCompile(`DisplayVersion\s+REG_SZ\s+(\S+)`)
	matches := re.FindStringSubmatch(displayVersionOutput)
	if len(matches) > 1 {
		s.OSDisplayVersion = matches[1]
	}

	// RAM info
	s.GatherWindowsRAMInfo()

	// Network info
	s.GatherWindowsNetworkInfo()

	// Citrix info
	citrixName, citrixVersion := searchWindowsRegistry(
		"HKLM",
		"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
		"Citrix Workspace",
	)
	if citrixName != "Not found" {
		s.CitrixInfo = fmt.Sprintf("%s - %s", citrixName, citrixVersion)
	} else {
		s.CitrixInfo = "Not installed"
	}
}

func (s *SystemInfo) GatherMacOSInfo() {
	// Use macOS-specific commands
	s.SerialNumber = RunCommand("system_profiler", "SPHardwareDataType")
	if s.SerialNumber != "Unknown" {
		re := regexp.MustCompile(`Serial Number[^:]*:\s*(.+)`)
		matches := re.FindStringSubmatch(s.SerialNumber)
		if len(matches) > 1 {
			s.SerialNumber = matches[1]
		} else {
			s.SerialNumber = "Unknown"
		}
	}

	// Get processor info
	cpuInfo := RunCommand("sysctl", "-n", "machdep.cpu.brand_string")
	if cpuInfo != "Unknown" {
		s.Processor = cpuInfo
	}

	// Get macOS version
	osVersion := RunCommand("sw_vers", "-productVersion")
	if osVersion != "Unknown" {
		s.OSVersion = "macOS " + osVersion
	}
	s.OSDisplayVersion = RunCommand("sw_vers", "-buildVersion")

	// Get model info
	modelInfo := RunCommand("system_profiler", "SPHardwareDataType")
	if modelInfo != "Unknown" {
		re := regexp.MustCompile(`Model Name[^:]*:\s*(.+)`)
		matches := re.FindStringSubmatch(modelInfo)
		if len(matches) > 1 {
			s.Model = matches[1]
		}

		re = regexp.MustCompile(`Model Identifier[^:]*:\s*(.+)`)
		matches = re.FindStringSubmatch(modelInfo)
		if len(matches) > 1 {
			s.Manufacturer = "Apple"
		}
	}

	// RAM info
	memInfo := RunCommand("system_profiler", "SPMemoryDataType")
	if memInfo != "Unknown" {
		// Extract RAM info from system_profiler output
		reSize := regexp.MustCompile(`Size[^:]*:\s*(\d+)\s*GB`)
		reType := regexp.MustCompile(`Type[^:]*:\s*([^\n]+)`)
		reSpeed := regexp.MustCompile(`Speed[^:]*:\s*([^\n]+)`)
		
		sizeMatches := reSize.FindAllStringSubmatch(memInfo, -1)
		s.NumRamSlots = fmt.Sprintf("%d", len(sizeMatches))
		
		var totalRAM int
		var ramSizes []string
		for _, match := range sizeMatches {
			if len(match) > 1 {
				size, err := strconv.Atoi(match[1])
				if err == nil {
					totalRAM += size
					ramSizes = append(ramSizes, fmt.Sprintf("%d GB", size))
				}
			}
		}
		s.TotalRAM = fmt.Sprintf("%d GB", totalRAM)
		s.RamPerSlot = strings.Join(ramSizes, ", ")
		
		typeMatch := reType.FindStringSubmatch(memInfo)
		if len(typeMatch) > 1 {
			s.RamType = typeMatch[1]
		}
		
		speedMatch := reSpeed.FindStringSubmatch(memInfo)
		if len(speedMatch) > 1 {
			s.RamSpeed = speedMatch[1]
		}
	}

	// Network info
	s.GatherMacNetworkInfo()

	// Citrix info
	appList := RunCommand("mdfind", "kMDItemCFBundleIdentifier == 'com.citrix.receiver*'")
	if appList != "Unknown" && appList != "" {
		s.CitrixInfo = "Citrix Workspace installed"
		// Could use mdls to get more detailed version info if needed
	} else {
		s.CitrixInfo = "Not installed"
	}
}

func (s *SystemInfo) GatherLinuxInfo() {
	// Use Linux-specific commands
	
	// Try to get serial number
	s.SerialNumber = RunCommand("sudo", "dmidecode", "-s", "system-serial-number")
	if s.SerialNumber == "Unknown" || strings.Contains(s.SerialNumber, "Permission denied") {
		s.SerialNumber = RunCommand("cat", "/sys/devices/virtual/dmi/id/product_serial")
		if s.SerialNumber == "Unknown" {
			s.SerialNumber = "Unknown (requires root access)"
		}
	}
	
	// Get processor info
	cpuInfo := RunCommand("cat", "/proc/cpuinfo")
	if cpuInfo != "Unknown" {
		re := regexp.MustCompile(`model name\s*:\s*(.+)`)
		matches := re.FindStringSubmatch(cpuInfo)
		if len(matches) > 1 {
			s.Processor = matches[1]
		}
	}
	
	// Get OS version
	osReleaseInfo := RunCommand("cat", "/etc/os-release")
	if osReleaseInfo != "Unknown" {
		reName := regexp.MustCompile(`NAME="([^"]+)"`)
		reVersion := regexp.MustCompile(`VERSION="([^"]+)"`)
		
		nameMatch := reName.FindStringSubmatch(osReleaseInfo)
		versionMatch := reVersion.FindStringSubmatch(osReleaseInfo)
		
		if len(nameMatch) > 1 && len(versionMatch) > 1 {
			s.OSVersion = nameMatch[1] + " " + versionMatch[1]
		} else if len(nameMatch) > 1 {
			s.OSVersion = nameMatch[1]
		}
	}
	
	// Get kernel version as display version
	s.OSDisplayVersion = RunCommand("uname", "-r")
	
	// Get manufacturer and model
	manufacturer := RunCommand("cat", "/sys/devices/virtual/dmi/id/sys_vendor")
	if manufacturer != "Unknown" {
		s.Manufacturer = manufacturer
	}
	
	model := RunCommand("cat", "/sys/devices/virtual/dmi/id/product_name")
	if model != "Unknown" {
		s.Model = model
	}
	
	// Get RAM info
	memInfo := RunCommand("cat", "/proc/meminfo")
	if memInfo != "Unknown" {
		re := regexp.MustCompile(`MemTotal:\s+(\d+)\s+kB`)
		matches := re.FindStringSubmatch(memInfo)
		if len(matches) > 1 {
			memKB, err := strconv.ParseInt(matches[1], 10, 64)
			if err == nil {
				memGB := memKB / (1024 * 1024)
				if memGB < 1 {
					s.TotalRAM = fmt.Sprintf("%d MB", memKB/1024)
				} else {
					s.TotalRAM = fmt.Sprintf("%d GB", memGB)
				}
			}
		}
	}
	
	// Try to get detailed RAM info using lshw
	ramInfo := RunCommand("sudo", "lshw", "-class", "memory")
	if ramInfo == "Unknown" || strings.Contains(ramInfo, "Permission denied") {
		s.NumRamSlots = "Unknown (requires root access)"
		s.RamPerSlot = "Unknown (requires root access)"
		s.RamSpeed = "Unknown (requires root access)"
		s.RamType = "Unknown (requires root access)"
	} else {
		// Process lshw output to extract RAM details
		// This would require more complex parsing of the lshw output
		s.NumRamSlots = "See detailed output"
		s.RamPerSlot = "See detailed output"
		s.RamSpeed = "See detailed output"
		s.RamType = "See detailed output"
	}
	
	// Network info
	s.GatherLinuxNetworkInfo()
	
	// Check for Citrix
	citrixCheck := RunCommand("which", "wfica")
	if citrixCheck != "Unknown" && !strings.Contains(citrixCheck, "no wfica") {
		s.CitrixInfo = "Citrix Workspace installed"
	} else {
		// Alternative check
		dpkgCheck := RunCommand("dpkg", "-l", "icaclient")
		if dpkgCheck != "Unknown" && !strings.Contains(dpkgCheck, "no packages found") {
			s.CitrixInfo = "Citrix Workspace installed"
		} else {
			s.CitrixInfo = "Not installed"
		}
	}
}

func (s *SystemInfo) GatherWindowsRAMInfo() {
	capacityOutput := RunCommand("cmd", "/C", "wmic", "memorychip", "get", "capacity")
	speedOutput := RunCommand("cmd", "/C", "wmic", "memorychip", "get", "speed")
	typeOutput := RunCommand("cmd", "/C", "wmic", "memorychip", "get", "SMBIOSMemoryType")
	slotOutput := RunCommand("cmd", "/C", "wmic", "memorychip", "get", "devicelocator")

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
	s.RamPerSlot = strings.Join(ramCapacities, ", ")

	// Process RAM speed
	s.RamSpeed = extractValue(speedOutput)

	// RAM type mapping
	ramTypeMap := map[string]string{
		"20": "DDR",
		"21": "DDR2",
		"24": "DDR3",
		"26": "DDR4",
		"29": "DDR5",
	}

	// Process RAM type
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

func (s *SystemInfo) GatherWindowsNetworkInfo() {
	ipConfigOutput := RunCommand("cmd", "/C", "ipconfig", "/all")

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
		s.FormattedMac = strings.ReplaceAll(macMatch[1], "-", ":")
	} else {
		s.MacAddress = "Not found"
		s.FormattedMac = "Not found"
	}
}

func (s *SystemInfo) GatherMacNetworkInfo() {
	// Get IP address
	ipOutput := RunCommand("ifconfig", "en0")
	if ipOutput == "Unknown" {
		// Try alternative interface
		ipOutput = RunCommand("ifconfig", "en1")
	}
	
	if ipOutput != "Unknown" {
		ipMatch := regexp.MustCompile(`inet\s+(\d+\.\d+\.\d+\.\d+)`).FindStringSubmatch(ipOutput)
		if len(ipMatch) > 1 {
			s.IPAddress = ipMatch[1]
		} else {
			s.IPAddress = "Not found"
		}
		
		// Extract MAC address
		macMatch := regexp.MustCompile(`ether\s+([0-9a-f:]{17})`).FindStringSubmatch(ipOutput)
		if len(macMatch) > 1 {
			s.MacAddress = macMatch[1]
			s.FormattedMac = macMatch[1] // Already formatted
		} else {
			s.MacAddress = "Not found"
			s.FormattedMac = "Not found"
		}
	} else {
		s.IPAddress = "Not found"
		s.MacAddress = "Not found"
		s.FormattedMac = "Not found"
	}
}

func (s *SystemInfo) GatherLinuxNetworkInfo() {
	// Get IP address using ip command
	ipOutput := RunCommand("ip", "addr", "show")
	if ipOutput != "Unknown" {
		ipMatch := regexp.MustCompile(`inet\s+(\d+\.\d+\.\d+\.\d+)`).FindStringSubmatch(ipOutput)
		if len(ipMatch) > 1 {
			s.IPAddress = ipMatch[1]
		} else {
			s.IPAddress = "Not found"
		}
		
		// Extract MAC address
		macMatch := regexp.MustCompile(`link/ether\s+([0-9a-f:]{17})`).FindStringSubmatch(ipOutput)
		if len(macMatch) > 1 {
			s.MacAddress = macMatch[1]
			s.FormattedMac = macMatch[1] // Already formatted
		} else {
			s.MacAddress = "Not found"
			s.FormattedMac = "Not found"
		}
	} else {
		// Fallback to ifconfig
		ifconfigOutput := RunCommand("ifconfig")
		if ifconfigOutput != "Unknown" {
			ipMatch := regexp.MustCompile(`inet\s+(\d+\.\d+\.\d+\.\d+)`).FindStringSubmatch(ifconfigOutput)
			if len(ipMatch) > 1 {
				s.IPAddress = ipMatch[1]
			} else {
				s.IPAddress = "Not found"
			}
			
			// Extract MAC address
			macMatch := regexp.MustCompile(`ether\s+([0-9a-f:]{17})`).FindStringSubmatch(ifconfigOutput)
			if len(macMatch) > 1 {
				s.MacAddress = macMatch[1]
				s.FormattedMac = macMatch[1] // Already formatted
			} else {
				s.MacAddress = "Not found"
				s.FormattedMac = "Not found"
			}
		} else {
			s.IPAddress = "Not found (requires ip or ifconfig)"
			s.MacAddress = "Not found (requires ip or ifconfig)"
			s.FormattedMac = "Not found (requires ip or ifconfig)"
		}
	}
}

// Helper functions
func extractValue(output string) string {
	lines := strings.Split(output, "\n")
	if len(lines) > 1 {
		return strings.TrimSpace(lines[1])
	}
	return "Unknown"
}

func searchWindowsRegistry(hive, path, searchPattern string) (string, string) {
	output := RunCommand("cmd", "/C", "reg", "query", fmt.Sprintf("%s\\%s", hive, path), "/s")
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

// GetSystemInfo prints all system information as a formatted string
func (s *SystemInfo) GetSystemInfo() {
	fmt.Printf("System Information Summary\n")
	fmt.Printf("=========================\n")
	fmt.Printf("Username: %s\n", s.Username)
	fmt.Printf("Hostname: %s\n", s.Hostname)
	fmt.Printf("Operating System: %s\n", s.OSVersion)
	fmt.Printf("OS Build/Version: %s\n", s.OSDisplayVersion)
	fmt.Printf("\nHardware Details\n")
	fmt.Printf("=========================\n")
	fmt.Printf("Manufacturer: %s\n", s.Manufacturer)
	fmt.Printf("Model: %s\n", s.Model)
	fmt.Printf("Serial Number: %s\n", s.SerialNumber)
	fmt.Printf("Processor: %s\n", s.Processor)
	fmt.Printf("\nMemory Details\n")
	fmt.Printf("=========================\n")
	fmt.Printf("Total RAM: %s\n", s.TotalRAM)
	fmt.Printf("RAM Slots: %s\n", s.NumRamSlots)
	fmt.Printf("RAM Per Slot: %s\n", s.RamPerSlot)
	fmt.Printf("RAM Speed: %s\n", s.RamSpeed)
	fmt.Printf("RAM Type: %s\n", s.RamType)
	fmt.Printf("\nNetwork Details\n")
	fmt.Printf("=========================\n")
	fmt.Printf("IP Address: %s\n", s.IPAddress)
	fmt.Printf("MAC Address: %s\n", s.MacAddress)
	fmt.Printf("Formatted MAC: %s\n", s.FormattedMac)
	fmt.Printf("\nSoftware Details\n")
	fmt.Printf("=========================\n")
	fmt.Printf("Citrix Info: %s\n", s.CitrixInfo)
}

func main() {
	fmt.Printf("System Information Tool\n")
	fmt.Printf("OS: %s\n\n", runtime.GOOS)
	
	sysInfo := SystemInfo{}
	sysInfo.GatherInfo()
	sysInfo.GetSystemInfo()
}