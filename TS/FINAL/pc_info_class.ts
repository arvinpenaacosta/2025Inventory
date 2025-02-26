/**
 * SystemInfo class for gathering Windows system information
 * Can be imported and used in other scripts
 */
export class SystemInfo {
  // Basic system info properties
  private username: string = "Unknown";
  private hostname: string = "Unknown";
  private serialNumber: string = "Unknown";
  private processor: string = "Unknown";
  private windowsVersion: string = "Unknown";
  private windowsDisplayVersion: string = "Unknown";
  private manufacturer: string = "Unknown";
  private model: string = "Unknown";

  // RAM info properties
  private totalRam: string = "Unknown";
  private numRamSlots: string | number = "Unknown";
  private ramPerSlot: string = "Unknown";
  private ramSpeed: string = "Unknown";
  private ramType: string = "Unknown";

  // Network info properties
  private ipAddress: string = "Unknown";
  private macAddress: string = "Unknown";
  private formattedMac: string = "Unknown";

  // Software info properties
  private citrixName: string = "Not found";
  private citrixVersion: string = "Not found";

  // RAM type mapping
  private ramTypeMap: { [key: string]: string } = {
    "20": "DDR",
    "21": "DDR2",
    "24": "DDR3",
    "26": "DDR4",
    "29": "DDR5",
  };

  /**
   * Constructor initializes with default values
   * Call gatherInfo() to populate with actual system data
   */
  constructor() {}

  /**
   * Executes a Windows command and returns the output as a string
   * @param cmd Array of command arguments
   * @returns Trimmed stdout output or null if there's an error
   */
  private async runCommand(cmd: string[]): Promise<string | null> {
    try {
      const process = new Deno.Command("cmd", {
        args: ["/c", ...cmd],
        stdout: "piped",
        stderr: "piped",
      }).spawn();

      const { stdout, stderr } = await process.output();

      if (stderr.length > 0) {
        console.error(new TextDecoder().decode(stderr));
        return null;
      }
      return new TextDecoder().decode(stdout).trim();
    } catch (error) {
      console.error("Command execution error:", error);
      return null;
    }
  }

  /**
   * Extracts the value from command output (skipping the header line)
   * @param output Command output string
   * @returns Trimmed value or "Unknown" if not found
   */
  private extractValue(output: string | null): string {
    if (!output) return "Unknown";
    const lines = output.split("\n").map(line => line.trim()).filter(line => line.length > 0);
    return lines.length > 1 ? lines[1] : "Unknown";
  }

  /**
   * Searches the Windows registry for software information
   * @param hive Registry hive (e.g., "HKLM")
   * @param path Registry path
   * @param searchPattern Software name to search for
   * @returns Object containing displayName and displayVersion
   */
  private async searchRegistry(
    hive: string, 
    path: string, 
    searchPattern: string
  ): Promise<{ displayName: string; displayVersion: string }> {
    const outputString = await this.runCommand(["reg", "query", `${hive}\\${path}`, "/s"]);
    if (outputString === null) {
      return { displayName: "Not found", displayVersion: "Not found" };
    }

    const lines = outputString.split("\n");
    let displayName = '';
    let displayVersion = '';

    const searchPatternLower = searchPattern.toLowerCase();
    for (const line of lines) {
      if (line.toLowerCase().includes("displayname") && line.toLowerCase().includes(searchPatternLower)) {
        displayName = line.trim().split('REG_SZ')[1]?.trim() || '';
      }
      if (line.toLowerCase().includes("displayversion") && displayName !== '') {
        displayVersion = line.trim().split('REG_SZ')[1]?.trim() || '';
      }
      if (displayName && displayVersion) {
        return { displayName, displayVersion };
      }
    }

    return { displayName: "Not found", displayVersion: "Not found" };
  }

