// Utility for console colors
const green = "\x1b[32m";
const reset = "\x1b[0m";

// Function to prompt for EID
function getEID(): string | null {
  return prompt("Enter EID:");
}

// Function to prompt for floor selection
function getFloorSelection(data: any): any {
  console.log("=========================================");
  console.log("Available Floors:");
  data.floors.forEach((floorObj: any) => console.log(`- ${floorObj.floor}`));
  console.log("=========================================");

  const selectedFloorInput = prompt("Select a floor from the list above:");
  if (!selectedFloorInput) return null;

  return data.floors.find((f: any) => f.floor === selectedFloorInput) || null;
}

// Function to prompt for room selection
function getRoomSelection(selectedFloor: any): any {
  console.log("=========================================");
  console.log(`Available Rooms for Floor: ${green}${selectedFloor.floor} Floor${reset}`);

  let counter = 1;
  const roomMap = new Map<string, any>();

  selectedFloor.rooms.forEach((room: any) => {
    console.log(` ${counter} -> ${room.code} -> ${room.name}`);
    roomMap.set(counter.toString(), room); // Map number selection
    roomMap.set(room.code.toUpperCase(), room); // Map letter selection
    counter++;
  });

  console.log("=========================================");
  const selectedRoomCode = prompt("Select a room by entering its number or code:");
  if (!selectedRoomCode) return null;

  return roomMap.get(selectedRoomCode.toUpperCase()) || null;
}

// Function to handle E1 selection
function getE1Selection(selectedRoom: any): string | null {
  let e1Answer: string | null = null;

  if (typeof selectedRoom.E1 === "object") {
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

      const selectedValue = selectedRoom.E1[e1Answer];
      if (!selectedValue) {
        console.log("Invalid selection for E1. Try again.");
        continue;
      }

      console.log(`You selected:${green} ${selectedValue} ${reset}`);
      return selectedValue;
    }
  } else if (typeof selectedRoom.E1 === "string") {
    e1Answer = prompt(selectedRoom.E1);
    if (!e1Answer) {
      console.log("No input provided for E1. Exiting.");
      return null;
    }
  }
  return e1Answer;
}

// Function to handle E2 selection
function getE2Selection(selectedRoom: any): string | null {
  return prompt(selectedRoom.E2);
}

// Function to get optional Citrix Phone Extension
function getPhoneExt(): string {
  return prompt("Enter Citrix Phone Ext (Optional):") || "";
}

// Main function
async function main() {
  console.clear();

  const eid = getEID();
  if (!eid) {
    console.log("EID is required. Exiting.");
    return;
  }

  try {
    const dataText = await Deno.readTextFile("data2.json");
    const data = JSON.parse(dataText);

    const selectedFloor = getFloorSelection(data);
    if (!selectedFloor) {
      console.log("Floor not found. Exiting.");
      return;
    }

    const selectedRoom = getRoomSelection(selectedFloor);
    if (!selectedRoom) {
      console.log("Invalid selection. Exiting.");
      return;
    }

    console.log("=========================================");
    console.log(`You selected: ${green}${selectedRoom.name}${reset}`);
    console.log("=========================================");

    const e1Answer = getE1Selection(selectedRoom);
    if (!e1Answer) return;

    console.log("=========================================");
    const e2Answer = getE2Selection(selectedRoom);
    if (!e2Answer) {
      console.log("No input provided for E2. Exiting.");
      return;
    }

    console.log("=========================================X1");
    const phoneExt = getPhoneExt();

    const finalOutput = `${selectedFloor.floor} ${selectedRoom.name} ${phoneExt} | ${selectedRoom.D1}${e1Answer}-${e2Answer}`;

    console.log("++++++++++++++++++++++++++++++++++++++++++");
    console.log("Final Combined Output: " + finalOutput);
  } catch (error) {
    console.error("Error reading or parsing data2.json:", error);
  }
}

main();
