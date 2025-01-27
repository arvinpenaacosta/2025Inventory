import { Application, Router } from "https://deno.land/x/oak@v12.6.1/mod.ts";
import { DB } from "https://deno.land/x/sqlite/mod.ts";

// Initialize SQLite database
const db = new DB("app.db");

// Database setup (same as before)
db.query(`
  CREATE TABLE IF NOT EXISTS programs (
    program_id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
  );
`);

// ... (other table creations remain the same)

const router = new Router();

// Helper function to format timestamp
function formatTimestamp() {
  const date = new Date();
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${
    date.getDate().toString().padStart(2, '0')} ${
    date.getHours().toString().padStart(2, '0')}:${
    date.getMinutes().toString().padStart(2, '0')}:${
    date.getSeconds().toString().padStart(2, '0')}`;
}

// Routes
router
  .get("/", async (ctx) => {
    ctx.response.body = await Deno.readFile("./public/index2.html");
    ctx.response.type = "html";
  })
  .get("/api/programs", (ctx) => {
    const programs = [...db.query("SELECT * FROM programs WHERE status = 'active'")]
      .map(([program_id, program_name]) => ({ program_id, program_name }));
    ctx.response.body = programs;
  })
  .get("/api/attendees", (ctx) => {
    const attendees = [...db.query("SELECT * FROM attendees")]
      .map(([attendee_id, employee_id, full_name]) => ({ attendee_id, employee_id, full_name }));
    ctx.response.body = attendees;
  })
  .get("/api/items", (ctx) => {
    const items = [...db.query("SELECT * FROM items")]
      .map(([item_id, item_name]) => ({ item_id, item_name }));
    ctx.response.body = items;
  })
  .get("/api/items-log", (ctx) => {
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
    `)].map(([
      id, refnum, program_name, item_name, quantity, 
      location, reason, timestamp, attendedby, 
      program_id, item_id, attendee_id
    ]) => ({
      id, refnum, program_name, item_name, quantity,
      location, reason, timestamp, attendedby,
      program_id, item_id, attendee_id
    }));
    ctx.response.body = items;
  })
  .post("/api/items-log", async (ctx) => {
    const body = await ctx.request.body().value;
    const timestamp = formatTimestamp();
    
    db.query(
      "INSERT INTO items_log (refnum, program_id, item_id, quantity, location, reason, timestamp, attendee_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
      [body.refnum, body.program_id, body.item_id, body.quantity, 
       body.location, body.reason, timestamp, body.attendee_id]
    );
    ctx.response.status = 201;
    ctx.response.body = { message: "Item logged" };
  })
  .put("/api/items-log/:id", async (ctx) => {
    const id = ctx.params.id;
    const body = await ctx.request.body().value;
    const timestamp = formatTimestamp();
    
    db.query(
      "UPDATE items_log SET refnum = ?, program_id = ?, item_id = ?, quantity = ?, location = ?, reason = ?, timestamp = ?, attendee_id = ? WHERE id = ?",
      [body.refnum, body.program_id, body.item_id, body.quantity,
       body.location, body.reason, timestamp, body.attendee_id, id]
    );
    ctx.response.body = { message: "Item updated" };
  })
  .delete("/api/items-log/:id", (ctx) => {
    const id = ctx.params.id;
    db.query("DELETE FROM items_log WHERE id = ?", [id]);
    ctx.response.body = { message: "Item deleted" };
  });

// Create and configure application
const app = new Application();

// Error handling
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (err) {
    ctx.response.status = 500;
    ctx.response.body = { error: "Internal server error" };
    console.error(err);
  }
});

// Route handling
app.use(router.routes());
app.use(router.allowedMethods());

console.log("Server running on http://localhost:8000");
await app.listen({ port: 8000 });
