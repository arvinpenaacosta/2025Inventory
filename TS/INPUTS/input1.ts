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

  // Step 1: Prompt for EID
  let eid: string | null = null;
  while (true) {
    eid = prompt("Enter EID:");
    if (eid && eid.trim() !== "") {
      break;
    }
    console.log("EID is required. Please enter a valid EID.");
  }

  try {
    // Step 2: Load and parse data from data2.json
    const dataText = await Deno.readTextFile("data2.json");
    const data = JSON.parse(dataText);

    // Step 3: List all floors
    console.log("=========================================");
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

    // Step 5: List rooms available on the selected floor
    console.log("=========================================");
    console.log(`Available Rooms for Floor ${selectedFloor.floor}:`);
    let counter = 1;
    const roomMap = new Map<string, any>();

    selectedFloor.rooms.forEach((room: any) => {
      console.log(` ${counter} -> ${room.code} -> ${room.name}`);

      // Store both number and code in the map
      roomMap.set(counter.toString(), room); // Map number selection
      roomMap.set(room.code.toUpperCase(), room); // Map letter selection

      counter++;
    });

    // Step 6: Ask user to select a room by number or code
    let selectedRoom: any = null;
    while (true) {
      console.log("=========================================");
      const selectedRoomCode = prompt("Select a room by entering its number or code:");
      if (!selectedRoomCode) {
        console.log("No room selected. Please try again.");
        continue;
      }

      // Normalize input to uppercase for code-based selection
      selectedRoom = roomMap.get(selectedRoomCode.toUpperCase());

      if (!selectedRoom) {
        console.log("Invalid selection. Please try again.");
        continue;
      }
      break;
    }

    console.log("=========================================");
    console.log(`You selected: ${selectedRoom.name}`);
    console.log("=========================================");

    // Step 7: Process E1 prompt based on its type (object/dictionary or string)
    let e1Answer: string | null = null;
    while (true) {
      if (typeof selectedRoom.E1 === "object") {
        // E1 is a dictionary; use L1 as prompt and list options
        console.log("=========================================X");
        console.log(selectedRoom.L1);
        for (const [key, value] of Object.entries(selectedRoom.E1)) {
          console.log(`  ${key}: ${value}`);
        }
        console.log("=========================================X1");
        e1Answer = prompt(selectedRoom.L1);
        if (!e1Answer || !selectedRoom.E1.hasOwnProperty(e1Answer)) {
          console.log("Invalid selection for E1. Please try again.");
          continue;
        }
      } else if (typeof selectedRoom.E1 === "string") {
        // E1 is a string; use it as the prompt directly
        e1Answer = prompt(selectedRoom.E1);
        if (!e1Answer) {
          console.log("No input provided for E1. Please try again.");
          continue;
        }
      }
      break;
    }

    console.log("=========================================");
    // Step 8: Prompt for E2 using the room's E2 prompt string
    let e2Answer: string | null = null;
    while (true) {
      e2Answer = prompt(selectedRoom.E2);
      if (!e2Answer) {
        console.log("No input provided for E2. Please try again.");
        continue;
      }
      break;
    }

    // Step 9: Combine the inputs into the final output
    // Pattern: "floor D1+E1-E2" (e.g., "11 POD_1-A")

    console.log("=========================================X1");
    const phoneExt = prompt("Enter Citrix Phone Ext (Optional):") || "";

    const finalOutput = `${selectedFloor.floor}  ${selectedRoom.name} ${phoneExt} | ${selectedRoom.D1}${e1Answer}-${e2Answer}`;

    // Step 10: Display the final result
    console.log("++++++++++++++++++++++++++++++++++++++++++");
    console.log("Final Combined Output: " + finalOutput);
 
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

  
main1();