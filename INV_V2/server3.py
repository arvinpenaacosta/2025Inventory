from fastapi import FastAPI, HTTPException, Request 

from fastapi.responses import FileResponse
import sqlite3
from pydantic import BaseModel
from datetime import datetime
import os
from typing import List

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"))

# Initialize templates
templates = Jinja2Templates(directory="templates")

db_path = "app.db"

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS programs (
        program_id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_name TEXT NOT NULL UNIQUE,
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendees (
        attendee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL UNIQUE,
        full_name TEXT NOT NULL
    );
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL UNIQUE
    );
    ''')
    
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


@app.get("/api/programs")
def get_programs():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT program_id, program_name FROM programs WHERE status = 'active'")
    programs = [{"program_id": row[0], "program_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return programs

@app.get("/api/attendees")
def get_attendees():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees")
    attendees = [{"attendee_id": row[0], "employee_id": row[1], "full_name": row[2]} for row in cursor.fetchall()]
    conn.close()
    return attendees

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
async def items_log(request: Request):
    return templates.TemplateResponse("index2d.html", {"request": request})


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


# GET ALL items-log record and populate in the  Table
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

@app.delete("/api/items-log/{id}")
def delete_item_log(id: int):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items_log WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Item deleted"}


# Modified items-log route to use templates
@app.get("/items-log")
async def items_log(request: Request):
    return templates.TemplateResponse("items_log.html", {"request": request})

# [Rest of your existing code including the SSL configuration and main block]

cert_dir = os.path.join(os.path.dirname(__file__), "certs")
ssl_keyfile = os.path.join(cert_dir, "server_unencrypted.key")
ssl_certfile = os.path.join(cert_dir, "server.crt")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8851, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)


# Run the server using: uvicorn filename:app --reload
# uvicorn main_jwt:app --host 0.0.0.0.0 --port 8851 --reload --ssl-keyfile=certs/server_unencrypted.key --ssl-certfile=certs/server.crt


# uvicorn server3:app --host 0.0.0.0.0 --port 8821 --reload --ssl-keyfile=certs/server_unencrypted.key --ssl-certfile=certs/server.crt 
# https://127.0.0.1:8821/items-log
