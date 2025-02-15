# routes/program_routes.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3

import os


router = APIRouter()
DB_FILE = os.getenv("DB_FILE", "db/appFeb12.db")

# Database initialization
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS programs (
        program_id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_name TEXT NOT NULL UNIQUE,
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on module import
init_db()

# Pydantic model for input validation
class ProgramCreate(BaseModel):
    program_name: str = Field(..., min_length=1, description="Name of the program")

class ProgramUpdate(BaseModel):
    program_name: Optional[str] = None
    status: Optional[str] = Field(None, pattern='^(active|inactive)$')


# API Routes
##############################################
@router.get("/programs")
def get_programs():
    print("line 48. programs_routes.py")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM programs")
    
    programs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return programs

# Create a new program #####################
@router.post("/programs")
def create_program(program: ProgramCreate):
    conn = sqlite3.connect(DB_FILE)
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

# Update a program #####################
@router.put("/programs/{program_id}")
def update_program(program_id: int, program: ProgramUpdate):
    print(f"Updating program {program_id} with data:", program.dict())
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # First check if program exists
    cursor.execute("SELECT program_id FROM programs WHERE program_id = ?", (program_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Program not found")

    try:
        # Prepare update query dynamically
        update_fields = []
        params = []

        if program.program_name is not None:
            update_fields.append("program_name = ?")
            params.append(program.program_name)

        if program.status is not None:
            update_fields.append("status = ?")
            params.append(program.status)

        if not update_fields:  # If no fields to update
            conn.close()
            return {"message": "No fields to update"}
        
        # Remove the updated_at field update since it's causing issues
        query = f"UPDATE programs SET {', '.join(update_fields)} WHERE program_id = ?"
        params.append(program_id)

        cursor.execute(query, params)
        
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail="Update failed")
            
        conn.commit()
        conn.close()
        return {"message": "Program updated successfully"}
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail="Program name already exists")
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))




# DELETE a program #####################
@router.delete("/programs/{program_id}")
def delete_program(program_id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM programs WHERE program_id = ?", (program_id,))
    conn.commit()
    conn.close()
    return {"message": "Program deleted"}

