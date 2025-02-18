const runCommand = async (cmd: string[]) => {
  const process = Deno.run({
    cmd: ["cmd", "/c", ...cmd],
    stdout: "piped",
    stderr: "piped",
  });

  const output = await process.output();
  const error = await process.stderrOutput();
  process.close();

  if (error.length > 0) {
    console.error(new TextDecoder().decode(error));
    return null;
  }
  return new TextDecoder().decode(output).trim();
};

const getSystemInfo = async () => {
  // Get basic system information
  const serialNumber = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  const processor = await runCommand(["wmic", "cpu", "get", "name"]);
  const windowsVersion = await runCommand(["wmic", "os", "get", "caption"]);
  const displayVersion = await runCommand([
    "reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
    "/v", "DisplayVersion"
  ]);

  // Get PC brand (manufacturer)
  const manufacturer = await runCommand(["wmic", "computersystem", "get", "manufacturer"]);
  const model = await runCommand(["wmic", "computersystem", "get", "model"]);

  // Get RAM details
  const capacityOutput = await runCommand(["wmic", "memorychip", "get", "capacity"]);
  const speedOutput = await runCommand(["wmic", "memorychip", "get", "speed"]);
  const typeOutput = await runCommand(["wmic", "memorychip", "get", "SMBIOSMemoryType"]);
  const slotOutput = await runCommand(["wmic", "memorychip", "get", "devicelocator"]);

  // Get network information for IP and MAC address
  const ipConfigOutput = await runCommand(["ipconfig", "/all"]);
  
  const ipAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?IPv4 Address[ .]*: (\d+\.\d+\.\d+\.\d+)/s);
  const macAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?Physical.*?([\w-]{17})/s);

  // RAM Type Mapping
  const ramTypeMap: { [key: string]: string } = {
    "20": "DDR",
    "21": "DDR2",
    "24": "DDR3",
    "26": "DDR4",
    "29": "DDR5",
  };

  // Count RAM slots
  const slotLines = slotOutput?.split("\n").map(line => line.trim()).filter(line => line.length > 0);
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

  // Process RAM speed
  const ramSpeed = speedOutput?.split("\n")[1]?.trim() || "Unknown";

  // Process RAM type
  let ramType = "Unknown";
  if (typeOutput) {
    const typeLines = typeOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    ramType = typeLines.length > 0 ? (ramTypeMap[typeLines[0]] || "Unknown") : "Unknown";
  }

  // Extract Display Version
  const displayVersionMatch = displayVersion?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);

  // Output all system info
  console.log("🔹 PC Information:");
  console.log("Serial Number:", serialNumber?.split("\n")[1]?.trim());
  console.log("Processor:", processor?.split("\n")[1]?.trim());
  console.log("Windows Version:", windowsVersion?.split("\n")[1]?.trim());
  console.log("Windows Display Version:", displayVersionMatch ? displayVersionMatch[1] : "Unknown");
  console.log("Manufacturer:", manufacturer?.split("\n")[1]?.trim());
  console.log("Model:", model?.split("\n")[1]?.trim());

  console.log("\n🔹 RAM Information:");
  console.log("Total RAM Capacity:", totalRamInGB.toFixed(2), "GB");
  console.log("Number of RAM Slots:", numRamSlots);
  console.log("RAM Installed per Slot:", ramCapacities.length > 0 ? ramCapacities.join(", ") : "Unknown");
  console.log("RAM Speed:", ramSpeed);
  console.log("RAM Type:", ramType);

  console.log("\n🔹 Network Information:");
  console.log("IP Address:", ipAddressMatch ? ipAddressMatch[1] : "Not found");
  console.log("MAC Address:", macAddressMatch ? macAddressMatch[1] : "Not found");
};

// Run the script
await getSystemInfo();
