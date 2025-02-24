// Import Deno's readTextFile if needed (built-in in Deno)
// Ensure data2.json is in the same directory as this script

async function main1() {
  console.clear();

  const green: string = "\x1b[32m";
  const reset: string = "\x1b[0m";

  console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);
  console.log(`${green}+                 2 0 2 5               +${reset}`);
  console.log(`${green}+             V I N T O O L S           +${reset}`);
  console.log(`${green}+                                       +${reset}`);
  console.log(`${green}+        INVENTORY RECORDER Rev.2       +${reset}`);
  console.log(`${green}+++++++++++++++++++++++++++++++++++++++++${reset}`);


  // Step 1: Prompt for EID until a valid non-empty input is provided.
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
    console.log(`${green}=========================================${reset}`);
    console.log("Available Floors:");
    data.floors.forEach((floorObj: any) => {
      console.log(`- ${floorObj.floor}`);
    });

    // Step 4: Ask user to select a floor until a valid floor is chosen.
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

    // Step 5: List rooms available on the selected floor.
    console.log(`${green}=========================================${reset}`);
    console.log(`Available Rooms for Floor ${selectedFloor.floor}:`);
    selectedFloor.rooms.forEach((room: any) => {
      console.log(`${room.code} -> ${room.name}`);
    });

    // Step 6: Ask user to select a room by code until a valid room is chosen.
    let selectedRoom: any = null;
    while (true) {
      const selectedRoomCode = prompt("Select a room by entering its code:");
      if (!selectedRoomCode) {
        console.log("No room selected. Please try again.");
        continue;
      }
      // Normalize input to uppercase in case user types in lowercase.
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
    // Step 7: Process E1 prompt based on its type (object/dictionary or string)
    let e1Answer: string | null = null;
    if (typeof selectedRoom.E1 === "object") {
      // E1 is a dictionary; use L1 as prompt and list options with keys and values
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
        // Assign the actual value from the dictionary instead of the key
        e1Answer = selectedRoom.E1[input];
        break;
      }
    } else if (typeof selectedRoom.E1 === "string") {
      // E1 is a string; use it as the prompt directly
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
    // Step 8: Prompt for E2 using the room's E2 prompt string until valid input is provided.
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
    // Step 9: Prompt for Citrix Phone Extension (optional)
    const phoneExt = prompt("Enter Citrix Phone Ext (Optional):") || "";

    // Step 10: Combine the inputs into the final output
    // Pattern: "floor D1+E1-E2" optionally with " ext:phoneExt"
    let finalOutput = `${selectedFloor.floor} ${selectedRoom.D1}${e1Answer}-${e2Answer}`;
    if (phoneExt.trim() !== "") {
      finalOutput += ` ext:${phoneExt}`;
    }

    // Step 11: Display the final result along with detailed information
    console.log(`${green}=========================================${reset}`);
    console.log("Generated Location: " + finalOutput);
    console.log(`${green}=========================================${reset}`);
    console.log("EID: " + eid);
    console.log("Citrix Phone Ext: " + (phoneExt.trim() !== "" ? phoneExt : "None"));
    console.log("Selected Floor: " + selectedFloor.floor);
    console.log("Selected Room: " + selectedRoom.name);
    console.log("E1 Answer: " + e1Answer);
    console.log("E2 Answer: " + e2Answer);
    console.log(`${green}=========================================${reset}`);


    
  } catch (error) {
    console.error("Error reading or parsing data2.json:", error);
  }
}

main1();
