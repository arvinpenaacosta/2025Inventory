const runCommand = async (cmd: string[]) => {
  const process = Deno.run({
    cmd,
    stdout: "piped",
    stderr: "piped",
  });

  const output = await process.output();
  const error = await process.stderrOutput();
  process.close();

  if (error.length > 0) {
    return `Error: ${new TextDecoder().decode(error)}`;
  }

  return new TextDecoder().decode(output).trim();
};

const parseMemoryType = (type: string): string => {
  const typeMap: Record<string, string> = {
    "20": "DDR",
    "21": "DDR2",
    "22": "DDR3",
    "24": "DDR4",
    "26": "DDR5",
    "0": "Unknown"
  };
  return typeMap[type] || "Other";
};

const getSystemInfo = async () => {
  const info: Record<string, string> = {};

  info.ComputerName = await runCommand(["wmic", "computersystem", "get", "name"]);
  info.SerialNumber = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  info.PCBrand = await runCommand(["wmic", "computersystem", "get", "manufacturer"]); // PC Brand
  info.PCModel = await runCommand(["wmic", "computersystem", "get", "model"]);
  info.Processor = await runCommand(["wmic", "cpu", "get", "name"]);

  // RAM Information
  const ramSlots = await runCommand(["wmic", "memorychip", "get", "BankLabel"]);
  const ramCap = await runCommand(["wmic", "memorychip", "get", "Capacity"]);
  const ramType = await runCommand(["wmic", "memorychip", "get", "SMBIOSMemoryType"]);
  const ramSpeed = await runCommand(["wmic", "memorychip", "get", "Speed"]);
  const ramMfr = await runCommand(["wmic", "memorychip", "get", "Manufacturer"]);

  info.RAMSlot = ramSlots.split("\n").length - 1;
  info.RAMCapGB = ramCap.split("\n").map(val => `${parseInt(val.trim()) / 1073741824} GB`).join(", ");
  info.RAMType = ramType.split("\n").map(val => parseMemoryType(val.trim())).join(", ");
  info.SpeedMHz = ramSpeed.trim();
  info.Mfr = ramMfr.trim();

  console.log(JSON.stringify(info, null, 2));
};

await getSystemInfo();
