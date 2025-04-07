
import json
import sqlite3
import os
import uvicorn

from fastapi import FastAPI, Form, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse 
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


from jose import jwt, JWTError
from datetime import datetime, timedelta
from auth.authentication import authenticate, authenticate_netmiko, authenticate_dummy


# import datetime
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from pprint import pprint
from tabulate import tabulate

from io import BytesIO
from typing import Optional, List


from netmiko import ConnectHandler


SECRET_KEY = "your-secret-key"  # Replace with a strong secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Set token expiration as needed

print(ACCESS_TOKEN_EXPIRE_MINUTES)

# Database file path
DB_FILE = os.getenv("DB_FILE", "db/epmap.db")  # Default to 'db/entries.db' if not specified

# Header file path
PAGE_HEADER = os.getenv("PAGE_HEADER", "Linkrunner Web Tool App - Version 2")  # Default to 'Page Footer' if not specified

# Footer file path
PAGE_FOOTER = os.getenv("PAGE_FOOTER", "© 2025 DevApps by Arvin. All Rights Reserved.")  # Default to 'Page Footer' if not specified


app = FastAPI()

# Mount static files
app.mount("/statics", StaticFiles(directory="statics"), name="statics")

# Initialize templates
templates = Jinja2Templates(directory="templates")


##################################################################
# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DB_FILE) # DB_FILE = db/epmap.db
    conn.row_factory = sqlite3.Row  # To return rows as dictionaries
    return conn

