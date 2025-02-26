import { SystemInfo } from "./pc_info_class.ts";


const main = async () => {
  const sysInfo = new SystemInfo();
  await sysInfo.gatherInfo();
  sysInfo.printAllInfo();
  
};

await main();