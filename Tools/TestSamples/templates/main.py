# March 15, 2024 Revised Main.py
# Add Additional field  def create_table2(),  @app.post("/input1a/")


from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi.responses import RedirectResponse
from fastapi import Response

from contextlib import closing



import os
import sqlite3

from datetime import datetime
from tabulate import tabulate


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"))

# Initialize templates
templates = Jinja2Templates(directory="templates")

from dotenv import load_dotenv
import sys


# Get the command line arguments
args = sys.argv[1:]

host = "127.0.0.1"
port = 8000


# Iterate through the arguments and extract host and port
for i in range(len(args)):
    if args[i] == "--host" and i + 1 < len(args):
        host = args[i + 1]
    elif args[i] == "--port" and i + 1 < len(args):
        port = args[i + 1]

# Print the extracted host and port
print("Host:", host)
print("Port:", port)

# Load environment variables from .env file
load_dotenv()

# Access environment variables
host = os.getenv("SQL_HOST")
port = os.getenv("SQL_PORT")
SQLDB = os.getenv("SQLiteDB")

print(f"SQL_HOST: {host}")
print(f"SQL_PORT: {port}")
print(f"SQL_DB: {SQLDB}")


# Creating the FastAPI instance
app = FastAPI()

# Creating the SQLite database connection
DB_FILE = f"./db/{SQLDB}"


# Function to create a connection to the SQLite database
def get_connection():
    connection = sqlite3.connect(DB_FILE)
    return connection

# Function to create the entries table if it doesn't exist
def create_table():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            Floor TEXT,
            Location TEXT,
            CiscoExt TEXT,
            Updateby TEXT,
            ComputerName TEXT,
            SerialNumber TEXT,
            PCModel TEXT,
            CPU TEXT,
            RAM TEXT,
            IPAddress TEXT,            
            MACAddress TEXT,
            WindowsEdition TEXT,
            DisplayVersion TEXT,            
            OSVersion TEXT,
            CitrixName TEXT,
            CitrixVersion TEXT,
            RecordedDateTime TEXT
        );
    """)
    connection.commit()
    connection.close()

# Function to create the entries table if it doesn't exist
def create_table2():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            Floor TEXT,
            Location1 TEXT,
            Location2 TEXT,
            CiscoExt TEXT,
            Updateby TEXT,
            ComputerName TEXT,
            SerialNumber TEXT,
            PCModel TEXT,
            CPU TEXT,
            RAM TEXT,
            IPAddress TEXT,            
            MACAddress TEXT,
            WindowsEdition TEXT,
            DisplayVersion TEXT,            
            OSVersion TEXT,
            CitrixName TEXT,
            CitrixVersion TEXT,
            RecordedDateTime TEXT
        );
    """)
    connection.commit()
    connection.close()

# Create the entries table
create_table2()
####==============================================================


