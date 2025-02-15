# routes/item-log_routes.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List
import sqlite3
from datetime import datetime
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
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT NOT NULL UNIQUE,
        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
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
        attendee TEXT NOT NULL,
        FOREIGN KEY (program_id) REFERENCES programs(program_id),
        FOREIGN KEY (item_id) REFERENCES items(item_id)
    );
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on module import
init_db()

# Pydantic models
class ItemLog(BaseModel):
    refnum: str
    program_id: int
    item_id: int
    quantity: int
    location: str
    reason: str
    attendee: str

class ItemLogSearchRequest(BaseModel):
    search_term: str

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# API Routes
@router.get("/programs")
def get_programs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT program_id, program_name FROM programs WHERE status = 'active'")
    programs = [{"program_id": row[0], "program_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return programs

@router.get("/items")
def get_items():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    items = [{"item_id": row[0], "item_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return items

@router.get("/items-log")
def get_items_log():
    print("line 93. item_routes.py")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            il.id, il.refnum, p.program_name, i.item_name, il.quantity, il.location, 
            il.reason, il.timestamp, il.attendee, 
            il.program_id, il.item_id
        FROM items_log il
        JOIN programs p ON il.program_id = p.program_id
        JOIN items i ON il.item_id = i.item_id
    ''')
    
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return items

@router.post("/items-log")
def add_item_log(item_log: ItemLog):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = format_timestamp()
    cursor.execute(
        "INSERT INTO items_log (refnum, program_id, item_id, quantity, location, reason, timestamp, attendee) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (item_log.refnum, item_log.program_id, item_log.item_id, item_log.quantity, item_log.location, item_log.reason, timestamp, item_log.attendee)
    )
    conn.commit()
    conn.close()
    return {"message": "Item logged"}

@router.put("/items-log/{id}")
def update_item_log(id: int, item_log: ItemLog):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = format_timestamp()
    cursor.execute(
        "UPDATE items_log SET refnum = ?, program_id = ?, item_id = ?, quantity = ?, location = ?, reason = ?, timestamp = ?, attendee = ? WHERE id = ?",
        (item_log.refnum, item_log.program_id, item_log.item_id, item_log.quantity, item_log.location, item_log.reason, timestamp, item_log.attendee, id)
    )
    conn.commit()
    conn.close()
    return {"message": "Item updated"}

@router.delete("/items-log/{id}")
def delete_item_log(id: int):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items_log WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"message": "Item deleted"}

@router.post("/items-log-search", response_model=List[dict])
def search_items_log(request: ItemLogSearchRequest):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    search_query = """
        SELECT 
            il.id, il.refnum, p.program_name, i.item_name, il.quantity, il.location, 
            il.reason, il.timestamp, il.attendee, 
            il.program_id, il.item_id
        FROM items_log il
        JOIN programs p ON il.program_id = p.program_id
        JOIN items i ON il.item_id = i.item_id
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

@router.get("/items-log/{id}")
def get_item_log(id: int):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            il.id, il.refnum, p.program_name, i.item_name, il.quantity, il.location, 
            il.reason, il.timestamp, il.attendee, 
            il.program_id, il.item_id
        FROM items_log il
        JOIN programs p ON il.program_id = p.program_id
        JOIN items i ON il.item_id = i.item_id
        WHERE il.id = ?
    ''', (id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else {"error": "Item not found"}