import QRCode from "https://esm.sh/qrcode@1.5.3";
import { parse } from "https://deno.land/std@0.224.0/flags/mod.ts";
import { join } from "https://deno.land/std@0.224.0/path/mod.ts";
// Add SQLite dependency
import { DB } from "https://deno.land/x/sqlite/mod.ts"; // to interact with SQLite
// Add environment variable support
import { config } from "https://deno.land/x/dotenv@v3.2.2/mod.ts";
import { readJson } from "https://deno.land/x/jsonfile/mod.ts";


class InventoryRecorder {
    private COLORS = {
      green: "\x1b[32m",
      red: "\x1b[31m",
      yellow: "\x1b[33m",
      blue: "\x1b[34m",
      reset: "\x1b[0m",
    };
  
    private data: any;
    private answers: Record<string, any> = {};
  
    constructor() {}
  
    async loadData() {
      this.data = await readJson("data3.json");
    }

    public displayBanner() {
        console.clear();
        console.log(`${this.COLORS.green}+++++++++++++++++++++++++++++++++++++++++${this.COLORS.reset}`);
        console.log(`${this.COLORS.green}+                 2 0 2 5               +${this.COLORS.reset}`);
        console.log(`${this.COLORS.green}+             V I N T O O L S           +${this.COLORS.reset}`);
        console.log(`${this.COLORS.green}+                                       +${this.COLORS.reset}`);
        console.log(`${this.COLORS.green}+        INVENTORY RECORDER Rev.2       +${this.COLORS.reset}`);
        console.log(`${this.COLORS.green}+         Powered by DENO-DevApp        +${this.COLORS.reset}`);
        console.log(`${this.COLORS.green}+++++++++++++++++++++++++++++++++++++++++${this.COLORS.reset}`);
    }
  
    private formatRange(numbers: number[]): string {
      if (numbers.length === 0) return "";
  
      numbers.sort((a, b) => a - b);
      let ranges: string[] = [];
      let start = numbers[0];
      let end = start;


      for (let i = 1; i < numbers.length; i++) {
        if (numbers[i] === end + 1) {
          end = numbers[i];
        } else {
          ranges.push(start === end ? `${start}` : `${start}-${end}`);
          start = numbers[i];
          end = start;
        }
      }
      ranges.push(start === end ? `${start}` : `${start}-${end}`);
      return ranges.join(", ");
    }
  
    private async askQuestion(question: string, validChoices: string[], applyFormatRange = true): Promise<string> {
      let answer: string | null = null;
      let retries = 5;

      const isNumeric = validChoices.every((val) => !isNaN(Number(val)));
      const formattedChoices = isNumeric && applyFormatRange 
        ? this.formatRange(validChoices.map(Number)) 
        : validChoices.join(", ");
  
      while (!validChoices.includes(answer?.toUpperCase() || "")) {
        console.log(`\n${question}`);
        console.log(`Valid choices: ${formattedChoices}`);
        answer = (prompt("Enter your choice: ") ?? "").trim().toUpperCase() || null;
        retries--;

        if (!validChoices.includes(answer || "")) {
          console.log("-----------------------------------------");
          console.log(`${this.COLORS.red}❌ ${this.COLORS.reset} Invalid choice. Please try again.`);
          console.log("-----------------------------------------");
        }
      }
      console.log(`${this.COLORS.green}=========================================${this.COLORS.reset}`);
      console.log(`${this.COLORS.green}✅${this.COLORS.reset} You selected: ${this.COLORS.yellow}${answer}${this.COLORS.reset}`);
      console.log(`${this.COLORS.green}=========================================${this.COLORS.reset}`);

      if (retries === 0) {
        throw new Error("Too many invalid attempts.");
      }

      return answer!;
    }
  
