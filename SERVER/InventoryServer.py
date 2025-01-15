from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Constants
DB_FILE = os.getenv("SQLiteDB", "db/2025inv.db")  # Default to "./db/2025inv.db" if env variable is missing
CERT_DIR = os.path.join(os.path.dirname(__file__), "certs")
SSL_KEYFILE = os.path.join(CERT_DIR, "server_unencrypted.key")
SSL_CERTFILE = os.path.join(CERT_DIR, "server.crt")

# Initialize FastAPI app
app = FastAPI()


def get_connection():
    connection = sqlite3.connect(DB_FILE)
    return connection


# Define a Pydantic model for the incoming data
class DataObject(BaseModel):
    Floor: str
    Location1: str
    Location2: str
    LANPort: str
    CiscoExt: str
    Updateby: str
    ComputerName: str
    SerialNumber: str
    PCModel: str
    Processor: str
    RAMSlot: str
    RAMCapGB: str
    RAMTotalGB: str
    RAMType: str
    SpeedMHz: str
    Mfr: str
    RAMSerNum: str
    IPAddress: str
    MACAddress: str
    WindowsEdition: str
    DisplayVersion: str
    OSVersion: str
    CitrixName: str
    CitrixVersion: str
    #RecordedDateTime: str
    NOCItem: str

# Database initialization function
def create_table():
    connection = get_connection()
    cursor = connection.cursor()
        # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Floor TEXT,
            Location1 TEXT,
            Location2 TEXT,
            LANPort TEXT,
            CiscoExt TEXT,
            Updateby TEXT,
            ComputerName TEXT,
            SerialNumber TEXT,
            PCModel TEXT,
            Processor TEXT,
            RAMSlot TEXT,
            RAMCapGB TEXT,
            RAMTotalGB TEXT,
            RAMType TEXT,
            SpeedMHz TEXT,
            Mfr TEXT,
            RAMSerNum TEXT,
            IPAddress TEXT,
            MACAddress TEXT,
            WindowsEdition TEXT,
            DisplayVersion TEXT,
            OSVersion TEXT,
            CitrixName TEXT,
            CitrixVersion TEXT,
            RecordedDateTime TEXT,
            NOCItem TEXT
        )
    """)
    connection.commit()
    connection.close()

# Initialize the database
create_table()

# FastAPI endpoint to receive data and save it
@app.post("/api_save_data")
async def save_data(data: DataObject):
    try:
        RecordedDateTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(""" 
            INSERT INTO data (
                Floor, Location1, Location2, LANPort, CiscoExt, Updateby, 
                ComputerName, SerialNumber, PCModel, Processor, RAMSlot, 
                RAMCapGB, RAMTotalGB, RAMType, SpeedMHz, Mfr,
                RAMSerNum, IPAddress, MACAddress, WindowsEdition, DisplayVersion, 
                OSVersion, CitrixName, CitrixVersion, RecordedDateTime, NOCItem
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,   ?, ?, ?, ?, ?)
            """, (
                data.Floor, data.Location1, data.Location2, data.LANPort, data.CiscoExt, data.Updateby, 
                data.ComputerName, data.SerialNumber, data.PCModel, data.Processor, data.RAMSlot, 
                data.RAMCapGB, data.RAMTotalGB, data.RAMType, data.SpeedMHz, data.Mfr, 
                data.RAMSerNum, data.IPAddress, data.MACAddress, data.WindowsEdition, data.DisplayVersion, 
                data.OSVersion, data.CitrixName, data.CitrixVersion, RecordedDateTime, data.NOCItem
            ))
            conn.commit()
        return {"message": "Data saved successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Duplicate or invalid data.")
    except Exception as e:
        # Rollback changes in case of an error
        with sqlite3.connect(DB_FILE) as conn:
            conn.rollback()
        # Return error message
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# Validate SSL files exist before running
if not os.path.exists(SSL_KEYFILE) or not os.path.exists(SSL_CERTFILE):
    raise FileNotFoundError("SSL certificate or key file not found. Ensure 'server_unencrypted.key' and 'server.crt' exist in the 'certs' directory.")

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8892,
        ssl_keyfile=SSL_KEYFILE,
        ssl_certfile=SSL_CERTFILE
    )


# uvicorn server_inv:app --host 0.0.0.0 --port 8892
# uvicorn 2025_InvServer:app --host 192.168.1.18 --port 8892 --reload --ssl-keyfile=certs/server_unencrypted.key --ssl-certfile=certs/server.crt
# uvicorn InventoryServer:app --host 10.16.67.27 --port 8892 --reload --ssl-keyfile=certs/server_unencrypted.key --ssl-certfile=certs/server.crt
