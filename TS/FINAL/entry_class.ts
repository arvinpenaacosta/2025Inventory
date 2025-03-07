import { readJson } from "https://deno.land/x/jsonfile/mod.ts";

export class InventoryRecorder {
  constructor(jsonFile) {
    this.jsonFile = jsonFile;
    this.COLORS = {
      green: "\x1b[32m",
      red: "\x1b[31m",
      yellow: "\x1b[33m",
      blue: "\x1b[34m",
      reset: "\x1b[0m",
    };
  }

  async loadData() {
    this.data = await readJson(this.jsonFile);
  }

  formatRange(numbers) {
    if (numbers.length === 0) return "";
    numbers.sort((a, b) => a - b);
    let ranges = [];
    let start = numbers[0];
    let end = start;

    for (let i = 1; i < numbers.length; i++) {
      if (numbers[i] === end + 1) {
        end = numbers[i];
      } else {
        ranges.push(start === end ? `${start}` : `${start}-${end}`);
        start = numbers[i];
        end = start;
      }
    }
    ranges.push(start === end ? `${start}` : `${start}-${end}`);
    return ranges.join(", ");
  }

  async askQuestion(question, validChoices, applyFormatRange = true) {
    let answer = null;
    const isNumeric = validChoices.every((val) => !isNaN(Number(val)));
    const formattedChoices = isNumeric && applyFormatRange
      ? this.formatRange(validChoices.map(Number))
      : validChoices.join(", ");

    while (!validChoices.includes(answer?.toUpperCase() || "")) {
      console.log(`\n${question}`);
      console.log(`Valid choices: ${formattedChoices}`);
      answer = prompt("Enter your choice: ")?.trim().toUpperCase();
      
      if (!validChoices.includes(answer || "")) {
        console.log("-----------------------------------------");
        console.log(`${this.COLORS.red}❌ ${this.COLORS.reset} Invalid choice. Please try again.`);
        console.log("-----------------------------------------");
      }
    }
    console.log(`${this.COLORS.green}=========================================${this.COLORS.reset}`);
    console.log(`${this.COLORS.green}✅${this.COLORS.reset} You selected: ${this.COLORS.yellow}${answer}${this.COLORS.reset}`);
    console.log(`${this.COLORS.green}=========================================${this.COLORS.reset}`);
    return answer;
  }

  async run() {
    console.clear();
    console.log(`${this.COLORS.green}+++++++++++++++++++++++++++++++++++++++++${this.COLORS.reset}`);
    console.log(`${this.COLORS.green}+        INVENTORY RECORDER Rev.2       +${this.COLORS.reset}`);
    console.log(`${this.COLORS.green}+         Powered by DENO-DevApp        +${this.COLORS.reset}`);
    console.log(`${this.COLORS.green}+++++++++++++++++++++++++++++++++++++++++${this.COLORS.reset}`);

    await this.loadData();
    const floorChoices = this.data.floors.map(floor => floor.floor);
    const selectedFloor = await this.askQuestion("Select a floor:", floorChoices, false);

    const floorData = this.data.floors.find(floor => floor.floor === selectedFloor);
    const roomChoices = Object.fromEntries(
      floorData.rooms.map(room => [Object.keys(room.CO)[0].toUpperCase(), Object.values(room.CO)[0]])
    );

    console.log(`${this.COLORS.yellow}\nLocations :${this.COLORS.reset}`);
    Object.entries(roomChoices).forEach(([key, value]) => console.log(`${key} - ${value}`));
    
    const selectedRoomKey = await this.askQuestion("Select Location key (e.g., P for Pod):", Object.keys(roomChoices));
    const selectedRoomName = roomChoices[selectedRoomKey];
    
    const roomData = floorData.rooms.find(room => Object.keys(room.CO)[0].toUpperCase() === selectedRoomKey);
    const answers = { floor: selectedFloor, room_name: selectedRoomName, D1: roomData.D1, E1: null, E2: null };
    
    if (roomData.E1) {
      const e1Range = roomData.E1.Range;
      console.log(`\n${roomData.E1.label}`);
      let e1Answer;
      if (typeof e1Range === "object" && !Array.isArray(e1Range)) {
        Object.entries(e1Range).forEach(([key, value]) => console.log(`${key} - ${value}`));
        const selectedIndex = await this.askQuestion("Enter index:", Object.keys(e1Range), false);
        e1Answer = e1Range[selectedIndex];
      } else {
        e1Answer = await this.askQuestion(roomData.E1.label, e1Range.map(String));
      }
      answers.E1 = e1Answer;
    }

    if (roomData.E2) {
      const e2Choices = roomData.E2.Range.map(String);
      answers.E2 = await this.askQuestion(roomData.E2.label, e2Choices);
    }

    return answers; // Return answers as an object
  }
}