  /**
   * Gathers all system information and populates class properties
   * @returns Promise that resolves when all information is gathered
   */
  public async gatherInfo(): Promise<void> {
    // Get Username Logged-In
    this.username = Deno.env.get("USERNAME") || Deno.env.get("USER");

    // Get basic system information
    const hostnameOutput = await this.runCommand(["wmic", "computersystem", "get", "name"]);
    this.hostname = this.extractValue(hostnameOutput);

    const serialNumberOutput = await this.runCommand(["wmic", "bios", "get", "serialnumber"]);
    this.serialNumber = this.extractValue(serialNumberOutput);

    const processorOutput = await this.runCommand(["wmic", "cpu", "get", "name"]);
    this.processor = this.extractValue(processorOutput);

    const windowsVersionOutput = await this.runCommand(["wmic", "os", "get", "caption"]);
    this.windowsVersion = this.extractValue(windowsVersionOutput);
    
    const displayVersionOutput = await this.runCommand([
      "reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
      "/v", "DisplayVersion"
    ]);
    const displayVersionMatch = displayVersionOutput?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);
    this.windowsDisplayVersion = displayVersionMatch ? displayVersionMatch[1] : "Unknown";

    const manufacturerOutput = await this.runCommand(["wmic", "computersystem", "get", "manufacturer"]);
    this.manufacturer = this.extractValue(manufacturerOutput);

    const modelOutput = await this.runCommand(["wmic", "computersystem", "get", "model"]);
    this.model = this.extractValue(modelOutput);

    // Get RAM details
    await this.gatherRamInfo();

    // Get network information
    await this.gatherNetworkInfo();

    // Get Citrix information
    const citrixData = await this.searchRegistry(
      "HKLM",
      "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
      "Citrix Workspace"
    );
    
