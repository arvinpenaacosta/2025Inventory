import { serve } from "https://deno.land/std@0.203.0/http/server.ts";
import { DB } from "https://deno.land/x/sqlite/mod.ts";

// Initialize SQLite database
const db = new DB("app.db");

// Create tables if they don't exist
db.query(`
  CREATE TABLE IF NOT EXISTS programs (
    program_id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
  );
`);

db.query(`
  CREATE TABLE IF NOT EXISTS attendees (
    attendee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL
  );
`);

db.query(`
  CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_name TEXT NOT NULL UNIQUE
  );
`);

// Create main items_log table with foreign keys
db.query(`
  CREATE TABLE IF NOT EXISTS items_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    refnum TEXT NOT NULL,
    program_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    location TEXT NOT NULL,
    reason TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    attendee_id INTEGER NOT NULL,
    FOREIGN KEY (program_id) REFERENCES programs(program_id),
    FOREIGN KEY (item_id) REFERENCES items(item_id),
    FOREIGN KEY (attendee_id) REFERENCES attendees(attendee_id)
  );
`);

async function parseJSON(req: Request): Promise<any> {
  const text = await req.text();
  return JSON.parse(text || "{}");
}

async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  
  if (url.pathname === "/" && req.method === "GET") {
    const file = await Deno.readFile("./public/index2.html");
    return new Response(file, { headers: { "Content-Type": "text/html" } });
  }

  // Get all programs
  if (url.pathname === "/api/programs" && req.method === "GET") {
    const programs = [...db.query("SELECT * FROM programs WHERE status = 'active'")].map(
      ([program_id, program_name]) => ({ program_id, program_name })
    );
    return Response.json(programs);
  }

  // Get all attendees
  if (url.pathname === "/api/attendees" && req.method === "GET") {
    const attendees = [...db.query("SELECT * FROM attendees")].map(
      ([attendee_id, employee_id, full_name]) => ({ attendee_id, employee_id, full_name })
    );
    return Response.json(attendees);
  }

  // Get all items
  if (url.pathname === "/api/items" && req.method === "GET") {
    const items = [...db.query("SELECT * FROM items")].map(
      ([item_id, item_name]) => ({ item_id, item_name })
    );
    return Response.json(items);
  }


  // Get all items log with joined data
  if (url.pathname === "/api/items-log" && req.method === "GET") {
    const items = [...db.query(`
      SELECT 
        il.id, 
        il.refnum, 
        p.program_name,
        i.item_name,
        il.quantity,
        il.location,
        il.reason,
        il.timestamp,
        a.full_name as attendedby,
        il.program_id,
        il.item_id,
        il.attendee_id
      FROM items_log il
      JOIN programs p ON il.program_id = p.program_id
      JOIN items i ON il.item_id = i.item_id
      JOIN attendees a ON il.attendee_id = a.attendee_id
    `)].map(([id, refnum, program_name, item_name, quantity, location, reason, timestamp, attendedby, program_id, item_id, attendee_id]) => ({
      id,
      refnum,
      program_name,
      item_name,
      quantity,
      location,
      reason,
      timestamp,
      attendedby,
      program_id,
      item_id,
      attendee_id
    }));
    return Response.json(items);
  }

function formatTimestamp() {
  const date = new Date();
  
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0'); // Add 1 because months are zero-indexed
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  const seconds = String(date.getSeconds()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

  // Add new item log
  if (url.pathname === "/api/items-log" && req.method === "POST") {
    const formattedTimestamp = formatTimestamp();
    const timestamp = formattedTimestamp  //new Date().toISOString();

    const { refnum, program_id, item_id, quantity, location, reason, attendee_id } = await parseJSON(req);
    
    db.query(
      "INSERT INTO items_log (refnum, program_id, item_id, quantity, location, reason, timestamp, attendee_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
      [refnum, program_id, item_id, quantity, location, reason, timestamp, attendee_id]
    );
    return new Response("Item logged", { status: 201 });
  }

  // Update item log
  if (url.pathname.startsWith("/api/items-log/") && req.method === "PUT") {
    const formattedTimestamp = formatTimestamp();
    const timestamp = formattedTimestamp  //new Date().toISOString();

    const id = parseInt(url.pathname.split("/").pop() || "");
    const { refnum, program_id, item_id, quantity, location, reason, attendee_id } = await parseJSON(req);
    
    
    db.query(
      "UPDATE items_log SET refnum = ?, program_id = ?, item_id = ?, quantity = ?, location = ?, reason = ?, timestamp = ?, attendee_id = ? WHERE id = ?",
      [refnum, program_id, item_id, quantity, location, reason, timestamp, attendee_id, id]
    );
    return new Response("Item updated", { status: 200 });
  }

  // Delete item log
  if (url.pathname.startsWith("/api/items-log/") && req.method === "DELETE") {
    const id = parseInt(url.pathname.split("/").pop() || "");
    db.query("DELETE FROM items_log WHERE id = ?", [id]);
    return new Response("Item deleted", { status: 200 });
  }

  return new Response("Not Found", { status: 404 });
}

console.log("Server running on http://localhost:8000");
serve(handler, { port: 8000 });


// deno run -RWNE server2.ts