import { serve } from "https://deno.land/std@0.203.0/http/server.ts";
import { DB } from "https://deno.land/x/sqlite/mod.ts";

// Initialize SQLite database
//const db = new DB("webInfo.db");
const db = new DB("\\\\ltop8672\\devshared\\DENO\\webInfo2.db");


// Create table if not exists
db.query(`
  CREATE TABLE IF NOT EXISTS webinfo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    location_code TEXT NOT NULL,
    floor TEXT NOT NULL,
    room_prefix TEXT NOT NULL,
    room_name TEXT NOT NULL,
    e1_value TEXT NOT NULL,
    e2_valueTEXT NOT NULL

  );
`);




/*
async function parseFormData(req: Request): Promise<Record<string, string>> {
  const body = new URLSearchParams(await req.text());
  return Object.fromEntries(body.entries());
}
*/



async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);




  if (url.pathname === "/go" && req.method === "POST") {

    const { 
      locationCode, 
      selectedFloor, 
      roomPrefix, 
      roomSelected, 
      e1Value, 
      e2Value 
    } = await parseFormData(req);


    if (!locationCode || !selectedFloor || !roomPrefix || !roomSelected) {
      return new Response("Required location fields are missing", { 
        status: 400 
      });
    }


    // Insert into database
    const query = `
      INSERT INTO webinfo (
        location_code,
        floor,
        room_prefix,
        room_name,
        e1_value,
        e2_value

      ) VALUES (?, ?, ?, ?, ?, ?)
    `;

    const values = [
      locationCode,    // Full location code
      selectedFloor,   // Floor number
      roomPrefix,      // Room prefix (D1)
      roomSelected,    // Room name
      e1Value,         // E1 value
      e2Value          // E2 value
    ];

    await db.query(query, values);
    // Ask user confirmation for reboot

    return new Response( `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reboot Confirmation</title>
            <style>
                  body { display: flex; justify-content: center; align-items: flex-start; height: 100vh; background-color: #f4f4f4; font-family: Arial, sans-serif; margin: 0; padding-top: 100px; }  
                .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); text-align: center; }  
                h2 { margin-bottom: 20px; }  
                .btn { display: inline-block; padding: 10px 20px; margin: 10px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; transition: 0.3s; }  
                .btn-yes { background-color: #28a745; color: white; }  
                .btn-yes:hover { background-color: #218838; }  
                .btn-no { background-color: #dc3545; color: white; }  
                .btn-no:hover { background-color: #c82333; } 
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Do you want to Reboot the PC?</h2>
                <form method="POST" action="http://127.0.0.1:8000/yesreboot">
                    <button type="submit" class="btn btn-yes">Yes</button>
                </form>
                <form method="POST" action="http://127.0.0.1:8000/noreboot">
                    <button type="submit" class="btn btn-no">No</button>
                </form>
            </div>
        </body>
        </html>
      `,
      {
      status: 201,
      headers: { "Content-Type": "text/html" },
    });
  }

  if (url.pathname === "/yesreboot" && req.method === "POST") {
    console.log("Rebooting system...");

    setTimeout(async () => {
      console.log("Rebooting system...");
      //const rebootCmd = new Deno.Command("shutdown", { args: ["-r", "-t", "0"] });
      //await rebootCmd.spawn().status();
      console.log("Rebooting system...2");
    }, 1000);

    return new Response("<h2>System is rebooting...</h2>", {
      status: 200,
      headers: { "Content-Type": "text/html" },
    });
  }

  if (url.pathname === "/noreboot" && req.method === "POST") {
    console.log("Server is stopping without reboot...");
    const command = new Deno.Command("cmd", { args: ["/c", "cls"], stdout: "inherit", stderr: "inherit" });
    await command.output();

    setTimeout(() => Deno.exit(0), 1000);

    return new Response("<h2>Server is shutting down...</h2>", {
      status: 200,
      headers: { "Content-Type": "text/html" },
    });
  }





  return new Response("Not Found", { status: 404 });
}



//========================================= OPEN HTML

// Read the external HTML file.
const htmlFile ="entry2B.html"; // Your external HTML file.
const htmlContent = await Deno.readTextFile(htmlFile);

// Create a temporary directory.
const tempDir = await Deno.makeTempDir();

// Define the paths for the HTML file and data2.js in the temporary directory.
const tempHtmlPath = `${tempDir}/entry2B.html`;
const tempDataPath = `${tempDir}/data2.js`;

// Write the HTML content to the temporary HTML file.
await Deno.writeTextFile(tempHtmlPath, htmlContent);

// Copy data2.js to the temporary directory.
await Deno.copyFile("data2.js", tempDataPath);

// Open the HTML file in the default browser.
const fileUrl = `file://${tempHtmlPath}`;
await new Deno.Command("cmd", { args: ["/c", "start", fileUrl] }).output(); // For Windows
// await new Deno.Command("open", { args: [fileUrl] }).output(); // For macOS
// await new Deno.Command("xdg-open", { args: [fileUrl] }).output(); // For Linux

console.log(`Opened in browser: ${fileUrl}`);
//========================================= OPEN HTML


console.log("Server running on http://localhost:8000");
serve(handler, { port: 8000 });