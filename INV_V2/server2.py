from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import sqlite3
from pydantic import BaseModel
from datetime import datetime
import os
from typing import List

app = FastAPI()

db_path = "app.db"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # programs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS programs (
        program_id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_name TEXT NOT NULL UNIQUE,
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
    );
    ''')
    # attendees
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendees (
        attendee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL
    );
    ''')
    # items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL UNIQUE
    );
    ''')
    # items_log
    cursor.execute('''
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
    ''')
    
    conn.commit()
    conn.close()

init_db()


def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Get Programs to Load to Modal
@app.get("/api/programs")
def get_programs():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT program_id, program_name FROM programs WHERE status = 'active'")
    programs = [{"program_id": row[0], "program_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return programs

# Get attendees to Load to Modal
@app.get("/api/attendees")
def get_attendees():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees")
    attendees = [{"attendee_id": row[0], "employee_id": row[1], "full_name": row[2]} for row in cursor.fetchall()]
    conn.close()
    return attendees

# Get items to Load to Modal
@app.get("/api/items")
def get_items():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    items = [{"item_id": row[0], "item_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return items

# items-log API SEARCH ====================================
class ItemLogSearchRequest(BaseModel):
    search_term: str  # The term to search across multiple fields

@app.post("/api/items-log-search", response_model=List[dict])
def search_items_log(request: ItemLogSearchRequest):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    search_query = f"""
        SELECT 
            il.id, il.refnum, p.program_name, i.item_name, il.quantity, il.location, 
            il.reason, il.timestamp, a.full_name AS attendedby, 
            il.program_id, il.item_id, il.attendee_id
        FROM items_log il
        JOIN programs p ON il.program_id = p.program_id
        JOIN items i ON il.item_id = i.item_id
        JOIN attendees a ON il.attendee_id = a.attendee_id
        WHERE 
            p.program_name LIKE ? OR 
            i.item_name LIKE ? OR 
            il.quantity LIKE ? OR 
            il.location LIKE ? OR 
            il.reason LIKE ?
    """
    search_value = f"%{request.search_term}%"
    cursor.execute(search_query, (search_value, search_value, search_value, search_value, search_value))
    
    item_search = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return item_search

# items-log API ====================================

@app.get("/items-log")
def serve_html():
    if os.path.exists("./public/index2.html"):
        return FileResponse("./public/index2.html")
    raise HTTPException(status_code=404, detail="File not found")

# GET ALL items-log record and populate in the Table
@app.get("/api/items-log2")
def get_items_log():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            il.id, il.refnum, p.program_name, i.item_name, il.quantity, il.location, 
            il.reason, il.timestamp, a.full_name AS attendedby, 
            il.program_id, il.item_id, il.attendee_id
        FROM items_log il
        JOIN programs p ON il.program_id = p.program_id
        JOIN items i ON il.item_id = i.item_id
        JOIN attendees a ON il.attendee_id = a.attendee_id
    ''')
    items = [dict(zip(["id", "refnum", "program_name", "item_name", "quantity", "location", "reason", "timestamp", "attendedby", "program_id", "item_id", "attendee_id"], row)) for row in cursor.fetchall()]
    conn.close()
    return items

@app.get("/api/items-log")
def get_items_log():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like access to columns
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            il.id, il.refnum, p.program_name, i.item_name, il.quantity, il.location, 
            il.reason, il.timestamp, a.full_name AS attendedby, 
            il.program_id, il.item_id, il.attendee_id
        FROM items_log il
        JOIN programs p ON il.program_id = p.program_id
        JOIN items i ON il.item_id = i.item_id
        JOIN attendees a ON il.attendee_id = a.attendee_id
    ''')
    
    items = [dict(row) for row in cursor.fetchall()]  # Converts each row to a dictionary
    conn.close()
    
    return items

class ItemLog(BaseModel):
    refnum: str
    program_id: int
    item_id: int
    quantity: int
    location: str
    reason: str
    attendee_id: int

# Save
@app.post("/api/items-log")
def add_item_log(item_log: ItemLog):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    timestamp = format_timestamp()
    cursor.execute(
        "INSERT INTO items_log (refnum, program_id, item_id, quantity, location, reason, timestamp, attendee_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (item_log.refnum, item_log.program_id, item_log.item_id, item_log.quantity, item_log.location, item_log.reason, timestamp, item_log.attendee_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Item logged"}

# Get Row to Edit
@app.get("/api/items-log/{id}")
def get_item_log(id: int):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enables dictionary-like access to columns
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            il.id, il.refnum, p.program_name, i.item_name, il.quantity, il.location, 
            il.reason, il.timestamp, a.full_name AS attendedby, 
            il.program_id, il.item_id, il.attendee_id
        FROM items_log il
        JOIN programs p ON il.program_id = p.program_id
        JOIN items i ON il.item_id = i.item_id
        JOIN attendees a ON il.attendee_id = a.attendee_id
        WHERE il.id = ?
    ''', (id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)  # Converts the single row into a dictionary
    else:
        return {"error": "Item not found"}

# Update/Save
@app.put("/api/items-log/{id}")
def update_item_log(id: int, item_log: ItemLog):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    timestamp = format_timestamp()
    cursor.execute(
        "UPDATE items_log SET refnum = ?, program_id = ?, item_id = ?, quantity = ?, location = ?, reason = ?, timestamp = ?, attendee_id = ? WHERE id = ?",
        (item_log.refnum, item_log.program_id, item_log.item_id, item_log.quantity, item_log.location, item_log.reason, timestamp, item_log.attendee_id, id)
    )
    conn.commit()
    conn.close()
    return {"message": "Item updated"}

# Delete
@app.delete("/api/items-log/{id}")
def delete_item_log(id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items_log WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Item deleted"}

# Run the server using: uvicorn server2:app --reload