    async run() {
      console.clear();

      this.displayBanner();
  
      await this.loadData();
  
      // Floor selection
      const floorChoices = this.data.floors.map((floor: any) => floor.floor);
      this.answers.floor = await this.askQuestion(`${this.COLORS.yellow}Select a floor:${this.COLORS.reset}`, floorChoices, false);
  
      const floorData = this.data.floors.find((floor: any) => floor.floor === this.answers.floor);
      const roomChoices: Record<string, string> = Object.fromEntries(
        floorData.rooms.map((room: any) => [Object.keys(room.CO)[0].toUpperCase(), Object.values(room.CO)[0]])
      );
  
      console.log(`${this.COLORS.yellow}\nLocations :${this.COLORS.reset}`);
      Object.entries(roomChoices).forEach(([key, value]) => console.log(`${key} - ${value}`));
  
      // Room selection
      const selectedRoomKey = await this.askQuestion("Select Location key (e.g., P for Pod):", Object.keys(roomChoices));
      this.answers.room = selectedRoomKey;
      this.answers.room_name = roomChoices[selectedRoomKey];
  
      const roomData = floorData.rooms.find((room: any) => Object.keys(room.CO)[0].toUpperCase() === selectedRoomKey);
      this.answers.D1 = roomData.D1;
  
      // E1 selection (if available)
      if (roomData.E1) {
        const e1Range = roomData.E1.Range as number[] | Record<string, string>;
        console.log(`\n${roomData.E1.label}`);
  
        let e1Answer: string;
        if (typeof e1Range === "object" && !Array.isArray(e1Range)) {
          Object.entries(e1Range).forEach(([key, value]) => console.log(`${key} - ${value}`));
          const selectedIndex = await this.askQuestion("Enter index:", Object.keys(e1Range), false);
          e1Answer = e1Range[selectedIndex];
        } else {
          e1Answer = await this.askQuestion(roomData.E1.label, (e1Range as number[]).map(String));
        }
  
        this.answers.E1 = e1Answer;
      }
  
      // E2 selection (if available)
      if (roomData.E2) {
        const e2Choices = roomData.E2.Range.map(String);
        this.answers.E2 = await this.askQuestion(roomData.E2.label, e2Choices);
      }
  
    }
    
    getResults() {
      return this.answers;
    }

  }

// Set Color effect
const COLORS = {
  green: "\x1b[32m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  reset: "\x1b[0m",
};

// Load environment variables from .env file
const env = config();

// Get system's temporary folder
const tempDir = Deno.env.get("TMP") || Deno.env.get("TEMP") || "/tmp";
// We'll set the actual filename after we get the system info

// Parse command line arguments
const args = parse(Deno.args, {
  string: ["output", "db", "input"],
  boolean: ["qr", "saveToDb"],
  default: {
    output: "", // We'll set this later with the hostname and serial number
    qr: false, // Default: don't display QR code
    db: "", // Default is empty, we'll use .env values if available
    saveToDb: false, // Default: don't save to database
    e : "", // Default is empty, won't use InventoryRecorder if not provided
  },
});

/**
 * Executes a Windows command and returns the output as a string
 * @param cmd Array of command arguments
 * @returns Trimmed stdout output or null if there's an error
 */
const runCommand = async (cmd: string[]): Promise<string | null> => {
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

/**
 * Extracts the value from command output (skipping the header line)
 * @param output Command output string
 * @returns Trimmed value or "Unknown" if not found
 */
const extractValue = (output: string | null): string => {
  if (!output) return "Unknown";
  const lines = output.split("\n").map(line => line.trim()).filter(line => line.length > 0);
  return lines.length > 1 ? lines[1] : "Unknown";
};

/**
 * Searches the Windows registry for software information
 * @param hive Registry hive (e.g., "HKLM")
 * @param path Registry path
 * @param searchPattern Software name to search for
 * @returns Object containing displayName and displayVersion
 */
const searchRegistry = async (
  hive: string, 
  path: string, 
  searchPattern: string
): Promise<{ displayName: string; displayVersion: string }> => {
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
      displayName = line.trim().split('REG_SZ')[1]?.trim() || '';
    }
    if (line.toLowerCase().includes("displayversion") && displayName !== '') {
      displayVersion = line.trim().split('REG_SZ')[1]?.trim() || '';
    }
    if (displayName && displayVersion) {
      return { displayName, displayVersion };
    }
  }

  return { displayName: "Not found", displayVersion: "Not found" };
};

/**
 * Retrieves comprehensive system information
 * @returns Object containing system information
 */
