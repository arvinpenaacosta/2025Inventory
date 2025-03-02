// Import required modules
import { config } from "https://deno.land/x/dotenv/mod.ts"; // to load environment variables
import { DB } from "https://deno.land/x/sqlite/mod.ts"; // to interact with SQLite

// Load environment variables from .env file
const env = config();

// Get the SQLite file path from .env
const dbPath = `${env.FILE_PATH}\\${env.FILE_SQLITE}.db`;

// Connect to the SQLite database (it will create the file if it doesn't exist)
const db = new DB(dbPath);

// Create table if it does not exist
db.query(`
  CREATE TABLE IF NOT EXISTS pc_info_inv (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT,
    serial_number TEXT,
    processor TEXT,
    windows_version TEXT,
    display_version TEXT,
    manufacturer TEXT,
    model TEXT,
    total_ram TEXT,
    ram_slots TEXT,
    ram_per_slot TEXT,
    ram_speed TEXT,
    ram_type TEXT,
    ip_address TEXT,
    mac_address TEXT,
    citrix_name TEXT,
    citrix_version TEXT,
    timestamp TEXT
  )
`);

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

// Function to run commands in the system (e.g., to get system info)
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

// Function to retrieve system information
const getSystemInfo = async () => {
  const hostname = await runCommand(["wmic", "computersystem", "get", "name"]);
  
  const serialNumber = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  const processor = await runCommand(["wmic", "cpu", "get", "name"]);
  const windowsVersion = await runCommand(["wmic", "os", "get", "caption"]);
  const windispLayversion = await runCommand([ 
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

  const windispLayversionMatch = windispLayversion?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);

  return {
    Hostname: hostname?.split("\n")[1]?.trim() || "Unknown",
    SerialNumber: serialNumber?.split("\n")[1]?.trim() || "Unknown",
    Processor: processor?.split("\n")[1]?.trim() || "Unknown",
    WindowsVersion: windowsVersion?.split("\n")[1]?.trim() || "Unknown",
    DisplayVersion: windispLayversionMatch ? windispLayversionMatch[1] : "Unknown",
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

// Function to save system info to the SQLite database
const saveToSQLite = async (systemInfo: any) => {
  const timestamp = formatTimestamp(new Date()); // Get formatted timestamp

  const {
    Hostname,
    SerialNumber,
    Processor,
    WindowsVersion,
    DisplayVersion,
    Manufacturer,
    Model,
    TotalRAM,
    RAMSlots,
    RAMPerSlot,
    RAMSpeed,
    RAMType,
    IPAddress,
    MACAddress,
  } = systemInfo;

  const query = `
    INSERT INTO pc_info_inv (
      hostname, serial_number, processor, windows_version, display_version, 
      manufacturer, model, total_ram, ram_slots, ram_per_slot, 
      ram_speed, ram_type, ip_address, mac_address, citrix_name, citrix_version, timestamp
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `;

  db.query(query, [
    Hostname, SerialNumber, Processor, WindowsVersion, DisplayVersion, Manufacturer, Model, TotalRAM, 
    RAMSlots, RAMPerSlot, RAMSpeed, RAMType, IPAddress, MACAddress, registryData.displayName, registryData.displayVersion, timestamp
  ]);
  
  console.log("✅ Data saved to SQLite");
};

// Example usage: search for software "Citrix Workspace"
const hive = "HKLM";
const path = "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall";
const searchPattern = "Citrix Workspace";
const registryData = await searchRegistryWithGUID(hive, path, searchPattern);

// Get system information and save it to SQLite
const systemInfo = await getSystemInfo();
await saveToSQLite(systemInfo);

// Close the database connection
db.close();