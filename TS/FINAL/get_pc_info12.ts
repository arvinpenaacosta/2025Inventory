import QRCode from "https://esm.sh/qrcode@1.5.3";
import { parse } from "https://deno.land/std@0.224.0/flags/mod.ts";
import { join } from "https://deno.land/std@0.224.0/path/mod.ts";

// Get system's temporary folder
const tempDir = Deno.env.get("TMP") || Deno.env.get("TEMP") || "/tmp";
const tempFilePath = join(tempDir, "system_info_qrcode.png");

// Parse command line arguments
const args = parse(Deno.args, {
  string: ["output"],
  default: {
    output: tempFilePath, // Save to temp folder
  },
});

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
  } catch (error) {
    console.error("Error generating QR code:", error);
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
    await new Deno.Command(browserCommands[osType][0], {
      args: browserCommands[osType].slice(1),
    }).output();
  } else {
    console.error("Unsupported OS. Please open the file manually:", imagePath);
  }
}

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
 * Retrieves comprehensive system information and generates a QR code
 */
const getSystemInfoAndGenerateQR = async (): Promise<void> => {
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
  console.log("🔹 PC Information:");
  console.log("Log User:", systemInfo.logUser);
  console.log("Hostname:", systemInfo.hostname);
  console.log("Serial Number:", systemInfo.serialNumber);
  console.log("Processor:", systemInfo.processor);
  console.log("Windows Version:", systemInfo.windowsVersion);
  console.log("Windows Display Version:", systemInfo.windowsDisplayVersion);
  console.log("Manufacturer:", systemInfo.manufacturer);
  console.log("Model:", systemInfo.model);

  console.log("\n🔹 RAM Information:");
  console.log("Total RAM Capacity:", systemInfo.totalRam);
  console.log("Number of RAM Slots:", systemInfo.numRamSlots);
  console.log("RAM Installed per Slot:", systemInfo.ramPerSlot);
  console.log("RAM Speed:", systemInfo.ramSpeed);
  console.log("RAM Type:", systemInfo.ramType);

  console.log("\n🔹 Network Information:");
  console.log("IP Address:", systemInfo.ipAddress);
  console.log("MAC Address:", systemInfo.macAddress);

  console.log("\n🔹 Citrix Information:");
  console.log("Citrix Name:", systemInfo.citrixName);
  console.log("Citrix Version:", systemInfo.citrixVersion);
  console.log("Timestamp:", systemInfo.Timestamp);
  console.log("=================================================");

  // Convert to JSON string for QR code
  const systemInfoJson = JSON.stringify(systemInfo, null, 2);
  console.log(systemInfoJson);
  console.log("=================================================");

  // Generate QR code with the system information
  await generateQRCode(JSON.stringify(systemInfo), args.output);
  
  // Open the QR code in browser
  await openInBrowser(args.output);
};

// Run the script
await getSystemInfoAndGenerateQR();