const getSystemInfo = async () => {
  // RAM Type Mapping
  const ramTypeMap: { [key: string]: string } = {
    "20": "DDR",
    "21": "DDR2",
    "24": "DDR3",
    "26": "DDR4",
    "29": "DDR5",
  };
  
  // Get timestamp in Philippines time zone (UTC+8)
  const timestamp = new Date(new Date().getTime() + 8 * 60 * 60 * 1000).toISOString().replace('T', ' ').split('.')[0];
  const username = Deno.env.get("USERNAME") || Deno.env.get("USER");
  const hostnameOutput = await runCommand(["wmic", "computersystem", "get", "name"]);
  const hostname = extractValue(hostnameOutput);
  const serialNumberOutput = await runCommand(["wmic", "bios", "get", "serialnumber"]);
  const serialNumber = extractValue(serialNumberOutput);
  const processorOutput = await runCommand(["wmic", "cpu", "get", "name"]);
  const processor = extractValue(processorOutput);
  const windowsVersionOutput = await runCommand(["wmic", "os", "get", "caption"]);
  const windowsVersion = extractValue(windowsVersionOutput);
  const displayVersionOutput = await runCommand([
    "reg", "query", "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
    "/v", "DisplayVersion"
  ]);
  const displayVersionMatch = displayVersionOutput?.match(/DisplayVersion\s+REG_SZ\s+(\S+)/);
  const windowsDisplayVersion = displayVersionMatch ? displayVersionMatch[1] : "Unknown";
  const manufacturerOutput = await runCommand(["wmic", "computersystem", "get", "manufacturer"]);
  const manufacturer = extractValue(manufacturerOutput);
  const modelOutput = await runCommand(["wmic", "computersystem", "get", "model"]);
  const model = extractValue(modelOutput);

  // Get RAM details
  const capacityOutput = await runCommand(["wmic", "memorychip", "get", "capacity"]);
  const speedOutput = await runCommand(["wmic", "memorychip", "get", "speed"]);
  const typeOutput = await runCommand(["wmic", "memorychip", "get", "SMBIOSMemoryType"]);
  const slotOutput = await runCommand(["wmic", "memorychip", "get", "devicelocator"]);

  // Process RAM information
  const slotLines = slotOutput ? 
    slotOutput.split("\n").map(line => line.trim()).filter(line => line.length > 0) : 
    [];
  
  const numRamSlots = slotLines.length > 1 ? slotLines.length - 1 : "Unknown"; // Exclude header row

  // Process RAM capacities
  let totalRamInGB = 0;
  const ramCapacities: string[] = [];
  if (capacityOutput) {
    const capacities = capacityOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    capacities.forEach(capacity => {
      const capacityGB = parseInt(capacity) / (1024 ** 3); // Convert bytes to GB
      totalRamInGB += capacityGB;
      ramCapacities.push(`${capacityGB.toFixed(2)} GB`);
    });
  }

  const totalRam = totalRamInGB.toFixed(2);
  const ramPerSlot = ramCapacities.length > 0 ? ramCapacities.join(" > ") : "Unknown";

  // Process RAM speed and type
  const ramSpeed = speedOutput?.split("\n")[1]?.trim() || "Unknown";
  let ramType = "Unknown";
  if (typeOutput) {
    const typeLines = typeOutput.split("\n").map(line => line.trim()).filter(line => /^\d+$/.test(line));
    ramType = typeLines.length > 0 ? (ramTypeMap[typeLines[0]] || "Unknown") : "Unknown";
  }

  // Get network information
  const ipConfigOutput = await runCommand(["ipconfig", "/all"]);
  const ipAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?IPv4 Address[ .]*: (\d+\.\d+\.\d+\.\d+)/s);
  const ipAddress = ipAddressMatch ? ipAddressMatch[1] : "Not found";
  const macAddressMatch = ipConfigOutput?.match(/Ethernet adapter.*?Physical.*?([\w-]{17})/s);
  const macAddress = macAddressMatch ? macAddressMatch[1] : "Not found";
  const formattedMac = macAddress !== "Not found" ? 
    macAddress.replace(/-/g, "").match(/.{1,4}/g)?.join(".") || "Not found" : 
    "Not found";

  // Get Citrix information
  const citrixData = await searchRegistry(
    "HKLM",
    "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
    "Citrix Workspace"
  );
  //+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  // Create the system info object
  const systemInfo = {
    logUser: username,
    hostname,
    serialNumber,
    processor,
    windowsVersion,
    windowsDisplayVersion,
    manufacturer,
    model,
    totalRam: `${totalRam} GB`,
    numRamSlots,
    ramPerSlot,
    ramSpeed: `${ramSpeed} MHz`,
    ramType,
    ipAddress,
    macAddress: formattedMac,
    citrixName: citrixData.displayName,
    citrixVersion: citrixData.displayVersion,
    Timestamp: timestamp,
  };


  // Output all system info
  console.log(`${COLORS.green}🔹 PC Information:${COLORS.reset}`);
  console.log("   Log User:", systemInfo.logUser);
  console.log("   Hostname:", systemInfo.hostname);
  console.log("   Serial Number:", systemInfo.serialNumber);
  console.log("   Processor:", systemInfo.processor);
  console.log("   Windows Version:", systemInfo.windowsVersion);
  console.log("   Windows Display Version:", systemInfo.windowsDisplayVersion);
  console.log("   Manufacturer:", systemInfo.manufacturer);
  console.log("   Model:", systemInfo.model);

  console.log(`\n${COLORS.green}🔹 RAM Information:${COLORS.reset}`);
  console.log("   Total RAM Capacity:", systemInfo.totalRam);
  console.log("   Number of RAM Slots:", systemInfo.numRamSlots);
  console.log("   RAM Installed per Slot:", systemInfo.ramPerSlot);
  console.log("   RAM Speed:", systemInfo.ramSpeed);
  console.log("   RAM Type:", systemInfo.ramType);

  console.log(`\n${COLORS.green}🔹 Network Information:${COLORS.reset}`);
  console.log("   IP Address:", systemInfo.ipAddress);
  console.log("   MAC Address:", systemInfo.macAddress);

  console.log(`\n${COLORS.green}🔹 Citrix Information:${COLORS.reset}`);
  console.log("   Citrix Name:", systemInfo.citrixName);
  console.log("   Citrix Version:", systemInfo.citrixVersion);
  console.log("   Timestamp:", systemInfo.Timestamp);

  return systemInfo;
};

