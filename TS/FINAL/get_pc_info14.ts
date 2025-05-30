import QRCode from "https://esm.sh/qrcode@1.5.3";
import { parse } from "https://deno.land/std@0.224.0/flags/mod.ts";
import { join } from "https://deno.land/std@0.224.0/path/mod.ts";

// Get system's temporary folder
const tempDir = Deno.env.get("TMP") || Deno.env.get("TEMP") || "/tmp";
// We'll set the actual filename after we get the system info

// Parse command line arguments
const args = parse(Deno.args, {
  string: ["output"],
  boolean: ["qr"],
  default: {
    output: "", // We'll set this later with the hostname and serial number
    qr: false, // Default: don't display QR code
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
  const green: string = "\x1b[32m";
  const reset: string = "\x1b[0m";
  console.log(`${green}🔹 PC Information:${reset}`);
  console.log("   Log User:", systemInfo.logUser);
  console.log("   Hostname:", systemInfo.hostname);
  console.log("   Serial Number:", systemInfo.serialNumber);
  console.log("   Processor:", systemInfo.processor);
  console.log("   Windows Version:", systemInfo.windowsVersion);
  console.log("   Windows Display Version:", systemInfo.windowsDisplayVersion);
  console.log("   Manufacturer:", systemInfo.manufacturer);
  console.log("   Model:", systemInfo.model);

  console.log(`\n${green}🔹 RAM Information:${reset}`);
  console.log("   Total RAM Capacity:", systemInfo.totalRam);
  console.log("   Number of RAM Slots:", systemInfo.numRamSlots);
  console.log("   RAM Installed per Slot:", systemInfo.ramPerSlot);
  console.log("   RAM Speed:", systemInfo.ramSpeed);
  console.log("   RAM Type:", systemInfo.ramType);

  console.log(`\n${green}🔹 Network Information:${reset}`);
  console.log("   IP Address:", systemInfo.ipAddress);
  console.log("   MAC Address:", systemInfo.macAddress);

  console.log(`\n${green}🔹 Citrix Information:${reset}`);
  console.log("   Citrix Name:", systemInfo.citrixName);
  console.log("   Citrix Version:", systemInfo.citrixVersion);
  console.log("   Timestamp:", systemInfo.Timestamp);
  console.log("=================================================");

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
async function openInBrowser(filePath: string) {
  const imagePath = `file:///${filePath}`;
  const browserCommands: Record<string, string[]> = {
    windows: ["cmd", "/c", "start", "chrome", imagePath], // Change to "msedge" or "firefox" if needed
    darwin: ["open", "-a", "Google Chrome", imagePath], // macOS
    linux: ["google-chrome", imagePath], // Linux (Change to "firefox" if needed)
  };
  
  const osType = Deno.build.os;
  if (browserCommands[osType]) {
    try {
      await new Deno.Command(browserCommands[osType][0], {
        args: browserCommands[osType].slice(1),
      }).output();
      console.log("QR code opened in browser");
      return true;
    } catch (error) {
      console.error("Error opening browser:", error);
      return false;
    }
  } else {
    console.error("Unsupported OS. Please open the file manually:", imagePath);
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
 * Main function to run the workflow sequentially
 */
async function main() {
  console.clear();

  const green: string = "\x1b[32m";
  const reset: string = "\x1b[0m";

  console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);
  console.log(`${green}+                 2 0 2 5               +${reset}`);
  console.log(`${green}+             V I N T O O L S           +${reset}`);
  console.log(`${green}+                                       +${reset}`);
  console.log(`${green}+        INVENTORY RECORDER Rev.2       +${reset}`);
  console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);


  //  console.log("Step 1: Collecting system information...");
  const systemInfo = await getSystemInfo();
  
  // Generate dynamic filename using hostname and serial number
  const safeHostname = sanitizeForFilename(systemInfo.hostname);
  const safeSerialNumber = sanitizeForFilename(systemInfo.serialNumber);
  
  // Create the dynamic filename
  const dynamicFilename = `${safeHostname}_${safeSerialNumber}.png`;
  
  // Set the output path (use provided path or create from temp dir + dynamic filename)
  const outputPath = args.output || join(tempDir, dynamicFilename);
  
  //  console.log(`\nStep 2: Generating QR code to ${outputPath}...`);
  const qrSuccess = await generateQRCode(JSON.stringify(systemInfo), outputPath);
  
  if (qrSuccess && args.qr) {
    console.log("\nStep 3: Opening QR code in browser...");
    await openInBrowser(outputPath);
  } else if (qrSuccess) {
    console.log("\nQR code display skipped (use --qr flag to display)");
  }
  
  console.log("\nProcess completed!");
}

// Show usage information if --help is provided
if (args.help) {
  console.log("System Information QR Code Generator");
  console.log("\nUsage:");
  console.log("  deno run --allow-run --allow-env --allow-read --allow-write --allow-net script.ts [options]");
  console.log("\nOptions:");
  console.log("  --qr                 Display QR code in browser (default: false)");
  console.log("  --output=<path>      Specify custom output path for QR code image");
  console.log("                       (default: <temp_dir>/<hostname>_<serialnumber>.png)");
  console.log("  --help               Show this help message");
  Deno.exit(0);
}

// Run the script
await main();