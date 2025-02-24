// Import Deno's readTextFile if needed (built-in in Deno)

interface InventoryRecord {
  eid: string;
  phoneExt: string;
  floor: string;
  roomName: string;
  e1Answer: string;
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

  let eid: string | null = null;
  while (true) {
    eid = prompt("Enter EID:");
    if (eid && eid.trim() !== "") {
      break;
    }
    console.log("EID is required. Please enter a valid EID.");
  }

  try {
    const dataText = await Deno.readTextFile("data2.json");
    const data = JSON.parse(dataText);

    console.log(`${green}=========================================${reset}`);
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

    console.log(`${green}=========================================${reset}`);
    console.log(`Available Rooms for Floor ${selectedFloor.floor}:`);
    selectedFloor.rooms.forEach((room: any) => {
      console.log(`${room.code} -> ${room.name}`);
    });

    let selectedRoom: any = null;
    while (true) {
      const selectedRoomCode = prompt("Select a room by entering its code:");
      if (!selectedRoomCode) {
        console.log("No room selected. Please try again.");
        continue;
      }
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
    let e1Answer: string | null = null;
    if (typeof selectedRoom.E1 === "object") {
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
        e1Answer = selectedRoom.E1[input];
        break;
      }
    } else if (typeof selectedRoom.E1 === "string") {
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
    const phoneExt = prompt("Enter Citrix Phone Ext (Optional):") || "";

    let finalOutput = `${selectedFloor.floor} ${selectedRoom.D1}${e1Answer}-${e2Answer}`;
    if (phoneExt.trim() !== "") {
      finalOutput += ` ext:${phoneExt}`;
    }

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

// Example usage:
async function run() {
  const result = await main1();
  if (result) {
    // Now you can access all the values outside main1()
    console.log("Access values outside main1():");
    console.log("EID:", result.eid);
    console.log("Phone Extension:", result.phoneExt);
    console.log("Floor:", result.floor);
    console.log("Room Name:", result.roomName);
    console.log("E1 Answer:", result.e1Answer);
    console.log("E2 Answer:", result.e2Answer);
    console.log("Final Output:", result.finalOutput);
  }
}

run();

