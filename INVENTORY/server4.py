from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
from typing import Optional, List
import uvicorn

# Pydantic model for input validation
class ProgramCreate(BaseModel):
    program_name: str = Field(..., min_length=1, description="Name of the program")

class ProgramUpdate(BaseModel):
    program_name: Optional[str] = None
    status: Optional[str] = Field(None, pattern='^(active|inactive)$')

# FastAPI app setup
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('app4.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS programs (
            program_id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_name TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.close()

# Initialize DB on startup
init_db()

# Static HTML route
@app.get("/apifm_programs", response_class=HTMLResponse)
async def serve_html():
    with open('./public/index4.html', 'r') as file:
        return HTMLResponse(content=file.read())

# Get all programs
@app.get("/apifm/programs", response_model=List[dict])
def get_programs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM programs")
        programs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return programs
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch programs")

# Create a new program
@app.post("/apifm/programs", status_code=201)
def create_program(program: ProgramCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO programs (program_name) VALUES (?)", 
            (program.program_name,)
        )
        conn.commit()
        program_id = cursor.lastrowid
        conn.close()
        return {
            "program_id": program_id, 
            "message": "Program created successfully"
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Program name already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create program")

# Update a program
@app.put("/apifm/programs/{program_id}")
def update_program(program_id: int, program: ProgramUpdate):
    try:
        # Validate input
        if not program.program_name and not program.status:
            raise HTTPException(status_code=400, detail="Nothing to update")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Prepare update query dynamically
        update_fields = []
        params = []

        if program.program_name:
            update_fields.append("program_name = ?")
            params.append(program.program_name)

        if program.status:
            update_fields.append("status = ?")
            params.append(program.status)

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(program_id)

        # Construct and execute query
        query = f"UPDATE programs SET {', '.join(update_fields)} WHERE program_id = ?"
        cursor.execute(query, params)
        conn.commit()

        # Check if any rows were updated
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Program not found")

        conn.close()
        return {"message": "Program updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update program")

# Delete (soft delete) a program
@app.delete("/apifm/programs/{program_id}")
def delete_program(program_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE programs SET status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE program_id = ?", 
            (program_id,)
        )
        conn.commit()

        # Check if any rows were updated
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Program not found")

        conn.close()
        return {"message": "Program deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete program")

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)