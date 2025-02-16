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
  const serialNumber = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  const processor = await runCommand(["wmic", "cpu", "get", "name"]);
  const windowsVersion = await runCommand(["wmic", "os", "get", "caption"]);
  const displayVersion = await runCommand([
    "reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", 
    "/v", "DisplayVersion"
  ]);

  console.log("🔹 PC Information:");
  console.log("Serial Number:", serialNumber?.split("\n")[1]?.trim());
  console.log("Processor:", processor?.split("\n")[1]?.trim());
  console.log("Windows Version:", windowsVersion?.split("\n")[1]?.trim());

  // Extract Display Version
  const displayVersionMatch = displayVersion?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);
  console.log("Windows Display Version:", displayVersionMatch ? displayVersionMatch[1] : "Unknown");
};

await getSystemInfo();
