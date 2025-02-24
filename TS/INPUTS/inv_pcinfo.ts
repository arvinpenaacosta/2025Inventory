// Import required modules
import { config } from "https://deno.land/x/dotenv/mod.ts"; // to load environment variables
import { DB } from "https://deno.land/x/sqlite/mod.ts"; // to interact with SQLite



// Import Deno's readTextFile if needed (built-in in Deno)

  interface InventoryRecord {
    eid: string;
    phoneExt: string;
    floor: string;
    roomName: string;
    e1Answer: string | null;
    e2Answer: string;
    finalOutput: string;
  }

  async function main1(): Promise<InventoryRecord | null> {
    console.clear();

    const green: string = "\x1b[32m";
    const reset: string = "\x1b[0m";

    console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);
    console.log(`${green}+                 2 0 2 5               +${reset}`);
    console.log(`${green}+             V I N T O O L S           +${reset}`);
    console.log(`${green}+                                       +${reset}`);
    console.log(`${green}+        INVENTORY RECORDER Rev.2       +${reset}`);
    console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);

    let eid: string | null = null;
    while (true) {
      eid = prompt("Enter EID:");
      if (eid && eid.trim() !== "") {
        break;
      }
      console.log("EID is required. Please enter a valid EID.");
    }

    try {
      const dataText = await Deno.readTextFile("data2.json");
      const data = JSON.parse(dataText);

      console.log(`${green}=========================================${reset}`);
      console.log("Available Floors:");
      data.floors.forEach((floorObj: any) => {
        console.log(`- ${floorObj.floor}`);
      });

      let selectedFloor: any = null;
      while (true) {
        console.log(`${green}=========================================${reset}`);
        const selectedFloorInput = prompt("Select a floor from the list above:");
        if (!selectedFloorInput) {
          console.log("No floor selected. Please try again.");
          continue;
        }
        selectedFloor = data.floors.find((f: any) => f.floor === selectedFloorInput);
        if (!selectedFloor) {
          console.log("Floor not found. Please try again.");
          continue;
        }
        break;
      }

      console.log(`${green}=========================================${reset}`);
      console.log(`Available Rooms for Floor ${selectedFloor.floor}:`);
      selectedFloor.rooms.forEach((room: any) => {
        console.log(`${room.code} -> ${room.name}`);
      });

      let selectedRoom: any = null;
      while (true) {
        const selectedRoomCode = prompt("Select a room by entering its code:");
        if (!selectedRoomCode) {
          console.log("No room selected. Please try again.");
          continue;
        }
        selectedRoom = selectedFloor.rooms.find(
          (room: any) => room.code.toUpperCase() === selectedRoomCode.toUpperCase()
        );
        if (!selectedRoom) {
          console.log("Room code not found. Please try again.");
          continue;
        }
        break;
      }

      console.log(`${green}=========================================${reset}`);
      let e1Answer: string | null = null;
      if (typeof selectedRoom.E1 === "object") {
        console.log(selectedRoom.L1);
        for (const [key, value] of Object.entries(selectedRoom.E1)) {
          console.log(`  ${key}: ${value}`);
        }
        while (true) {
          const input = prompt(selectedRoom.L1);
          if (!input || !selectedRoom.E1.hasOwnProperty(input)) {
            console.log("Invalid selection for E1. Please try again.");
            continue;
          }
          e1Answer = selectedRoom.E1[input];
          break;
        }
      } else if (typeof selectedRoom.E1 === "string") {
        while (true) {
          e1Answer = prompt(selectedRoom.E1);
          if (!e1Answer) {
            console.log("No input provided for E1. Please try again.");
            continue;
          }
          break;
        }
      }

      console.log(`${green}=========================================${reset}`);
      let e2Answer: string | null = null;
      while (true) {
        e2Answer = prompt(selectedRoom.E2);
        if (!e2Answer) {
          console.log("No input provided for E2. Please try again.");
          continue;
        }
        break;
      }
      e2Answer = e2Answer.toUpperCase();

      console.log(`${green}=========================================${reset}`);
      const phoneExt = prompt("Enter Citrix Phone Ext (Optional):") || "";

      let finalOutput = `${selectedFloor.floor} ${selectedRoom.D1}${e1Answer}-${e2Answer}`;
      if (phoneExt.trim() !== "") {
        finalOutput += ` ext:${phoneExt}`;
      }



      // Return all the requested values in an object
      return {
        eid,
        phoneExt: phoneExt.trim() !== "" ? phoneExt : "None",
        floor: selectedFloor.floor,
        roomName: selectedRoom.name,
        e1Answer,
        e2Answer,
        finalOutput
      };

    } catch (error) {
      console.error("Error reading or parsing data2.json:", error);
      return null;
    }
  }


