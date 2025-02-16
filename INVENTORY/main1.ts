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

const parseWmicOutput = (output: string) => {
  const lines = output.split("\n").map(line => line.trim()).filter(line => line);
  return lines.length > 1 ? lines.slice(1).join(", ") : lines[0] || "N/A";
};

const getSystemInfo = async () => {
  const info: Record<string, string> = {};

  info.ComputerName = await runCommand(["wmic", "computersystem", "get", "name"]);
  info.SerialNumber = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  info.PCModel = await runCommand(["wmic", "computersystem", "get", "model"]);
  info.Processor = await runCommand(["wmic", "cpu", "get", "name"]);
  info.RAMSlot = await runCommand(["wmic", "memorychip", "get", "BankLabel"]);
  info.RAMCapGB = await runCommand(["wmic", "memorychip", "get", "Capacity"]);
  info.RAMType = await runCommand(["wmic", "memorychip", "get", "MemoryType"]);
  info.SpeedMHz = await runCommand(["wmic", "memorychip", "get", "Speed"]);
  info.Mfr = await runCommand(["wmic", "memorychip", "get", "Manufacturer"]);

  info.IPAddress = await runCommand(["wmic", "nicconfig", "where", "IPEnabled=true", "get", "IPAddress"]);
  info.MACAddress = await runCommand(["wmic", "nicconfig", "where", "IPEnabled=true", "get", "MACAddress"]);
  
  info.WindowsEdition = await runCommand(["wmic", "os", "get", "Caption"]);
  info.DisplayVersion = await runCommand(["wmic", "os", "get", "Version"]);
  info.OSVersion = await runCommand(["wmic", "os", "get", "BuildNumber"]);

  info.CitrixName = await runCommand(["wmic", "product", "where", "Name like 'Citrix%'", "get", "Name"]);
  info.CitrixVersion = await runCommand(["wmic", "product", "where", "Name like 'Citrix%'", "get", "Version"]);

  // Format output
  for (const key in info) {
    info[key] = parseWmicOutput(info[key]);
  }

  console.log(JSON.stringify(info, null, 2));
};

await getSystemInfo();
