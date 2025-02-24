// Import Deno's readTextFile if needed (built-in in Deno)
// Ensure data2.json is in the same directory as this script

async function main() {

  console.clear();

  const green: string = "\x1b[32m";
  const reset: string = "\x1b[0m";



  // Step 1: Prompt for EID
  const eid = prompt("Enter EID:");
  if (!eid) {
    console.log("EID is required. Exiting.");
    return;
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

    // Step 4: Ask user to select a floor
    console.log("=========================================");
    const selectedFloorInput = prompt("Select a floor from the list above:");
    if (!selectedFloorInput) {
      console.log("No floor selected. Exiting.");
      return;
    }

    const selectedFloor = data.floors.find((f: any) => f.floor === selectedFloorInput);
    if (!selectedFloor) {
      console.log("Floor not found. Exiting.");
      return;
    }

    // Step 5: List rooms available on the selected floor
    console.log("=========================================");
    console.log(`Available Rooms for Floor :${green} ${selectedFloor.floor} Floor ${reset}`);
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
    console.log("=========================================");
    const selectedRoomCode = prompt("Select a room by entering its number or code:");
    if (!selectedRoomCode) {
      console.log("No room selected. Exiting.");
      return;
    }

    // Normalize input to uppercase for code-based selection
    const selectedRoom = roomMap.get(selectedRoomCode.toUpperCase());
    
    if (!selectedRoom) {
      console.log("Invalid selection. Exiting.");
      return;
    }

    console.log("=========================================");
    console.log(`You selected:${green} ${selectedRoom.name} ${reset}`);
    console.log("=========================================");


    // Step 7: Process E1 prompt based on its type (object/dictionary or string)
    let e1Answer: string | null = null;
    if (typeof selectedRoom.E1 === "object") {
      // E1 is a dictionary; use L1 as prompt and list options
      //console.log("=========================================X");
      console.log(selectedRoom.L1);
      for (const [key, value] of Object.entries(selectedRoom.E1)) {
        console.log(`  ${key} -> ${value}`);
      }

      console.log("=========================================X1");
      while (true) {
        e1Answer = prompt(selectedRoom.L1);
        
        if (!e1Answer) {
          console.log("No selection made. Please try again.");
          continue;
        }

        // Retrieve the value instead of the key
        const selectedValue = selectedRoom.E1[e1Answer];
        
        if (!selectedValue) {
          console.log("Invalid selection for E1. Try again.");
          continue;
        }

        e1Answer = selectedValue; // Store the value instead of the key
        console.log(`You selected:${green} ${selectedValue} ${reset}`);
        break;
      }

    } else if (typeof selectedRoom.E1 === "string") {
      // E1 is a string; use it as the prompt directly
      e1Answer = prompt(selectedRoom.E1);
      if (!e1Answer) {
        console.log("No input provided for E1. Exiting.");
        return;
      }
    }

    console.log("=========================================");
    // Step 8: Prompt for E2 using the room's E2 prompt string
    const e2Answer = prompt(selectedRoom.E2);
    if (!e2Answer) {
      console.log("No input provided for E2. Exiting.");
      return;
    }

    // Step 9: Combine the inputs into the final output
    // Pattern: "floor D1+E1-E2" (e.g., "11 POD_1-A")
    
    console.log("=========================================X1");
    const phoneExt = prompt("Enter Citrix Phone Ext (Optional):") || "";

    const finalOutput = `${selectedFloor.floor}  ${selectedRoom.name} ${phoneExt} | ${selectedRoom.D1}${e1Answer}-${e2Answer}`;


    // Step 10: Display the final result
    console.log("++++++++++++++++++++++++++++++++++++++++++");
    console.log("Final Combined Output: " + finalOutput);
  } catch (error) {
    console.error("Error reading or parsing data2.json:", error);
  }
}

main();
