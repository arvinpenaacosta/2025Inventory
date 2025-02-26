// Import the SystemInfo class from your module file
// Assuming it's saved as "pc_info_class.ts"
import { SystemInfo } from "./pc_info_class.ts";

async function displayHostnameAndSerial() {
  // Create an instance of the SystemInfo class
  const sysInfo = new SystemInfo();
  
  // Gather all system information
  await sysInfo.gatherInfo();
  
  // Get all info as an object
  const infoData = sysInfo.getAllInfo();
  
  // Extract just the hostname and serial number
  const username = infoData.system.username;
  const hostname = infoData.system.hostname;
  const serialNumber = infoData.system.serialNumber;
  
  // Display these values to the console
  console.log("Computer Hostname:", username);
  console.log("Computer Hostname:", hostname);
  console.log("Serial Number:", serialNumber);
}

// Run the function
await displayHostnameAndSerial();
