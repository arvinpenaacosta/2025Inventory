import { readLines } from "https://deno.land/std/io/mod.ts";

// Set Color Effects
const COLORS = {
  green: "\x1b[32m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  reset: "\x1b[0m",
};

// Define types for JSON structure
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

// Load JSON Data
async function loadData(): Promise<FloorData> {
  try {
    const jsonData = await Deno.readTextFile("./data3.json");
    return JSON.parse(jsonData);
  } catch (error) {
    console.error("Error loading data3.json:", error.message);
    Deno.exit(1);
  }
}

// Function to clear the current input line and reprint the prompt (like Clipper)
function clearInputLine(row: number, col: number) {
  Deno.stdout.writeSync(new TextEncoder().encode(`\x1b[${row};${col}H\x1b[K`)); // Moves cursor & clears line
}

// Function to get validated user input (Keeps cursor on same line)
async function getValidatedInput(row: number, col: number, prompt: string, validOptions: string[]): Promise<string> {
  let selection: string | null = null;

  while (!selection || !validOptions.includes(selection.toUpperCase())) {
    clearInputLine(row, col);
    Deno.stdout.writeSync(new TextEncoder().encode(`\x1b[${row};${col}H${COLORS.blue}${prompt}${COLORS.reset} [${validOptions.join(", ")}]: `));

    for await (const line of readLines(Deno.stdin)) {
      selection = line.trim().toUpperCase(); // Convert input to uppercase
      break;
    }

    if (!validOptions.includes(selection)) {
      clearInputLine(row, col);
      Deno.stdout.writeSync(new TextEncoder().encode(`\x1b[${row};${col}H${COLORS.red}Invalid input! Try again.${COLORS.reset}`));
      selection = null;
    }
  }

  return selection;
}

// Function to select a floor
async function selectFloor(floorData: Floor[]): Promise<Floor> {
  const floorOptions = floorData.map(floor => floor.floor);
  const selectedFloorNumber = await getValidatedInput(5, 5, "Select Floor:", floorOptions);
  return floorData.find(f => f.floor === selectedFloorNumber)!;
}

// Function to select a room
async function selectRoom(selectedFloor: Floor): Promise<Room> {
  const rooms = selectedFloor.rooms;
  const coOptions = rooms.map(room => Object.keys(room.CO)[0]);
  const selectedCOKey = await getValidatedInput(10, 5, "Select Room Type:", coOptions);
  return rooms.find(room => Object.keys(room.CO)[0] === selectedCOKey)!;
}

// Function to select E1 (First Question)
async function selectE1(room: Room): Promise<string> {
  const e1Options = Array.isArray(room.E1.Range)
    ? room.E1.Range.map(String)
    : Object.keys(room.E1.Range || {});

  return await getValidatedInput(15, 5, room.E1.label, e1Options);
}

// Function to select E2 (Second Question)
async function selectE2(room: Room): Promise<string> {
  const e2Options = Array.isArray(room.E2.Range)
    ? room.E2.Range.map(String)
    : Object.keys(room.E2.Range || {});

  return await getValidatedInput(20, 5, room.E2.label, e2Options);
}

// Main function
async function main() {
  const data = await loadData();
  const floorData = data.floors;

  console.clear();
  console.log("Welcome to Room Selector\n");

  // Step 1: Select Floor
  const selectedFloor = await selectFloor(floorData);

  // Step 2: Select Room
  const selectedRoom = await selectRoom(selectedFloor);

  // Step 3: Handle E1 & E2 Questions Separately
  const selectedE1 = await selectE1(selectedRoom);
  const selectedE2 = await selectE2(selectedRoom);

  // Final Summary
  console.log("\n\x1b[32m===== SELECTION SUMMARY =====\x1b[0m");
  console.log(`Floor: ${selectedFloor.floor}`);
  console.log(`Room Type: ${selectedRoom.CO[Object.keys(selectedRoom.CO)[0]]}`);
  console.log(`${selectedRoom.E1.label}: ${selectedE1}`);
  console.log(`${selectedRoom.E2.label}: ${selectedE2}`);
  console.log("\n\x1b[32mSelection Complete!\x1b[0m");
}

// Run the main function
if (import.meta.main) {
  main();
}