    this.citrixName = citrixData.displayName;
    this.citrixVersion = citrixData.displayVersion;
  }

  /**
   * Gathers RAM-specific information
   */
  private async gatherRamInfo(): Promise<void> {
    const capacityOutput = await this.runCommand(["wmic", "memorychip", "get", "capacity"]);
    const speedOutput = await this.runCommand(["wmic", "memorychip", "get", "speed"]);
    const typeOutput = await this.runCommand(["wmic", "memorychip", "get", "SMBIOSMemoryType"]);
    const slotOutput = await this.runCommand(["wmic", "memorychip", "get", "devicelocator"]);

    // Process RAM slots
    const slotLines = slotOutput ? 
      slotOutput.split("\n").map(line => line.trim()).filter(line => line.length > 0) : 
      [];
    
    this.numRamSlots = slotLines.length > 1 ? slotLines.length - 1 : "Unknown"; // Exclude header row

    // Process RAM capacities
    let totalRamInGB = 0;
    const ramCapacities: string[] = [];
    if (capacityOutput) {
      const capacities = capacityOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
      capacities.forEach(capacity => {
        const capacityGB = parseInt(capacity) / (1024 ** 3); // Convert bytes to GB
        totalRamInGB += capacityGB;
        ramCapacities.push(`${capacityGB.toFixed(2)} GB`);
      });
    }

    this.totalRam = totalRamInGB.toFixed(2);
    this.ramPerSlot = ramCapacities.length > 0 ? ramCapacities.join(", ") : "Unknown";

    // Process RAM speed and type
    this.ramSpeed = speedOutput?.split("\n")[1]?.trim() || "Unknown";

    if (typeOutput) {
      const typeLines = typeOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
      this.ramType = typeLines.length > 0 ? (this.ramTypeMap[typeLines[0]] || "Unknown") : "Unknown";
    }
  }

  /**
   * Gathers network-specific information
   */
  private async gatherNetworkInfo(): Promise<void> {
    const ipConfigOutput = await this.runCommand(["ipconfig", "/all"]);
    
    const ipAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?IPv4 Address[ .]*: (\d+\.\d+\.\d+\.\d+)/s);
    this.ipAddress = ipAddressMatch ? ipAddressMatch[1] : "Not found";

    const macAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?Physical.*?([\w-]{17})/s);
    this.macAddress = macAddressMatch ? macAddressMatch[1] : "Not found";
    
    this.formattedMac = this.macAddress !== "Not found" ? 
      this.macAddress.replace(/-/g, "").match(/.{1,4}/g)?.join(".") || "Not found" : 
      "Not found";
  }

  /**
   * Gets all system information as an object
   * @returns Object containing all system information
   */
  public getAllInfo(): SystemInfoData {
    return {
      system: {
        username: this.username,
        hostname: this.hostname,
        serialNumber: this.serialNumber,
        processor: this.processor,
        windowsVersion: this.windowsVersion,
        windowsDisplayVersion: this.windowsDisplayVersion,
        manufacturer: this.manufacturer,
        model: this.model
      },
      ram: {
        totalCapacity: this.totalRam,
        numSlots: this.numRamSlots,
        perSlot: this.ramPerSlot,
        speed: this.ramSpeed,
        type: this.ramType
      },
      network: {
        ipAddress: this.ipAddress,
        macAddress: this.macAddress,
        formattedMac: this.formattedMac
      },
      software: {
        citrixName: this.citrixName,
        citrixVersion: this.citrixVersion
      }
    };
  }

  /**
   * Prints all system information to the console
   */
  public printAllInfo(): void {
    console.log("🔹 PC Information:");
    console.log("Username:", this.username);
    console.log("Hostname:", this.hostname);
    console.log("Serial Number:", this.serialNumber);
    console.log("Processor:", this.processor);
    console.log("Windows Version:", this.windowsVersion);
    console.log("Windows Display Version:", this.windowsDisplayVersion);
    console.log("Manufacturer:", this.manufacturer);
    console.log("Model:", this.model);

    console.log("\n🔹 RAM Information:");
    console.log("Total RAM Capacity:", this.totalRam, "GB");
    console.log("Number of RAM Slots:", this.numRamSlots);
    console.log("RAM Installed per Slot:", this.ramPerSlot);
    console.log("RAM Speed:", this.ramSpeed, "MHz");
    console.log("RAM Type:", this.ramType);

    console.log("\n🔹 Network Information:");
    console.log("IP Address:", this.ipAddress);
    console.log("MAC Address:", this.formattedMac);

    console.log("\n🔹 Citrix Information:");
    console.log("Citrix Name:", this.citrixName);
    console.log("Citrix Version:", this.citrixVersion);
  }

  /**
   * Searches for specific software in the registry
   * @param softwareName Name of the software to search for
   * @returns Promise resolving to object with display name and version
   */
  public async getSoftwareInfo(softwareName: string): Promise<{ displayName: string; displayVersion: string }> {
    return this.searchRegistry(
      "HKLM",
      "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
      softwareName
    );
  }
}

/**
 * Interface defining the structure of system information data
 */
export interface SystemInfoData {
  system: {
    username: string;
    hostname: string;
    serialNumber: string;
    processor: string;
    windowsVersion: string;
    windowsDisplayVersion: string;
    manufacturer: string;
    model: string;
  };
  ram: {
    totalCapacity: string;
    numSlots: string | number;
    perSlot: string;
    speed: string;
    type: string;
  };
  network: {
    ipAddress: string;
    macAddress: string;
    formattedMac: string;
  };
  software: {
    citrixName: string;
    citrixVersion: string;
  };
}

// Example usage (uncomment to run directly)
/*
const main = async () => {
  const sysInfo = new SystemInfo();
  await sysInfo.gatherInfo();
  sysInfo.printAllInfo();
  
  // Or get the data as an object
  const infoData = sysInfo.getAllInfo();
  console.log(JSON.stringify(infoData, null, 2));
  
  // Search for specific software
  const adobeInfo = await sysInfo.getSoftwareInfo("Adobe");
  console.log("Adobe Software:", adobeInfo);
};

await main();
*/
