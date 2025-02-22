import { serve } from "https://deno.land/std@0.203.0/http/server.ts";
import { DB } from "https://deno.land/x/sqlite/mod.ts";

// Initialize SQLite database
const db = new DB("webInfo.db");

// Create table if not exists
db.query(`
  CREATE TABLE IF NOT EXISTS webinfo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
  );
`);

async function parseFormData(req: Request): Promise<Record<string, string>> {
  const body = new URLSearchParams(await req.text());
  return Object.fromEntries(body.entries());
}

async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);

  if (url.pathname === "/go" && req.method === "POST") {
    const { name } = await parseFormData(req);

    if (!name) {
      return new Response("Name is required", { status: 400 });
    }

    db.query("INSERT INTO webinfo (name) VALUES (?)", [name]);

    // Ask user confirmation for reboot
    const userChoice = prompt("Do you want to reboot the system? (yes/no):")?.toLowerCase();

    if (userChoice === "yes") {
      console.log("Rebooting system...");
      /*setTimeout(async () => {
        const rebootCmd = new Deno.Command("shutdown", { args: ["-r", "-t", "0"] });
        await rebootCmd.spawn().status();
      }, 1000);*/
    } else {
      console.log("Server is stopping without reboot...");
      setTimeout(() => Deno.exit(0), 1000);
    }

    return new Response(`<h2>Data submitted successfully! Server is stopping...</h2>`, {
      status: 201,
      headers: { "Content-Type": "text/html" },
    });
  }

  return new Response("Not Found", { status: 404 });
}

console.log("Server running on http://localhost:8000");
serve(handler, { port: 8000 });