/**
 * Generates a QR code from the provided text and saves it as an image.
 */
async function generateQRCode(text: string, outputFile: string) {
  try {
    await QRCode.toFile(outputFile, text, {
      errorCorrectionLevel: "H",
      margin: 1,
      scale: 8,
      color: {
        dark: "#000000",
        light: "#ffffff",
      },
    });
    console.log(`${COLORS.green}+++++++++++++++++++++++++++++++++++++++++${COLORS.reset}`);
    console.log(`QR code saved to: ${outputFile}`);
    return true;
  } catch (error) {
    console.error("Error generating QR code:", error);
    return false;
  }
}

/**
 * Opens the generated QR code image in the default browser
 */
 async function openInBrowser(filePath: string, hostname?: string) {
    const htmlPath = filePath.replace(/\.png$/, ".html"); // Change PNG path to HTML path
  
    // Create an HTML file with the image and hostname
    const htmlContent = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Image Viewer</title>
      <style>
        * {
          margin: 0; padding: 0;  box-sizing: border-box;
        }
    
        body {
          display: flex; flex-direction: column; justify-content: center; align-items: center;
          height: 100vh; background-color: #000; color: white; font-family: Arial, sans-serif;
        }
        .header, .footer {
          position: fixed; width: 100%; text-align: center; background: rgba(0, 0, 0, 0.8); /* Slight transparency */
          padding: 10px 0;
        }
        .header {
          top: 0; font-size: 1.5em; font-weight: bold; border-bottom: 2px solid white;
        }
        .footer {
          bottom: 0; font-size: 1em; border-top: 2px solid white;
        }
        .content {
          display: flex; flex-direction: column; justify-content: center; align-items: center;
          flex-grow: 1; text-align: center; width: 100%;
        }
        img {
          max-width: 70vw; max-height: 70vh;
        }
        .info {
          margin-top: 20px; font-size: 1.2em;
        }
      </style>
    </head>
    <body>
    
      <!-- Header -->
      <div class="header">PC Info QR Code Viewer</div>
    
      <!-- Content (QR Code and Hostname) -->
      <div class="content">
        <img src="file:///${filePath}" alt="QR Code">
        <div class="info">${hostname ? `Hostname : ${hostname}` : ""}</div>
      </div>
    
      <!-- Footer -->
      <div class="footer">Powered by <Deno2.2> DevAppVin</div>
    
    </body>
    </html>
    
    `;
  
    // Write the HTML file
    await Deno.writeTextFile(htmlPath, htmlContent);
  
    // Open the HTML file in the browser
    const browserCommands: Record<string, string[]> = {
      windows: ["cmd", "/c", "start", "chrome", htmlPath],
      darwin: ["open", "-a", "Google Chrome", htmlPath],
      linux: ["google-chrome", htmlPath],
    };
  
    const osType = Deno.build.os;
    if (browserCommands[osType]) {
      try {
        await new Deno.Command(browserCommands[osType][0], {
          args: browserCommands[osType].slice(1),
        }).output();
        console.log("QR code opened in browser with system info.");
        return true;
      } catch (error) {
        console.error("Error opening browser:", error);
        return false;
      }
    } else {
      console.error("Unsupported OS. Please open the file manually:", htmlPath);
      return false;
    }
  }
  
/**
 * Sanitizes a string to be safe for filenames
 * Removes/replaces characters that aren't allowed in filenames
 */
function sanitizeForFilename(str: string): string {
  // Replace invalid filename characters with underscores
  return str.replace(/[\\/:*?"<>|]/g, '_');
}

/**
 * Get the database file path from environment variables or command line args
 */
function getDatabasePath(): string {
  // First check if path is provided via command line
  if (args.db) {
    return args.db;
  }
  
  // Then check if path is provided via environment variables
  if (env.FILE_PATH && env.FILE_SQLITE) {
    return `${env.FILE_PATH}\\${env.FILE_SQLITE}.db`;
  }
  
  // Default fallback
  return "./inventory.db";
}

/**
 * Initialize SQLite database and create table if it doesn't exist
 */
function initDatabase(): DB {
  try {
    const dbPath = getDatabasePath();
    console.log(`Using database at: ${dbPath}`);
    
    const db = new DB(dbPath);
    
    // Create the inventory table if it doesn't exist
    db.query(`
      CREATE TABLE IF NOT EXISTS inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        floor TEXT,
        roomname TEXT,
        loc1 TEXT,
        loc2 TEXT,
        locEAM TEXT,

        log_user TEXT,
        hostname TEXT,
        serial_number TEXT,
        processor TEXT,
        windows_version TEXT,
        windows_display_version TEXT,
        manufacturer TEXT,
        model TEXT,
        total_ram TEXT,
        num_ram_slots TEXT,
        ram_per_slot TEXT,
        ram_speed TEXT,
        ram_type TEXT,
        ip_address TEXT,
        mac_address TEXT,
        citrix_name TEXT,
        citrix_version TEXT,
        timestamp TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    return db;
  } catch (error) {
    console.error("Error initializing database:", error);
    throw error;
  }
}

