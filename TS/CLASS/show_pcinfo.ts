// Import the SystemInfo class from your module file
// Assuming it's saved as "pc_info_class.ts"
import { SystemInfo } from "./pc_info_class.ts";

async function generateSystemReport() {
  console.log("Generating system report...");
  
  // Create an instance of the SystemInfo class
  const sysInfo = new SystemInfo();
  
  // Gather all system information
  await sysInfo.gatherInfo();
  
  // Option 1: Print all information to console
  sysInfo.printAllInfo();
  
  // Option 2: Get information as an object to use in your application
  const infoData = sysInfo.getAllInfo();
  
  // Example: Save report to a file
  const jsonReport = JSON.stringify(infoData, null, 2);
  await Deno.writeTextFile("system_report.json", jsonReport);
  
  // Example: Check for specific software
  const officeInfo = await sysInfo.getSoftwareInfo("Microsoft Office");
  console.log("\nMicrosoft Office Information:");
  console.log("Name:", officeInfo.displayName);
  console.log("Version:", officeInfo.displayVersion);
  
  // Example: Use specific properties for custom logic
  const systemData = infoData.system;
  if (systemData.manufacturer.includes("Lenovo")) {
    console.log("\nThis is a Dell computer. Running Dell-specific diagnostics...");
    // Run Dell-specific code here
  }
  
  // Example: Check RAM capacity for system requirements
  const ramGB = parseFloat(infoData.ram.totalCapacity);
  if (ramGB < 8) {
    console.log("\nWARNING: System has less than 8GB RAM installed.");
  }
  
  console.log("\nSystem report complete!");
}

// Run the example
await generateSystemReport();