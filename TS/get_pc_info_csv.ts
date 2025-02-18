import { config } from "https://deno.land/x/dotenv/mod.ts";

// Load environment variables from .env
const env = config();

// Function to format the timestamp as YYYY-MM-DD HH:MM:SS
const formatTimestamp = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
};

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
  const serialNumber = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  const processor = await runCommand(["wmic", "cpu", "get", "name"]);
  const windowsVersion = await runCommand(["wmic", "os", "get", "caption"]);
  const displayVersion = await runCommand([
    "reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
    "/v", "DisplayVersion"
  ]);
  const manufacturer = await runCommand(["wmic", "computersystem", "get", "manufacturer"]);
  const model = await runCommand(["wmic", "computersystem", "get", "model"]);
  const capacityOutput = await runCommand(["wmic", "memorychip", "get", "capacity"]);
  const speedOutput = await runCommand(["wmic", "memorychip", "get", "speed"]);
  const typeOutput = await runCommand(["wmic", "memorychip", "get", "SMBIOSMemoryType"]);
  const slotOutput = await runCommand(["wmic", "memorychip", "get", "devicelocator"]);
  const ipConfigOutput = await runCommand(["ipconfig", "/all"]);

  const ipAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?IPv4 Address[ .]*: (\d+\.\d+\.\d+\.\d+)/s);
  const macAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?Physical.*?([\w-]{17})/s);

  const ramTypeMap: { [key: string]: string } = {
    "20": "DDR",
    "21": "DDR2",
    "24": "DDR3",
    "26": "DDR4",
    "29": "DDR5",
  };

  const slotLines = typeof slotOutput === "string"
    ? slotOutput.split("\n").map(line => line.trim()).filter(line => line.length > 0)
    : [];
  const numRamSlots = slotLines.length > 1 ? slotLines.length - 1 : "Unknown"; 

  let totalRamInGB = 0;
  let ramCapacities: string[] = [];
  if (capacityOutput) {
    const capacities = capacityOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    capacities.forEach(capacity => {
      const capacityGB = parseInt(capacity) / (1024 ** 3); 
      totalRamInGB += capacityGB;
      ramCapacities.push(`${capacityGB} GB`);
    });
  }

  const ramSpeed = speedOutput?.split("\n")[1]?.trim() || "Unknown";
  let ramType = "Unknown";
  if (typeOutput) {
    const typeLines = typeOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    ramType = typeLines.length > 0 ? (ramTypeMap[typeLines[0]] || "Unknown") : "Unknown";
  }

  const displayVersionMatch = displayVersion?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);

  return {
    SerialNumber: serialNumber?.split("\n")[1]?.trim() || "Unknown",
    Processor: processor?.split("\n")[1]?.trim() || "Unknown",
    WindowsVersion: windowsVersion?.split("\n")[1]?.trim() || "Unknown",
    DisplayVersion: displayVersionMatch ? displayVersionMatch[1] : "Unknown",
    Manufacturer: manufacturer?.split("\n")[1]?.trim() || "Unknown",
    Model: model?.split("\n")[1]?.trim() || "Unknown",
    TotalRAM: totalRamInGB.toFixed(2) + " GB",
    RAMSlots: numRamSlots,
    RAMPerSlot: ramCapacities.length > 0 ? ramCapacities.join(" | ") : "Unknown",
    RAMSpeed: ramSpeed,
    RAMType: ramType,
    IPAddress: ipAddressMatch ? ipAddressMatch[1] : "Not found",
    MACAddress: macAddressMatch ? macAddressMatch[1] : "Not found",
  };
};

// Access the variables
const filePath = env.FILE_PATH || "default_path";
const fileCsv = env.FILE_CSV || "default_filename.csv";

console.log(`File Path: ${filePath}`);
console.log(`CSV Filename: ${fileCsv}`);

const timestamp = formatTimestamp(new Date()); // Get formatted timestamp

const saveToCSV = async (filePath: string, fileCsv: string) => {
  const systemInfo = await getSystemInfo();

  const headers = "Serial Number,Processor,Windows Version,Display Version,Manufacturer,Model,Total RAM (GB),RAM Slots,RAM Per Slot,RAM Speed,RAM Type,IP Address,MAC Address,Time Recorded\n";
  const csvRow = `${systemInfo.SerialNumber},${systemInfo.Processor},${systemInfo.WindowsVersion},${systemInfo.DisplayVersion},${systemInfo.Manufacturer},${systemInfo.Model},${systemInfo.TotalRAM},${systemInfo.RAMSlots},${systemInfo.RAMPerSlot},${systemInfo.RAMSpeed},${systemInfo.RAMType},${systemInfo.IPAddress},${systemInfo.MACAddress},${timestamp}\n`;

  try {
    const filePathWithCsv = `${filePath}\\${fileCsv}`;
    const fileExists = await Deno.stat(filePathWithCsv).then(() => true).catch(() => false);

    if (!fileExists) {
      await Deno.writeTextFile(filePathWithCsv, headers + csvRow);
    } else {
      await Deno.writeTextFile(filePathWithCsv, csvRow, { append: true });
    }

    console.log(`✅ Data saved to ${filePathWithCsv}`);
  } catch (error) {
    console.error("❌ Error saving CSV file:", error);
  }
};

// Call function with correct parameters
await saveToCSV(env.FILE_PATH, env.FILE_CSV);


// Save to the file path and file name specified in the .env file
//await saveToCSV(filePath, fileCsv);