/**
 * Save system information to SQLite database
 */
 function saveToDatabase(db: DB, systemInfo: any, locationInfo: any = null): boolean {
    try {
      // Prepare location information if available
      const floor = locationInfo?.floor || null;
      const roomName = locationInfo?.room_name || null;
      const d1 = locationInfo?.D1 || null;
      const e1 = locationInfo?.E1 || null;
      const e2 = locationInfo?.E2 || null;
      const de1 = d1 && e1 ? `${d1}${e1}` : null;

      // Insert new record with location information if available
      db.query(
        `INSERT INTO inventory (
            floor,
            roomname,
            loc1,
            loc2,

            log_user,
            hostname,
            serial_number,
            processor,
            windows_version,
            windows_display_version,
            manufacturer,
            model,
            total_ram,
            num_ram_slots,
            ram_per_slot,
            ram_speed,
            ram_type,
            ip_address,
            mac_address,
            citrix_name,
            citrix_version,
            timestamp
          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [
          floor,
          roomName,
          de1,
          e2,

          systemInfo.logUser,
          systemInfo.hostname,
          systemInfo.serialNumber,
          systemInfo.processor,
          systemInfo.windowsVersion,
          systemInfo.windowsDisplayVersion,
          systemInfo.manufacturer,
          systemInfo.model,
          systemInfo.totalRam,
          systemInfo.numRamSlots,
          systemInfo.ramPerSlot,
          systemInfo.ramSpeed,
          systemInfo.ramType,
          systemInfo.ipAddress,
          systemInfo.macAddress,
          systemInfo.citrixName,
          systemInfo.citrixVersion,
          systemInfo.Timestamp,
        ]
      );
      
      console.log(`Added new record with serial number: ${COLORS.red}${systemInfo.serialNumber}${COLORS.reset}`);
      return true;
    } catch (error) {
      console.error("Error saving to database:", error);
      return false;
    }
  }

/**
 * Main function to run the workflow sequentially
 */
async function main() {
let locationInfo = null;  // Initialize locationInfo to prevent ReferenceError

// Step 0: Process input data if --entry flag is provided
if (args.entry) {
    try {
    // Create an instance and run the script
    const inventory = new InventoryRecorder();
    await inventory.run();
    inventory.displayBanner();

    // Retrieve results
    locationInfo = inventory.getResults();  // Assign the results to locationInfo

    console.log(`\n${COLORS.green}🔹 Item Location Info:${COLORS.reset}`);
    console.log(`   Floor: ${locationInfo.floor}`);
    console.log(`   Location Name: ${locationInfo.room_name}`);
    console.log(`   Location: ${locationInfo.D1}${locationInfo.E1 || ""}`);
    if (locationInfo.E2) console.log(`   Seat/Station: ${locationInfo.E2}`);
    console.log();

    } catch (error) {
    console.error(`\n${COLORS.red}Error processing Entry data:${COLORS.reset}`, error);
    }
}

 
  // Step 1: Collecting system information
  const systemInfo = await getSystemInfo();
  
  // Generate dynamic filename using hostname and serial number
  const safeHostname = sanitizeForFilename(systemInfo.hostname);
  const safeSerialNumber = sanitizeForFilename(systemInfo.serialNumber);
  
  // Create the dynamic filename
  const dynamicFilename = `${safeHostname}_${safeSerialNumber}.png`;
  
  // Set the output path (use provided path or create from temp dir + dynamic filename)
  const outputPath = args.output || join(tempDir, dynamicFilename);
  
  // Step 2: Generating QR code
  const qrSuccess = await generateQRCode(JSON.stringify(systemInfo), outputPath);
  
  // Step 3: Save to database if flag is set
  if (args.saveToDb) {
    console.log(`\n${COLORS.green}🔹 Database Operation:${COLORS.reset}`);
    try {
      const db = initDatabase();
      const dbSuccess = saveToDatabase(db, systemInfo, locationInfo);
      
      if (dbSuccess) {
        console.log(`   System information saved to database...`);
      } else {
        console.log("   Failed to save system information to database");
      }
      
      // Close the database connection
      db.close();
    } catch (error) {
      console.error("   Database operation failed:", error);
    }
  }
  
  // Step 4: Display QR code if flag is set
  if (qrSuccess && args.qr) {
    await openInBrowser(outputPath, systemInfo.hostname || "Unknown Host");
  }
  
  console.log("\nProcess completed!");
}

// Show usage information if --help is provided
if (args.help) {
  console.log("System Information QR Code Generator and Inventory Tool");
  console.log("\nUsage:");
  console.log("  deno run --allow-run --allow-env --allow-read --allow-write --allow-net script.ts [options]");
  console.log("\nOptions:");
  console.log("  --qr                 Display QR code in browser (default: false)");
  console.log("  --output=<path>      Specify custom output path for QR code image");
  console.log("                       (default: <temp_dir>/<hostname>_<serialnumber>.png)");
  console.log("  --saveToDb           Save system information to SQLite database (default: false)");
  console.log("  --db=<path>          Specify SQLite database file path");
  console.log("                       (default: uses FILE_PATH and FILE_SQLITE from .env file)");
  console.log("  --entry[=<file>]     Import and run InventoryRecorder class from input_class.ts");
  console.log("                       (provide optional JSON file path or defaults to data3.json)");
  console.log("  --help               Show this help message");
  console.log("\nEnvironment Variables (.env file):");
  console.log("  FILE_PATH            Directory path for the SQLite database");
  console.log("  FILE_SQLITE          SQLite filename (without .db extension)");
}

// Run the script
await main();