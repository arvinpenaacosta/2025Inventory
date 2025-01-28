import { serve } from "https://deno.land/std@0.203.0/http/server.ts";
import { DB } from "https://deno.land/x/sqlite/mod.ts";

// Type definitions for better type safety
interface Program {
  program_id?: number;
  program_name: string;
  status?: 'active' | 'inactive';
}

// Initialize SQLite database
const db = new DB("./db/app4.db");

// Create tables with better constraints
db.query(`
  CREATE TABLE IF NOT EXISTS programs (
    program_id INTEGER PRIMARY KEY AUTOINCREMENT,
    program_name TEXT NOT NULL UNIQUE,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );
`);

// Helper functions
async function parseJSON(req: Request): Promise<any> {
  try {
    const text = await req.text();
    return JSON.parse(text || "{}");
  } catch (error) {
    throw new Error(`Invalid JSON: ${error.message}`);
  }
}

function createResponse(data: any, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

// Request handlers
async function getPrograms(): Promise<Response> {
  try {
    const programs = [...db.query("SELECT * FROM programs ")].map(
      ([program_id, program_name, status]) => ({ program_id, program_name, status })
    );
    return createResponse(programs);
  } catch (error) {
    return createResponse({ error: "Failed to fetch programs" }, 500);
  }
}

async function createProgram(req: Request): Promise<Response> {
  try {
    const { program_name } = await parseJSON(req);
    
    if (!program_name) {
      return createResponse({ error: "program_name is required" }, 400);
    }

    const result = db.query(
      "INSERT INTO programs (program_name) VALUES (?) RETURNING program_id",
      [program_name]
    );
    
    const [program_id] = [...result][0];
    return createResponse({ program_id, message: "Program created successfully" }, 201);
  } catch (error) {
    if (error.message.includes("UNIQUE constraint failed")) {
      return createResponse({ error: "Program name already exists" }, 409);
    }
    return createResponse({ error: "Failed to create program" }, 500);
  }
}

async function updateProgram(id: number, req: Request): Promise<Response> {
  try {
    const { program_name, status } = await parseJSON(req);
    
    if (!program_name && !status) {
      return createResponse({ error: "Nothing to update" }, 400);
    }

    const updateFields = [];
    const params = [];
    
    if (program_name) {
      updateFields.push("program_name = ?");
      params.push(program_name);
    }
    
    if (status) {
      updateFields.push("status = ?");
      params.push(status);
    }
    
    updateFields.push("updated_at = CURRENT_TIMESTAMP");
    params.push(id);

    const query = `
      UPDATE programs 
      SET ${updateFields.join(", ")} 
      WHERE program_id = ?
    `;
    
    const result = db.query(query, params);
    
    if (result.changes === 0) {
      return createResponse({ error: "Program not found" }, 404);
    }
    
    return createResponse({ message: "Program updated successfully" });
  } catch (error) {
    return createResponse({ error: "Failed to update program" }, 500);
  }
}

async function deleteProgram(id: number): Promise<Response> {
  try {
    const result = db.query(
      "UPDATE programs SET status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE program_id = ?",
      [id]
    );
    
    if (result.changes === 0) {
      return createResponse({ error: "Program not found" }, 404);
    }
    
    return createResponse({ message: "Program deleted successfully" });
  } catch (error) {
    return createResponse({ error: "Failed to delete program" }, 500);
  }
}

// Main request handler
async function handler(req: Request): Promise<Response> {
  try {
    const url = new URL(req.url);
    
    // Handle CORS preflight requests
    if (req.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    if (url.pathname === "/apifm_programs" && req.method === "GET") {
      const file = await Deno.readFile("./public/index4.html");
      return new Response(file, { 
        headers: { "Content-Type": "text/html" }
      });
    }

    if (url.pathname === "/apifm/programs") {
      switch (req.method) {
        case "GET":
          return getPrograms();
        case "POST":
          return createProgram(req);
        default:
          return createResponse({ error: "Method not allowed" }, 405);
      }
    }

    if (url.pathname.startsWith("/apifm/programs/")) {
      const id = parseInt(url.pathname.split("/").pop() || "");
      
      if (isNaN(id)) {
        return createResponse({ error: "Invalid program ID" }, 400);
      }

      switch (req.method) {
        case "PUT":
          return updateProgram(id, req);
        case "DELETE":
          return deleteProgram(id);
        default:
          return createResponse({ error: "Method not allowed" }, 405);
      }
    }

    return createResponse({ error: "Not found" }, 404);
  } catch (error) {
    return createResponse({ error: "Internal server error" }, 500);
  }
}

// Start server
const port = 8000;
console.log(`Server running on http://localhost:${port}`);
serve(handler, { port });


// deno run -RWNE server4.ts
// http://localhost:8000/apifm_programs
