# db.py
import sqlite3
from datetime import datetime

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

def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_programs():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT program_id, program_name FROM programs WHERE status = 'active'")
    programs = [{"program_id": row[0], "program_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return programs

def get_attendees():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attendees")
    attendees = [{"attendee_id": row[0], "employee_id": row[1], "full_name": row[2]} for row in cursor.fetchall()]
    conn.close()
    return attendees

def get_items():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    items = [{"item_id": row[0], "item_name": row[1]} for row in cursor.fetchall()]
    conn.close()
    return items