# Initialize the database and create the table with updated columns if it does not exist
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mapping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station TEXT,
            port TEXT,
            interface TEXT,
            floor TEXT,
            info1 TEXT,
            info2 TEXT,
            trans_time TEXT,
            alterby TEXT
        )'''
    )

    conn.commit()
    conn.close()

# Run the database initialization
@app.on_event("startup")
def on_startup():
    init_db()

##################################################################
def get_vlan():
    try:
        conn = get_db_connection()
        
        # Execute query to get VLAN data
        query = "SELECT * FROM vlans"
        cursor = conn.cursor()
        vlan_rows = cursor.execute(query).fetchall()
        vlans = [dict(row) for row in vlan_rows]
        conn.close()
        
        return vlans
    
    except Exception as e:
        # Log the error
        print(f"Error fetching VLAN data: {str(e)}")
        # Return empty list in case of error
        return []


##################################################################
def get_voice():
    try:
        conn = get_db_connection()
        
        # Execute query to get VLAN data
        query = "SELECT * FROM voices"
        cursor = conn.cursor()
        voice_rows = cursor.execute(query).fetchall()
        voice = [dict(row) for row in voice_rows]
        conn.close()
        
        return voice
    
    except Exception as e:
        # Log the error
        print(f"Error fetching VOICE data: {str(e)}")
        # Return empty list in case of error
        return []






# Pydantic model ===================================================================================================
class FormData(BaseModel):
    station: str
    port: str
    interface: str
    floor: str
    info1: str
    info2: str
    trans_time: str
    alterby: str


# Model for each row
class Row(BaseModel):
    station: str
    port: str
    interface: str
    floor: str
    info2: str


# Model for the VLAN change request
class ChangeVlanRequest(BaseModel):
    rows: List[Row]
    vlan: str
    customValue: Optional[str] = None
    username: str
    password: str

# Model for the VOICE change request
class ChangeVoiceRequest(BaseModel):
    rows: List[Row]
    voice: str
    customValue: Optional[str] = None
    username: str
    password: str


class RequestData(BaseModel):
    rows: list
    username: str
    password: str



# ===================================================================================================
class NetworkDeviceManager:
    base_ip = "10.16.0."

    def __init__(self, username: str, password: str, base_ip: str = None):
        self.username = username
        self.password = password
        self.connection = None
        self.current_ip = None
        if base_ip:
            self.base_ip = base_ip

    def connect(self, port: str):
        ip = f"{self.base_ip}{port}"
        
        if ip != self.current_ip:
            if self.connection:
                print(f"\n📴 Cleaning up before switching from {self.current_ip}")
                try:
                    self.connection.send_command("end")
                except Exception as e:
                    print(f"⚠️ Could not send 'end' to {self.current_ip}: {e}")
                self.connection.disconnect()
                self.connection = None
                self.current_ip = None
            

            print(f"\n🔌 Connecting : {self.username}@{ip}...")
            try:
                self.connection = ConnectHandler(
                    device_type='cisco_ios',
                    ip=ip,
                    username=self.username,
                    password=self.password
                )
                self.current_ip = ip
                print(f"✅ Connected to {ip}")
            except Exception as e:
                print(f"❌ Failed to connect : {self.username}@{ip}: {e}")
                self.connection = None
                return str(e)
        
        return self.connection


    # CLEAR PORT  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CLEAR PORT SECURITY 🔥
    def process_and_clear_ports(self, rows: List[dict]):
        results = []
        last_ip = None
        
        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            
            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to new device
                error = self.connect(row['port'])
                if error:
                    results.append({"device": ip, "status": f"❌ Connection failed: {error}"})
                    continue
                last_ip = ip
            
            # Clear interface directly (inline implementation of clear_interface)
            interface = row['interface']
            if not self.connection:
                results.append({"device": ip, "interface": interface, "status": "⚠️ No active connection."})
                continue
                
            print(f"⚡ Clearing {interface} configuration...")
            commands = [
                f"interface {interface}",
                "shutdown",
                "no shutdown"
            ]

            output = self.connection.send_config_set(commands)
            print(f"✔️ Port {interface} cleared successfully.")
            
            results.append({"device": ip, "interface": interface, "status": output})
        
        # ✅ Final cleanup after all rows are processed
        if self.connection:
            self.connection.send_command("end")  # Exits config mode (if applicable)

            print(f"\n🔌 Disconnecting from {self.current_ip}")
            self.connection.disconnect()
            self.connection = None
        
        return results


    # CLEAR PORT STICKY  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CLEAR STICKY PORT 🔥
    def process_and_clear_sticky_interface(self, rows: List[dict]):
        results = []
        last_ip = None

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            interface = row['interface']
            
            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to the new device
                error = self.connect(row['port'])
                if error:
                    results.append({"device": ip, "status": f"❌ Connection failed: {error}"})
                    continue
                last_ip = ip
            
            # If no active connection, skip the interface processing
            if not self.connection:
                results.append({"device": ip, "interface": interface, "status": "⚠️ No active connection."})
                continue
            
            # ⚠️ Clear sticky MAC address (Step 1)
            print(f"⚡ Clearing sticky MAC address on {interface}...")
            self.connection.send_command(f"clear port-security sticky interface {interface}")
            print(f"✔️ Sticky MAC address cleared on {interface}.")
            
            # ⚠️ Apply Shutdown & No Shutdown commands (Step 2)
            print(f"⚡ Reapplying configuration on {interface}...")
            config_commands = [
                f"interface {interface}",
                "shutdown",
                "no shutdown"
            ]

            try:
                output = self.connection.send_config_set(commands)
                print(f"✔️ Configuration applied to {interface} successfully - Clear Sticky.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": output
                })
            except Exception as e:
                # Handle any command failure
                print(f"❌ Failed Configuration applied to {interface} - Clear Sticky.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": f"❌ Command failure: {str(e)}"
                })


        # ✅ Final cleanup after all rows are processed
        if self.connection:
            self.connection.send_command("end")  # Exits config mode (if applicable)

            print(f"\n🔌 Disconnecting from {self.current_ip}")
            self.connection.disconnect()
            self.connection = None
        
        return results


    # CHANGE VLAN  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CHANGE VLAN 🔥
    def process_and_changeVlans(self, rows: list, vlan: str):
        results = []
        last_ip = None  # Track the previous IP

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            
            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from the previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from previous device {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to the new device
                if not self.connect(row['port']):
                    results.append({
                        "device": ip,
                        "interface": row['interface'],
                        "status": "❌ Connection failed."
                    })
                    continue  # Skip to the next row if connection fails
                last_ip = ip  # Update to the current IP
            
            # Proceed with changing the VLAN for the current interface
            interface = row['interface']
            print(f"⚡ Changing VLAN for interface {interface} to vlan {vlan}")
            commands = [
                f"interface {interface}",
                f"switchport access vlan {vlan}",
                "shutdown",
                "no shutdown"
            ]

            try:
                output = self.connection.send_config_set(commands)
                print(f"✔️ VLAN {vlan} applied to interface {interface} successfully.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": output
                })
            except Exception as e:
                # Handle any command failure
                print(f"❌ Failed to apply VLAN {vlan} to interface {interface}: {str(e)}")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": f"❌ Command failure: {str(e)}"
                })
        
        # ✅ Final cleanup after all rows are processed
        if self.connection:
            try:
                self.connection.send_command("end")  # Exits config mode (if applicable)
                print(f"\n🔌 Disconnecting from {self.current_ip}")
            except Exception as e:
                print(f"⚠️ Could not send 'end' command: {str(e)}")

            # Disconnect from the last device
            self.connection.disconnect()
            self.connection = Nonee

        return results


    # CHANGE VOICE  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CHANGE VOICE 🔥
    def process_and_changeVoices(self, rows: list, voice: str):
        results = []
        last_ip = None  # Track the previous IP

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            
            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from the previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from previous device {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to the new device
                if not self.connect(row['port']):
                    results.append({
                        "device": ip,
                        "interface": row['interface'],
                        "status": "❌ Connection failed."
                    })
                    continue  # Skip to the next row if connection fails
                last_ip = ip  # Update to the current IP
            
            # Proceed with changing the VOICE for the current interface
            interface = row['interface']
            print(f"⚡ Changing VOICE for interface {interface} to voice {voice}")
            commands = [
                f"interface {interface}",
                f"switchport voice vlan {voice}",
                "shutdown",
                "no shutdown"
            ]

            try:
                output = self.connection.send_config_set(commands)
                print(f"✔️ VOICE {voice} applied to interface {interface} successfully.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": output
                })
            except Exception as e:
                # Handle any command failure
                print(f"❌ Failed to apply VOICE VLAN {voice} to interface {interface}: {str(e)}")

                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": f"❌ Command failure: {str(e)}"
                })
        
        # ✅ Final cleanup after all rows are processed
        if self.connection:
            try:
                self.connection.send_command("end")  # Exits config mode (if applicable)
                print(f"\n🔌 Disconnecting from {self.current_ip}")
            except Exception as e:
                print(f"⚠️ Could not send 'end' command: {str(e)}")

            # Disconnect from the last device
            self.connection.disconnect()
            self.connection = Nonee

        return results








##################################################################
# ✅ Function to create JWT token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Dependency to get current user from the token
async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated1")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated2")
        
        password: str = payload.get("psub")
        if password is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token structure")
        
        # Return both values (you can return them as a tuple)
        return username, password

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token3")
##################################################################


# ✅load Welcome Page - if Authenticated redirect to Dashboard
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    error = request.query_params.get("error")
    token = request.cookies.get("access_token")
    if token:
        try:
            await get_current_user(request)
            return RedirectResponse(url="/dashboard")
        except HTTPException:
            # Token is invalid, proceed to render login page
            return templates.TemplateResponse("welcome_aim.html", {"request": request, "error": erro, "pageheader": PAGE_HEADER, "pagefooter": PAGE_FOOTER})

    return templates.TemplateResponse("welcome_aim.html", {"request": request, "error": error,  "pageheader": PAGE_HEADER, "pagefooter": PAGE_FOOTER})


# ✅Login / Logout / Authorization Handler
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    
    #auth_result = authenticate(username, password) #authenticate using LDAP3
    #auth_result = authenticate_netmiko(username, password) #authenticate using NETMIKO
    auth_result = authenticate_dummy(username, password) #authenticate using dummy


    if auth_result is True:
        access_token = create_access_token(data={"sub": username,"psub": password})
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        return response
    else:
        error_message = "Can't connect to server to validate user." if auth_result == "Can't connect to server to validate user." else "Invalid username or password"
        return RedirectResponse(url=f"/?error={error_message}", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")  # Clear JWT cookie
    return response

##################################################################
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # Redirect to login page if not authenticated
        return RedirectResponse(url="/?error=you got expired.", status_code=303)
    return templates.TemplateResponse("welcome.html", {"request": request, "error": str(exc.detail)})

##################################################################





# ✅ ALLOWED ENDPOINTS API
# RESTRICTED API PAGES (CENTRAL MAIN PAGE DIRECTOR)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: tuple = Depends(get_current_user)):
    username, password = current_user
    return templates.TemplateResponse("restricted/dashboard.html", {
        "request": request, 
        "username": username, 
        "password": password,
        "pageheader": PAGE_HEADER, 
        "pagefooter": PAGE_FOOTER
        })





# ✅ March30 - New
#NEW ALLOWED - Accessing Restricted Page  ========================================
@app.get("/netscout4", response_class=HTMLResponse)
async def read_items(
        request: Request, 
        current_user: tuple = Depends(get_current_user)
    ):

    username, password = current_user

    # async def get_vlan()
    # async def get_voice()
    vlan = get_vlan()
    voice = get_voice()

    return templates.TemplateResponse("restricted/tabtable4.html", {
        "request": request, 
        "username": username, 
        "password": password,
        "vlan": vlan,
        "voice": voice,
        "pageheader": PAGE_HEADER, 
        "pagefooter": PAGE_FOOTER}
        )


@app.get("/netscout5", response_class=HTMLResponse)
async def read_items(
        request: Request, 
        current_user: tuple = Depends(get_current_user)
    ):

    username, password = current_user

    # async def get_vlan()
    # async def get_voice()
    vlan = get_vlan()
    voice = get_voice()

    return templates.TemplateResponse("restricted/tabtable5.html", {
        "request": request, 
        "username": username, 
        "password": password,
        "vlan": vlan,
        "voice": voice,
        "pageheader": PAGE_HEADER, 
        "pagefooter": PAGE_FOOTER}
        )




# ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
# ✅ Query function for `mapping` table
def query_mapping_db(station, ip_port, interface, floor, info2):
    """Query the SQLite `mapping` table using provided filters."""

    conn = get_db_connection()
    cursor = conn.cursor()

    # Dynamically build the SQL query
    query = "SELECT * FROM mapping WHERE 1=1"  # Always true, allows dynamic filters
    params = []

    if station:
        query += " AND station like ?"
        params.append(f"%{station}%")

    if ip_port:
        query += " AND port like ?"
        params.append(f"%{ip_port}%")

    if interface:
        query += " AND interface like ?"
        params.append(f"%{interface}%")

    if floor:
        query += " AND floor like ?"
        params.append(f"%{floor}%")

    if info2:
        query += " AND info2 like ?"
        params.append(f"%{info2}%")

    # Execute query
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()

    # Close the connection
    conn.close()

    # Convert results to dictionary format
    results = [dict(row) for row in rows]

    return results


# ✅ March30 - New
@app.post("/searchdb")
async def submit_formSearch(request: Request):
    """Handle JSON form submission."""

    # ✅ Read JSON data from the request
    founddata = await request.json()

    # ✅ Extract form values
    station = founddata.get("station")
    ip_port = founddata.get("ip_port")  # Using `ip_port` as `port` from frontend
    interface = founddata.get("interface")
    floor = founddata.get("floor")
    info2 = founddata.get("info2")

    # Log the received data
    print("Searching with:", {
        "station": station,
        "ip_port": ip_port,
        "interface": interface,
        "floor": floor,
        "info2": info2
    })

    # ✅ Query the `mapping` table
    results = query_mapping_db(station, ip_port, interface, floor, info2)

    # ✅ Return the results as JSON
    response_data = {
        "message": "Database search completed!",
        "total_results": len(results),
        "results": results
    }

    return JSONResponse(content=response_data)



# ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
# ✅ *******************************************
@app.post("/clearport")
async def clear_port(request: Request):
    try:
        data = await request.json()
        rows = data.get("rows", [])
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required.")

        '''  
        # ✅ Print only rows, username, and password in JSON format
        print("[REQUEST DEBUG - CLEAR PORT] Incoming Data:\n", json.dumps({
            "rows": rows,
            "username": username,
            "password": password  # ⚠️ Be cautious logging passwords in production
        }, indent=4))
        '''

        manager = NetworkDeviceManager(username=username, password=password)
        result_message = manager.process_and_clear_ports(rows)

        return JSONResponse(content={"message": "✅ All Selected Ports Cleared Successfully.", "details": result_message})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing devices: {str(e)}")


# ✅ *******************************************
@app.post("/clearsticky")
async def process_rows(request: Request):
    try:
        data = await request.json()
        rows = data.get("rows", [])
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required.")

        '''    
        # ✅ Print only rows, username, and password in JSON format
        print("[REQUEST DEBUG - CLEAR STICKY] Incoming Data:\n", json.dumps({
            "rows": rows,
            "username": username,
            "password": password  # ⚠️ Be cautious logging passwords in production
        }, indent=4))
        '''

        manager = NetworkDeviceManager(username=username, password=password)
        result_message = manager.process_and_clear_sticky_interface(rows)

        return JSONResponse(content={"message": "✅ All ports cleared successfully.", "details": result_message})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing devices: {str(e)}")


# ✅ *******************************************
@app.post("/change_vlan")
async def change_vlan(request: ChangeVlanRequest):
    try:

        rows = [row.dict() for row in request.rows]
        vlan = request.customValue if request.vlan == "000" else request.vlan

        '''
        print("[REQUEST DEBUG - VLAN] Incoming Data:\n", json.dumps({
            "rows": [row.dict() for row in request.rows],  # Convert each Row model to dict
            "username": request.username,
            "password": request.password,  # ⚠️ Be cautious logging passwords in production
            "vlan": vlan,
        }, indent=4))
        '''

        manager = NetworkDeviceManager(username=request.username, password=request.password)
        result_message = manager.process_and_changeVlans(rows,vlan)

        # Return success response
        return {"message": f"VLAN {vlan} applied to {len(rows)} ports"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing devices: {str(e)}")


# ✅ *******************************************
@app.post("/change_voice")
async def change_voice(request: ChangeVoiceRequest):
    try:

        rows = [row.dict() for row in request.rows]
        voice = request.customValue if request.voice == "000" else request.voice

        '''
        print("[REQUEST DEBUG - VOICE] Incoming Data:\n", json.dumps({
            "rows": [row.dict() for row in request.rows],  # Convert each Row model to dict
            "username": request.username,
            "password": request.password,  # ⚠️ Be cautious logging passwords in production
            "voice": voice,
        }, indent=4))
        '''

        

        manager = NetworkDeviceManager(username=request.username, password=request.password)
        result_message = manager.process_and_changeVoices(rows, voice)

        # Return success response
        return {"message": f"VOICE {voice} applied to {len(rows)} ports"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing devices: {str(e)}")





# 🚀 *******************************************
@app.post("/showStatus")
async def process_rows(request: Request):
    data = await request.json()
    rows = data.get("rows", [])

    if not rows:
        return JSONResponse(content={"message": "No rows received."}, status_code=400)

    # ✅ Print the rows in table format
    headers = ["Station", "Port", "Interface", "Floor", "Info2"]  # Table headers
    table_data = [list(row.values()) for row in rows]

    print("\n🚀 Received Rows in Table Format: SHOW VLAN STATUS")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # ✅ Respond with success message
    return JSONResponse(content={"message": f"{len(rows)} rows processed successfully."})





# ✅✅✅✅✅✅✅✅✅✅✅✅✅✅✅
if __name__ == "__main__":
    # Get port from command-line argument or use default 8857
   # port = int(sys.argv[1]) if len(sys.argv) > 1 else 8857

    cert_dir = os.path.join(os.path.dirname(__file__), "certs")
    ssl_keyfile = os.path.join(cert_dir, "server_unencrypted.key")
    ssl_certfile = os.path.join(cert_dir, "server.crt")

    #uvicorn.run(app, host="0.0.0.0", port=port, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
    uvicorn.run(app, host="0.0.0.0", port=8856, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)

    