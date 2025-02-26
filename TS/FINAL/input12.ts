// room-selector.ts
import { parse } from "https://deno.land/std/flags/mod.ts";
import { readLines } from "https://deno.land/std/io/mod.ts";

// Define types for the JSON structure
interface FloorData {
  floors: Floor[];
}

interface Floor {
  floor: string;
  rooms: Room[];
}

interface Room {
  CO: Record<string, string>;
  E1: {
    label: string;
    Range: number[] | string[] | Record<string, string>;
  };
  E2: {
    label: string;
    Range: number[] | string[] | Record<string, string>;
  };
  L1?: string;
  D1: string;
}

// Load the data
async function loadData(): Promise<FloorData> {
  try {
    const jsonData = await Deno.readTextFile("./data3.json");
    return JSON.parse(jsonData);
  } catch (error) {
    console.error("Error loading data3.json:", error.message);
    Deno.exit(1);
  }
}

// Function to get user input
async function getUserInput(prompt: string): Promise<string> {
  console.log(prompt);
  for await (const line of readLines(Deno.stdin)) {
    return line.trim();
  }
  return "";
}

// Main function ====================================================
async function main() {
  const data = await loadData();
  const floorData = data.floors;
  
  console.log("Welcome to Room Selector\n");
  
  // Q1: Select Floor +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  console.log("Q1. Select Floor from the List:");
  
  // Create floor map with index
  const floorMap = new Map<number, string>();
  
  floorData.forEach((floor, index) => {
    const floorNumber = index + 1;
    floorMap.set(floorNumber, floor.floor);
    console.log(`${floorNumber}. Floor ${floor.floor}`);
  });
  
  // Get floor selection
  let selectedFloorIndex: number | null = null;
  let selectedFloor: Floor | null = null;
  
  while (!selectedFloor) {
    const floorInput = await getUserInput("Enter floor number or index:");
    
    // Check if input is an index number
    const floorIndexNumber = parseInt(floorInput);
    if (!isNaN(floorIndexNumber) && floorMap.has(floorIndexNumber)) {
      const floorValue = floorMap.get(floorIndexNumber)!;
      selectedFloor = floorData.find(f => f.floor === floorValue) || null;
      selectedFloorIndex = floorIndexNumber - 1;
    } else {
      // Check if input is a direct floor number (case-insensitive)
      selectedFloor = floorData.find(f => f.floor.toLowerCase() === floorInput.toLowerCase()) || null;
      selectedFloorIndex = floorData.findIndex(f => f.floor.toLowerCase() === floorInput.toLowerCase());
    }
    
    if (!selectedFloor) {
      console.log("Invalid floor selection. Please try again.");
    }
  }
  
  console.log(`\nYou selected Floor ${selectedFloor.floor}\n`);
  
  // Q2: List All CO values for the selected floor with updated format ++++++++++++++++++++++++++
  console.log("Q2. Select Room Type:");
  
  const rooms = selectedFloor.rooms;
  const coMap = new Map<number, { key: string, value: string }>();
  const availableKeys: string[] = [];
  
  rooms.forEach((room, index) => {
    const coNumber = index + 1;
    const coKey = Object.keys(room.CO)[0];
    const coValue = room.CO[coKey];
    coMap.set(coNumber, { key: coKey, value: coValue });
    availableKeys.push(coKey);
    // Updated format: 1 -> [P] Pod
    console.log(`${coNumber} -> [${coKey}] ${coValue}`);
  });
  
  // Get CO selection with dynamic prompt
  let selectedRoom: Room | null = null;
  let selectedCOKey: string | null = null;
  
  // Create a dynamic prompt based on available keys for this floor
  const keyOptions = availableKeys.join(", ");
  const dynamicPrompt = `Enter room type, key (${keyOptions}), or index:`;
  
  while (!selectedRoom) {
    const coInput = await getUserInput(dynamicPrompt);
    
    // Check if input is an index number
    const coIndexNumber = parseInt(coInput);
    if (!isNaN(coIndexNumber) && coMap.has(coIndexNumber)) {
      const { key } = coMap.get(coIndexNumber)!;
      selectedCOKey = key;
      selectedRoom = rooms.find(room => Object.keys(room.CO)[0] === key) || null;
    } else {
      // Check if input is a direct CO key (case-insensitive)
      selectedRoom = rooms.find(room => Object.keys(room.CO)[0].toLowerCase() === coInput.toLowerCase()) || null;
      if (selectedRoom) {
        selectedCOKey = Object.keys(selectedRoom.CO)[0]; // Get the original case
      } else {
        // Check if the input is a CO value (case-insensitive)
        const roomWithValue = rooms.find(room => 
          Object.values(room.CO)[0].toLowerCase() === coInput.toLowerCase()
        );
        if (roomWithValue) {
          selectedRoom = roomWithValue;
          selectedCOKey = Object.keys(roomWithValue.CO)[0];
        }
      }
    }
    
    if (!selectedRoom) {
      console.log("Invalid room type selection. Please try again.");
    }
  }
  
  const roomType = selectedRoom.CO[selectedCOKey!];
  console.log(`\nYou selected ${roomType}\n`);
  
  // Q3: E1 selection based on CO ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  console.log(`Q3x. ${selectedRoom.E1.label}:`);
  
  let e1Value: string | null = null;
  
  // Display options based on the type of Range
  if (Array.isArray(selectedRoom.E1.Range)) {
    selectedRoom.E1.Range.forEach((option, index) => {
      //console.log(`${index + 1}. ${option}`);
    });
    const firstValue = selectedRoom.E1.Range[0]; // First element
    const lastValue = selectedRoom.E1.Range[selectedRoom.E1.Range.length - 1];
    //console.log(`First Value: ${firstValue}`);
    //console.log(`Last Value: ${lastValue}`);

    
    while (e1Value === null) {
      const e1Input = await getUserInput(`q31Enter ${selectedRoom.E1.label.toLowerCase()}:[ ${firstValue} - ${lastValue} ]`);
      
      // Check if input is valid
      const e1IndexNumber = parseInt(e1Input);
      if (!isNaN(e1IndexNumber) && e1IndexNumber >= 1 && e1IndexNumber <= selectedRoom.E1.Range.length) {
        e1Value = String(selectedRoom.E1.Range[e1IndexNumber - 1]);
      } else {
        // Case-insensitive check for string values
        const matchIndex = selectedRoom.E1.Range.findIndex(item => 
          String(item).toLowerCase() === e1Input.toLowerCase()
        );
        if (matchIndex >= 0) {
          e1Value = String(selectedRoom.E1.Range[matchIndex]);
        } else {
          console.log("Invalid input. Please try again.");
        }
      }
    }
  } else if (typeof selectedRoom.E1.Range === 'object' && !Array.isArray(selectedRoom.E1.Range)) {
    // Object Range with key-value pairs
    Object.entries(selectedRoom.E1.Range).forEach(([key, value], index) => {
      console.log(`${index + 1}. ${value} (${key})`);
    });
    
    while (e1Value === null) {
      const e1Input = await getUserInput(`q32Enter ${selectedRoom.E1.label.toLowerCase()}:`);
      
      // Check if input is a key or index
      const e1IndexNumber = parseInt(e1Input);
      
      if (!isNaN(e1IndexNumber) && e1IndexNumber >= 1 && e1IndexNumber <= Object.keys(selectedRoom.E1.Range).length) {
        const key = Object.keys(selectedRoom.E1.Range)[e1IndexNumber - 1];
        e1Value = selectedRoom.E1.Range[key];
      } else {
        // Case-insensitive key check
        const matchingKey = Object.keys(selectedRoom.E1.Range).find(key => 
          key.toLowerCase() === e1Input.toLowerCase()
        );
        if (matchingKey) {
          e1Value = selectedRoom.E1.Range[matchingKey];
        } else {
          // Case-insensitive value check
          const matchingEntry = Object.entries(selectedRoom.E1.Range).find(([_, value]) => 
            String(value).toLowerCase() === e1Input.toLowerCase()
          );
          if (matchingEntry) {
            e1Value = String(matchingEntry[1]);
          } else {
            console.log("Invalid input. Please try again.");
          }
        }
      }
    }
  }
  
  console.log(`\nYou selected ${e1Value} for ${selectedRoom.E1.label}\n`);
  
  // Q4: E2 selection based on CO - Modified for Station Letters
  console.log(`Q4. ${selectedRoom.E2.label}:`);
  
  let e2Value: string | null = null;
  
  // Special handling for station letters
  if (selectedRoom.E2.label === "Enter Station Letter" && 
      Array.isArray(selectedRoom.E2.Range) && 
      typeof selectedRoom.E2.Range[0] === 'string') {
    
    // Just list the letters without numbering
    selectedRoom.E2.Range.forEach((letter) => {
      //console.log(`${letter}`);
    });

    const firstValue = selectedRoom.E2.Range[0]; // First element
    const lastValue = selectedRoom.E2.Range[selectedRoom.E2.Range.length - 1];
    console.log(`First Value: ${firstValue}`);
    console.log(`Last Value: ${lastValue}`);

    
    while (e2Value === null) {
      const e2Input = await getUserInput(`zEnter a station letter : [  ${firstValue} - ${lastValue} ] `);
      
      // Case-insensitive check for station letters
      const matchIndex = selectedRoom.E2.Range.findIndex(letter => 
        String(letter).toLowerCase() === e2Input.toLowerCase()
      );
      
      if (matchIndex >= 0) {
        e2Value = String(selectedRoom.E2.Range[matchIndex]); // Use the original case from the data
      } else {
        console.log("Invalid station letter. Please enter one of the listed letters.");
      }
    }
  } else if (Array.isArray(selectedRoom.E2.Range)) {
    // Regular numbered list for other types
    selectedRoom.E2.Range.forEach((option, index) => {
      //console.log(`${index + 1}. ${option}`);
    });
    const firstValue = selectedRoom.E2.Range[0]; // First element
    const lastValue = selectedRoom.E2.Range[selectedRoom.E2.Range.length - 1];
    console.log(`First Value: ${firstValue}`);
    console.log(`Last Value: ${lastValue}`);

    while (e2Value === null) {
      const e2Input = await getUserInput(`xEnter ${selectedRoom.E2.label.toLowerCase()}: ${firstValue} - ${lastValue}`);
      
      // Check if input is valid
      const e2IndexNumber = parseInt(e2Input);
      if (!isNaN(e2IndexNumber) && e2IndexNumber >= 1 && e2IndexNumber <= selectedRoom.E2.Range.length) {
        e2Value = String(selectedRoom.E2.Range[e2IndexNumber - 1]);
      } else {
        // Case-insensitive check for string values
        const matchIndex = selectedRoom.E2.Range.findIndex(item => 
          String(item).toLowerCase() === e2Input.toLowerCase()
        );
        if (matchIndex >= 0) {
          e2Value = String(selectedRoom.E2.Range[matchIndex]);
        } else {
          console.log("Invalid input. Please try again.");
        }
      }
    }
  } else if (typeof selectedRoom.E2.Range === 'object' && !Array.isArray(selectedRoom.E2.Range)) {
    // Object Range with key-value pairs
    Object.entries(selectedRoom.E2.Range).forEach(([key, value], index) => {
      console.log(`${index + 1}. ${value} (${key})`);
    });
    
    while (e2Value === null) {
      const e2Input = await getUserInput(`Enter ${selectedRoom.E2.label.toLowerCase()}:`);
      
      // Check if input is a key or index
      const e2IndexNumber = parseInt(e2Input);
      
      if (!isNaN(e2IndexNumber) && e2IndexNumber >= 1 && e2IndexNumber <= Object.keys(selectedRoom.E2.Range).length) {
        const key = Object.keys(selectedRoom.E2.Range)[e2IndexNumber - 1];
        e2Value = selectedRoom.E2.Range[key];
      } else {
        // Case-insensitive key check
        const matchingKey = Object.keys(selectedRoom.E2.Range).find(key => 
          key.toLowerCase() === e2Input.toLowerCase()
        );
        if (matchingKey) {
          e2Value = selectedRoom.E2.Range[matchingKey];
        } else {
          // Case-insensitive value check
          const matchingEntry = Object.entries(selectedRoom.E2.Range).find(([_, value]) => 
            String(value).toLowerCase() === e2Input.toLowerCase()
          );
          if (matchingEntry) {
            e2Value = String(matchingEntry[1]);
          } else {
            console.log("Invalid input. Please try again.");
          }
        }
      }
    }
  }
  
  console.log(`\nYou selected ${e2Value} for ${selectedRoom.E2.label}\n`);
  
  // Collect and display all selected values
  console.log("\n===== SELECTION SUMMARY =====");
  console.log(`Floor: ${selectedFloor.floor}`);
  console.log(`Room Type: ${roomType} (${selectedCOKey})`);
  console.log(`${selectedRoom.E1.label}: ${e1Value}`);
  console.log(`${selectedRoom.E2.label}: ${e2Value}`);
  
  // Generate location code
  const locationCode = `${selectedFloor.floor}-${selectedRoom.D1}${e1Value}_${e2Value}`;
  console.log(`\nLocation Code: ${locationCode}`);
}

// Run the main function
if (import.meta.main) {
  main();
}