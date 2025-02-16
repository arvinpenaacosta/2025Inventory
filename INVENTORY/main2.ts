const runCommand = async (cmd: string[]) => {
  const command = new Deno.Command(cmd[0], {
    args: cmd.slice(1),
    stdout: "piped",
    stderr: "piped",
  });

  const { stdout, stderr } = await command.output();

  if (stderr.length > 0) {
    console.error(`Error: ${new TextDecoder().decode(stderr)}`);
    return null;
  }

  return new TextDecoder().decode(stdout).trim();
};

const parseWmicOutput = (output: string) => {
  const lines = output.split("\n").map(line => line.trim()).filter(line => line);
  return lines.length > 1 ? lines.slice(1).join(", ") : lines[0] || "N/A";
};

const getSystemInfo = async () => {
  const info: Record<string, string> = {};

  const commands = {
    ComputerName: ["wmic", "computersystem", "get", "name"],
    SerialNumber: ["wmic", "bios", "get", "serialnumber"],
    PCModel: ["wmic", "computersystem", "get", "model"],
    Processor: ["wmic", "cpu", "get", "name"],
    RAMSlot: ["wmic", "memorychip", "get", "BankLabel"],
    RAMCapGB: ["wmic", "memorychip", "get", "Capacity"],
    RAMType: ["wmic", "memorychip", "get", "MemoryType"],
    SpeedMHz: ["wmic", "memorychip", "get", "Speed"],
    Mfr: ["wmic", "memorychip", "get", "Manufacturer"],
    IPAddress: ["wmic", "nicconfig", "where", "IPEnabled=true", "get", "IPAddress"],
    MACAddress: ["wmic", "nicconfig", "where", "IPEnabled=true", "get", "MACAddress"],
    WindowsEdition: ["wmic", "os", "get", "Caption"],
    DisplayVersion: ["wmic", "os", "get", "Version"],
    OSVersion: ["wmic", "os", "get", "BuildNumber"],
    CitrixName: ["wmic", "product", "where", "Name like 'Citrix%'", "get", "Name"],
    CitrixVersion: ["wmic", "product", "where", "Name like 'Citrix%'", "get", "Version"],
  };

  for (const [key, cmd] of Object.entries(commands)) {
    const output = await runCommand(cmd);
    info[key] = output ? parseWmicOutput(output) : "N/A";
  }

  console.log(JSON.stringify(info, null, 2));
};

await getSystemInfo();