#------------------------------------------------------------------
# API endpoint to create a new entry
@app.post("/input2/")
def create_entry(
    Floor: str = Form(...), 
    Location: str = Form(...),
    CiscoExt: str = Form(...),
    Updateby: str = Form(...),
    CompName: str = Form(...),
    SerNum: str = Form(...),
    PCModel: str = Form(...),
    CPUName: str = Form(...),
    RAM: str = Form(...),
    IPAddress: str = Form(...),    
    MACVal: str = Form(...),
    WinEdition: str = Form(...),
    DisplayVersion: str = Form(...),   
    OSVer: str = Form(...),
    CitrixDisplayName: str = Form(...),
    CitrixDisplayVersion: str = Form(...)
):
    # Connect to SQLite database
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Get current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert data into the database
        cursor.execute("INSERT INTO entries (Floor, Location, CiscoExt, Updateby, ComputerName, SerialNumber, PCModel, CPU, RAM, IPAddress, MACAddress, WindowsEdition, DisplayVersion, OSVersion, CitrixName, CitrixVersion, RecordedDateTime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                        (Floor, Location, CiscoExt, Updateby, CompName, SerNum, PCModel, CPUName, RAM, IPAddress, MACVal, WinEdition, DisplayVersion, OSVer, CitrixDisplayName, CitrixDisplayVersion, current_time))
    
        # Commit changes and close connection
        connection.commit()
        connection.close()

        # Return success message
        return "Data saved to SQLite Database successfully."
    
    except Exception as e:
        # Rollback changes and close connection in case of an error
        connection.rollback()
        connection.close()
        
        # Return error message
        return f"An error occurred: {str(e)}"
#------------------------------------------------------------------

#------------------------------------------------------------------
# API endpoint to create a new entry
@app.post("/input1a/")
def create_entry(
    Floor: str = Form(...), 
    Location1: str = Form(...),
    Location2: str = Form(...),
    CiscoExt: str = Form(...),
    Updateby: str = Form(...),
    ComputerName: str = Form(...),
    SerialNumber: str = Form(...),
    PCModel: str = Form(...),
    CPU: str = Form(...),
    RAM: str = Form(...),
    IPAddress: str = Form(...),    
    MACAddress: str = Form(...),
    WindowsEdition: str = Form(...),
    DisplayVersion: str = Form(...),   
    OSVersion: str = Form(...),
    CitrixName: str = Form(...),
    CitrixVersion: str = Form(...)
):
    # Connect to SQLite database
    connection = get_connection()
    cursor = connection.cursor()

    # Removing all spaces from a string
    Location1 = Location1.replace(" ", "")


    try:
        # Get current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert data into the database
        cursor.execute("INSERT INTO entries (Floor, Location1, Location2, CiscoExt, Updateby, ComputerName, SerialNumber, PCModel, CPU, RAM, IPAddress, MACAddress, WindowsEdition, DisplayVersion, OSVersion, CitrixName, CitrixVersion, RecordedDateTime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                        (Floor, Location1, Location2, CiscoExt, Updateby, ComputerName, SerialNumber, PCModel, CPU, RAM, IPAddress, MACAddress, WindowsEdition, DisplayVersion, OSVersion, CitrixName, CitrixVersion, current_time))
    
        # Commit changes and close connection
        connection.commit()
        connection.close()

        # Return success message
        return f"Saved to SQLite Database successfully."
        
    
    except Exception as e:
        # Rollback changes and close connection in case of an error
        connection.rollback()
        connection.close()
        
        # Return error message
        return f"An error occurred: {str(e)}"
#------------------------------------------------------------------






# API endpoint to show all records
@app.get("/show1/")
async def show_records(request: Request):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM entries ORDER by ID DESC")
    entries = cursor.fetchall()
    connection.close()
    return templates.TemplateResponse("show1.html", {"request": request, "entries": entries})





# API endpoint to show all records
@app.get("/show3/")
async def show_records(request: Request):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * 
        FROM entries 
        ORDER BY Location1 ASC, Location2 ASC, SerialNumber ASC;
    """)

    entries = cursor.fetchall()
    connection.close()
    return templates.TemplateResponse("show3.html", {"request": request, "entries": entries})



# =======================================================Working
# API endpoint to show all records
@app.get("/show6/")
async def show_records(request: Request):


    selected_floor = "0"
    print(f"425 selected floor: {selected_floor}")

    connection = get_connection()
    cursor = connection.cursor()

    # Query to get distinct floors
    cursor.execute("""
        SELECT DISTINCT Floor
        FROM entries
    """)
    distinct_floors = cursor.fetchall()

    # Query to get floor-wise location counts
    cursor.execute("""
        SELECT Floor, Location1, COUNT(Location1) AS Location2_Count
        FROM entries
        WHERE Floor = ? 
        GROUP BY Floor, Location1
    """, (selected_floor))
    entries = cursor.fetchall()

    connection.close()
    return templates.TemplateResponse("show6.html", {"request": request, "entries": entries, "distinct_floors": distinct_floors, "selected_floor": selected_floor})



# =======================================================Working
@app.post("/show6/")
async def generate_floor_records(request: Request):
    form_data = await request.form()
    selected_floor = form_data["selectedFloor"]


    print(f"458 selected floor: {selected_floor}")

    connection = get_connection()
    cursor = connection.cursor()


    # Query to get distinct floors
    cursor.execute("""
        SELECT DISTINCT Floor
        FROM entries
    """)
    distinct_floors = cursor.fetchall()

    # Query to get floor-wise location counts for the selected floor
    cursor.execute("""
        SELECT Floor, Location1, COUNT(Location1) AS Location2_Count
        FROM entries
        WHERE Floor = ?
        GROUP BY Floor, Location1
    """, (selected_floor,))
    entries = cursor.fetchall()

    connection.close()
    return templates.TemplateResponse("show6.html", {"request": request, "entries": entries, "distinct_floors": distinct_floors, "selected_floor": selected_floor})


# =======================================================Working
@app.get("/show6/{floor}/{loc1}/")
async def show6(request: Request, floor: str, loc1: str):

    selected_floor = floor

    print(f"458 selected floor: {selected_floor}")

    connection = get_connection()
    cursor = connection.cursor()


    # Query to get distinct floors
    cursor.execute("""
        SELECT DISTINCT Floor
        FROM entries
    """)
    distinct_floors = cursor.fetchall()

    # Query to get floor-wise location counts for the selected floor
    cursor.execute("""
        SELECT Floor, Location1, COUNT(Location1) AS Location2_Count
        FROM entries
        WHERE Floor = ?
        GROUP BY Floor, Location1
    """, (selected_floor,))
    entries = cursor.fetchall()

    # Query to get floor-wise location counts for the selected floor
    cursor.execute("""
        SELECT Location1, Location2, ComputerName, SerialNumber, IPAddress, MACAddress, WindowsEdition, DisplayVersion, CitrixVersion, RecordedDateTime
        FROM entries
        WHERE Floor = ? AND Location1 = ?
        Order by Location2 Asc, RecordedDateTime Desc
    """, (floor,loc1))
    invRec = cursor.fetchall()

    #Location1, Location2,  CiscoExt, Updateby, ComputerName, SerialNumber,
    #PCModel, CPU, RAM, IPAddress, MACAddress, WindowsEdition, DisplayVersion, OSVersion,
    #CitrixName, CitrixVersion, RecordedDateTime,

    connection.close()
    return templates.TemplateResponse("show6.html", {"request": request, "entries": entries, "distinct_floors": distinct_floors, "selected_floor": selected_floor, "invRec": invRec})




# =======================================================Working
# API endpoint to show all records
@app.get("/show7/")
async def show_records(request: Request):


    selected_floor = "0"
    print(f"425 selected floor: {selected_floor}")

    connection = get_connection()
    cursor = connection.cursor()

    # Query to get distinct floors
    cursor.execute("""
        SELECT DISTINCT Floor
        FROM entries
        WHERE Updateby like 'Patch%'
    """)
    distinct_floors = cursor.fetchall()

    # Query to get floor-wise location counts
    cursor.execute("""
        SELECT Floor, Location1, COUNT(Location1) AS Location2_Count
        FROM entries
        WHERE Floor = ? AND Updateby like 'Patch%'
        GROUP BY Floor, Location1
    """, (selected_floor))
    entries = cursor.fetchall()

    connection.close()
    return templates.TemplateResponse("show7.html", {"request": request, "entries": entries, "distinct_floors": distinct_floors, "selected_floor": selected_floor})

# =======================================================Working
@app.post("/show7/")
async def generate_floor_records(request: Request):
    form_data = await request.form()
    selected_floor = form_data["selectedFloor"]


    print(f"458 selected floor: {selected_floor}")

    connection = get_connection()
    cursor = connection.cursor()


    # Query to get distinct floors
    cursor.execute("""
        SELECT DISTINCT Floor
        FROM entries 
        WHERE Updateby like 'Patch%'
    """)
    distinct_floors = cursor.fetchall()

    # Query to get floor-wise location counts for the selected floor
    cursor.execute("""
        SELECT Floor, Location1, COUNT(Location1) AS Location2_Count
        FROM entries
        WHERE Floor = ? AND Updateby like 'Patch%'
        GROUP BY Floor, Location1
    """, (selected_floor,))
    entries = cursor.fetchall()

    connection.close()
    return templates.TemplateResponse("show7.html", {"request": request, "entries": entries, "distinct_floors": distinct_floors, "selected_floor": selected_floor})


# =======================================================Working
@app.get("/show7/{floor}/{loc1}/")
async def show7(request: Request, floor: str, loc1: str):

    selected_floor = floor

    print(f"458 selected floor: {selected_floor}")

    connection = get_connection()
    cursor = connection.cursor()


    # Query to get distinct floors
    cursor.execute("""
        SELECT DISTINCT Floor
        FROM entries
        WHERE Updateby like 'Patch%'
    """)
    distinct_floors = cursor.fetchall()

    # Query to get floor-wise location counts for the selected floor
    cursor.execute("""
        SELECT Floor, Location1, COUNT(Location1) AS Location2_Count
        FROM entries
        WHERE Floor = ? AND Updateby like 'Patch%'
        GROUP BY Floor, Location1
    """, (selected_floor,))
    entries = cursor.fetchall()

    # Query to get floor-wise location counts for the selected floor
    cursor.execute("""
        SELECT Location1, Location2, ComputerName, SerialNumber, IPAddress, MACAddress, WindowsEdition, DisplayVersion, CitrixVersion, RecordedDateTime
        FROM entries
        WHERE Floor = ? AND Location1 = ? AND Updateby like 'Patch%'
        Order by Location2 Asc, RecordedDateTime Desc
    """, (floor,loc1))
    invRec = cursor.fetchall()

    #Location1, Location2,  CiscoExt, Updateby, ComputerName, SerialNumber,
    #PCModel, CPU, RAM, IPAddress, MACAddress, WindowsEdition, DisplayVersion, OSVersion,
    #CitrixName, CitrixVersion, RecordedDateTime,

    connection.close()
    return templates.TemplateResponse("show7.html", {"request": request, "entries": entries, "distinct_floors": distinct_floors, "selected_floor": selected_floor, "invRec": invRec})



#===================================================================
@app.get("/test")
async def home(
        request: Request
        ):

    print("TESTING LINKS")
    return templates.TemplateResponse(
        "/test.html", 
        {"request": request}
        )


#===================================================================
@app.get("/map")
async def home(
        request: Request
        ):

    print("TESTING LINKS")
    return templates.TemplateResponse(
        "/map.html", 
        {"request": request}
        )



# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# uvicorn main:app --reload
#############################
# uvicorn main:app --reload --host 10.16.67.27 --port 8856