// +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
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
    eid TEXT,
    floor TEXT,
    room TEXT, 
    loc1 TEXT, 
    loc2 TEXT, 
    loc_name TEXT,
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

  // Example usage:
  async function run() {
    const result = await main1();
    if (result) {

    // Function to save system info to the SQLite database
    const saveToSQLite = async (systemInfo: any) => {
      const timestamp = formatTimestamp(new Date()); // Get formatted timestamp

      const enhancedSystemInfo = {
        ...systemInfo,
        eid: result.eid,
        floor:result.floor,
        room: result.roomName,
        loc1: result.e1Answer,
        loc2: result.e2Answer,
        loc_name: result.finalOutput
      };

      const {
        eid,
        floor,
        room,
        loc1,
        loc2,
        loc_name,
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
      } = enhancedSystemInfo;

      const query = `
        INSERT INTO pc_info_inv (
          eid, floor, room, loc1, loc2, loc_name, hostname, serial_number, processor, windows_version, display_version, 
          manufacturer, model, total_ram, ram_slots, ram_per_slot, 
          ram_speed, ram_type, ip_address, mac_address, citrix_name, citrix_version, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,  ?, ?, ?)
      `;

      db.query(query, [
        eid, floor, room, loc1, loc2, loc_name, Hostname, SerialNumber, Processor, WindowsVersion, DisplayVersion, Manufacturer, Model, TotalRAM, 
        RAMSlots, RAMPerSlot, RAMSpeed, RAMType, IPAddress, MACAddress, registryData.displayName, registryData.displayVersion, timestamp
      ]);
      
      console.log("✅ Data saved to SQLite");
      console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);
    };

    // Example usage: search for software "Citrix Workspace"
    const hive = "HKLM";
    const path = "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall";
    const searchPattern = "Citrix Workspace";
    const registryData = await searchRegistryWithGUID(hive, path, searchPattern);

    // Get system information and save it to SQLite




      console.clear();

      const green: string = "\x1b[32m";
      const reset: string = "\x1b[0m";

      console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);
      console.log(`${green}+                 2 0 2 5               +${reset}`);
      console.log(`${green}+             V I N T O O L S           +${reset}`);
      console.log(`${green}+                                       +${reset}`);
      console.log(`${green}+        INVENTORY RECORDER Rev.2       +${reset}`);
      console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);


      // Now you can access all the values outside main1()
      console.log("🔹 Locations:");
      console.log("EID:", result.eid);
      console.log("Phone Extension:", result.phoneExt);
      console.log("Floor:", result.floor);
      console.log("Room Type:", result.roomName);
      console.log("Location:", result.e1Answer);
      console.log("Seat #:", result.e2Answer);
      console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);
      console.log("Final Output:", result.finalOutput);
      console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);

      /*
      console.log("🔹 PC Information:");
      console.log("Serial Number:", SerialNumber);  // Use the destructured variable
      console.log("Processor:", Processor);         // Use the destructured variable
      console.log("Windows Version:", WindowsVersion);
      console.log("Manufacturer:", Manufacturer);
      console.log("Model:", Model);
      console.log("Total RAM Capacity:", TotalRAM);
      console.log("RAM Speed:", RAMSpeed);
      console.log("RAM Type:", RAMType);
      console.log("Number of RAM Slots:", RAMSlots);
 
      // Extract Display Version
      const displayVersionMatch = displayVersion?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);
      console.log("Windows Display Version:", displayVersionMatch ? displayVersionMatch[1] : "Unknown");

      // Output IP and MAC addresses
      console.log("IP Address:", ipAddressMatch ? ipAddressMatch[1] : "Not found");
      console.log("MAC Address:", macAddressMatch ? macAddressMatch[1] : "Not found");
      */




    const systemInfo = await getSystemInfo();
    await saveToSQLite(systemInfo);

    // Close the database connection
    db.close();




    }
  }

  run();




