
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
from typing import Optional


SECRET_KEY = "your-secret-key"  # Replace with a strong secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1  # Set token expiration as needed


# Database file path
DB_FILE = os.getenv("DB_FILE", "db/epmap.db")  # Default to 'db/entries.db' if not specified


# Header file path
PAGE_HEADER = os.getenv("PAGE_HEADER", "NetScout Web App - Version 2")  # Default to 'Page Footer' if not specified

# Footer file path
PAGE_FOOTER = os.getenv("PAGE_FOOTER", "2024 DevApps. All Rights Reserved.")  # Default to 'Page Footer' if not specified




app = FastAPI()

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
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

# Mount static files
app.mount("/statics", StaticFiles(directory="statics"), name="statics")

# Initialize templates
templates = Jinja2Templates(directory="templates")


# ===================================================================================================
# Pydantic model for item data
class Item(BaseModel):
    station: str
    port: str
    interface: str
    floor: str
    info1: str
    info2: str
    trans_time: str
    alterby: str

##################################################################

# Function to create JWT token
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





# load Welcome Page - if Authenticated redirect to Dashboard
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


# Login / Logout / Authorization Handler
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    
    #auth_result = authenticate(username, password) #authenticate using LDAP3
    #auth_result = authenticate_netmiko(username, password) #authenticate using NETMIKO
    auth_result = authenticate_dummy(username, password) #authenticate using NETMIKO

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

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # Redirect to login page if not authenticated
        return RedirectResponse(url="/?error=you got expired.", status_code=303)
    return templates.TemplateResponse("welcome.html", {"request": request, "error": str(exc.detail)})







# RESTRICTED API PAGES ========================================
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



#NEW Working Netscout V2========================================
@app.get("/main_app_test", response_class=HTMLResponse)
async def read_items(request: Request, current_user: tuple = Depends(get_current_user)):
    username, password = current_user
    return templates.TemplateResponse("restricted/main_app_test2.html", {
        "request": request, 
        "username": username, 
        "password": password,
        "pageheader": PAGE_HEADER, 
        "pagefooter": PAGE_FOOTER}
        )





#NEW Working Netscout V2========================================
@app.get("/main_app2", response_class=HTMLResponse)
async def read_items(request: Request, username: str = Depends(get_current_user)):
    return templates.TemplateResponse("restricted/main_app2.html", {"request": request, "username": username, "pageheader": PAGE_HEADER, "pagefooter": PAGE_FOOTER})




# ================================ RESTFUL API for Items  ===============================

# FETCH All Items from the database
@app.post("/findport")
async def find_port(request: Request, floor: str = Form(...), port: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM mapping WHERE floor LIKE ? AND station LIKE ? ORDER BY station ASC"
    cursor.execute(query, ('%' + floor + '%', '%' + port + '%'))
    ports_data = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if request.headers.get('accept') == 'application/json':
        return JSONResponse(content={"ports": ports_data})
    
    # Print the data using tabulate (optional for debugging)
    selected_columns = [(row["id"], row["floor"], row["station"], row["port"], row["interface"]) for row in ports_data]
    headers = ["id", "floor", "station", "port", "interface"]
    print(tabulate(selected_columns, headers=headers, tablefmt="pretty"))

    return templates.TemplateResponse("restricted/main_app_test.html", {
        "request": request,
        "ports": ports_data,
    })







if __name__ == "__main__":
    # Get port from command-line argument or use default 8857
   # port = int(sys.argv[1]) if len(sys.argv) > 1 else 8857

    cert_dir = os.path.join(os.path.dirname(__file__), "certs")
    ssl_keyfile = os.path.join(cert_dir, "server_unencrypted.key")
    ssl_certfile = os.path.join(cert_dir, "server.crt")

    #uvicorn.run(app, host="0.0.0.0", port=port, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
    uvicorn.run(app, host="0.0.0.0", port=8856, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)