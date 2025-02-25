// Import the SystemInfo class from your module file
// Assuming it's saved as "system_info.ts"
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
  

  
 
  
  console.log("\nSystem report complete!");
}

// Run the example
await generateSystemReport();