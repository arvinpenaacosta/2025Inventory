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

const getRamInfo = async () => {
  // Get RAM details
  const capacityOutput = await runCommand(["wmic", "memorychip", "get", "capacity"]);
  const typeOutput = await runCommand(["wmic", "memorychip", "get", "SMBIOSMemoryType"]);
  const slotOutput = await runCommand(["wmic", "memorychip", "get", "devicelocator"]); // Alternative way to count slots

  // RAM Type Mapping
  const ramTypeMap: { [key: string]: string } = {
    "20": "DDR",
    "21": "DDR2",
    "24": "DDR3",
    "26": "DDR4",
    "29": "DDR5",
  };

  // Count RAM slots using `DeviceLocator`
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

  // Process RAM type
  let ramType = "Unknown";
  if (typeOutput) {
    const typeLines = typeOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    ramType = typeLines.length > 0 ? (ramTypeMap[typeLines[0]] || "Unknown") : "Unknown";
  }

  // Print results
  console.log("🔹 RAM Information:");
  console.log("Total RAM Capacity:", totalRamInGB.toFixed(2), "GB");
  console.log("Number of RAM Slots:", numRamSlots);
  console.log("RAM Installed per Slot:", ramCapacities.length > 0 ? ramCapacities.join(", ") : "Unknown");
  console.log("RAM Type:", ramType);
};

// Run the script
await getRamInfo();
