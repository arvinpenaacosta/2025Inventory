
const runCommand = async (cmd: string[]) => {
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
  };






const getSystemInfo = async () => {
  // Get basic system information
  const cpuname = await runCommand(["wmic", "computersystem", "get", "name"]);
  const hostname = cpuname?.split("\n")[1]?.trim()

  const serialNumber = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  const serNum = serialNumber?.split("\n")[1]?.trim();

  //
  const processor = await runCommand(["wmic", "cpu", "get", "name"]);
  const pcPro = processor?.split("\n")[1]?.trim();
  //
  const windowsVersion = await runCommand(["wmic", "os", "get", "caption"]);
  const winVerXX = windowsVersion?.split("\n")[1]?.trim();
  
  //
  const windispLayversion = await runCommand([
    "reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
    "/v", "DisplayVersion"
  ]);
  // Extract Display Version
  const windispLayversionMatch = windispLayversion?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);
  const win2xHx = windispLayversionMatch ? windispLayversionMatch[1] : "Unknown";

  // Get PC brand (manufacturer)
  const manufacturer = await runCommand(["wmic", "computersystem", "get", "manufacturer"]);
  const pcMfr = manufacturer?.split("\n")[1]?.trim();

  //
  const model = await runCommand(["wmic", "computersystem", "get", "model"]);
  const pcmodel = model?.split("\n")[1]?.trim();

  // Get RAM details
  const capacityOutput = await runCommand(["wmic", "memorychip", "get", "capacity"]);
  const speedOutput = await runCommand(["wmic", "memorychip", "get", "speed"]);
  const typeOutput = await runCommand(["wmic", "memorychip", "get", "SMBIOSMemoryType"]);
  const slotOutput = await runCommand(["wmic", "memorychip", "get", "devicelocator"]);

  // Get network information for IP and MAC address
  const ipConfigOutput = await runCommand(["ipconfig", "/all"]);
  
  //
  const ipAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?IPv4 Address[ .]*: (\d+\.\d+\.\d+\.\d+)/s);
  const IPAddress = ipAddressMatch ? ipAddressMatch[1] : "Not found"

  //
  const macAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?Physical.*?([\w-]{17})/s);
  const MACAddress =  macAddressMatch ? macAddressMatch[1] : "Not found"
  const formattedMac = MACAddress.replace(/-/g, "").match(/.{1,4}/g).join(".");

  // RAM Type Mapping
  const ramTypeMap: { [key: string]: string } = {
    "20": "DDR",
    "21": "DDR2",
    "24": "DDR3",
    "26": "DDR4",
    "29": "DDR5",
  };

  // Count RAM slots
  const slotLines = typeof slotOutput === "string"
    ? slotOutput.split("\n").map(line => line.trim()).filter(line => line.length > 0)
    : [];
  
  const numRamSlots = slotLines.length > 1 ? slotLines.length - 1 : "Unknown"; // Exclude header row



  // Process RAM capacities
  let totalRamInGB = 0;
  let ramCapacities: string[] = [];
  if (capacityOutput) {
    const capacities = capacityOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    capacities.forEach(capacity => {
      const capacityGB = parseInt(capacity) / (1024 ** 3); // Convert bytes to GB
      totalRamInGB += capacityGB;
      ramCapacities.push(`${capacityGB} GB`);
    });
  }

  const allRAM = totalRamInGB.toFixed(2);
  const ramEachSlot = ramCapacities.length > 0 ? ramCapacities.join(", ") : "Unknown";

  // Process RAM speed
  const ramSpeed = speedOutput?.split("\n")[1]?.trim() || "Unknown";

  // Process RAM type
  let ramType = "Unknown";
  if (typeOutput) {
    const typeLines = typeOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    ramType = typeLines.length > 0 ? (ramTypeMap[typeLines[0]] || "Unknown") : "Unknown";
  }



  // Function to search the registry for software
  async function searchRegistryWithGUID(hive: string, path: string, searchPattern: string) {
    const outputString = await runCommand(["reg", "query", `${hive}\\${path}`, "/s"]);
    if (outputString === null) {
      return { displayName: "Not found", displayVersion: "Not found" };
    }

    const lines = outputString.split("\n");
    let displayName = '';
    let displayVersion = '';

    const searchPatternLower = searchPattern.toLowerCase();
    for (const line of lines) {
      if (line.toLowerCase().includes("displayname") && line.toLowerCase().includes(searchPatternLower)) {
        displayName = line.trim().split('REG_SZ')[1]?.trim();
      }
      if (line.toLowerCase().includes("displayversion") && displayName !== '') {
        displayVersion = line.trim().split('REG_SZ')[1]?.trim();
      }
      if (displayName && displayVersion) {
        return { displayName, displayVersion };
      }
    }

    return { displayName: "Not found", displayVersion: "Not found" };
  }

  // Example usage: search for software "Citrix Workspace"
  const hive = "HKLM";
  const path = "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall";
  const searchPattern = "Citrix Workspace";
  const citrixData = await searchRegistryWithGUID(hive, path, searchPattern);




  // Output all system info
  console.log("🔹 PC Information:");
  console.log("Hostname:", hostname );
  console.log("Serial Number:", serNum );
  console.log("Processor:", pcPro );
  console.log("Windows Version:", winVerXX);
  console.log("xWindows Display Version:", win2xHx);
  console.log("Manufacturer:", pcMfr);
  console.log("Model:", pcmodel);

  console.log("\n🔹 RAM Information:");
  console.log("Total RAM Capacity:", allRAM, "GB");
  console.log("Number of RAM Slots:", numRamSlots);
  console.log("RAM Installed per Slot:", ramEachSlot);
  console.log("RAM Speed:", ramSpeed);
  console.log("RAM Type:", ramType);

  console.log("\n🔹 Network Information:");
  console.log("IP Address:", IPAddress);
  console.log("MAC Address:", formattedMac);

  console.log("\n🔹 Citrix Information:");
  console.log("Citrix Name:", citrixData.displayName);
  console.log("Citrix Version:", citrixData.displayVersion);

};

// Run the script
await getSystemInfo();