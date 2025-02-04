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
from auth.auth_sqlitedb import authenticate_user, authenticate_Xuser


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
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Set token expiration as needed

# Database file path
DB_FILE = os.getenv("DB_FILE", "db/epmap.db")  # Default to 'db/entries.db' if not specified

# Header file path
PAGE_HEADER = os.getenv("PAGE_HEADER", "NetScout Web App - Version 2")  # Default to 'Page Footer' if not specified

# Footer file path
PAGE_FOOTER = os.getenv("PAGE_FOOTER", "2024 DevApps. All Rights Reserved.")  # Default to 'Page Footer' if not specified

app = FastAPI()

# Mount static files
app.mount("/statics", StaticFiles(directory="statics"), name="statics")

# Initialize templates
templates = Jinja2Templates(directory="templates")


##################################################################
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eid TEXT UNIQUE NOT NULL,
            complete_name TEXT NOT NULL,
            login_name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            status TEXT CHECK(status IN ('active', 'inactive')) NOT NULL DEFAULT 'active',
            param1 TEXT,
            param2 TEXT,
            param3 TEXT
        )'''
    )

    conn.commit()
    conn.close()






# Run the database initialization
@app.on_event("startup")
def on_startup():
    init_db()

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



# Function to handle response after authentication
def handle_authenticated_response(username: str, password: str) -> RedirectResponse:
    access_token = create_access_token(data={"sub": username, "psub": password})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return response

# Function to handle the error response
def handle_error_response(auth_result: str) -> RedirectResponse:
    error_message = "Can't connect to server to validate user." if auth_result == "Can't connect to server to validate user." else "Invalid username or password"
    return RedirectResponse(url=f"/?error={error_message}", status_code=303)


#######################################################################
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
            return templates.TemplateResponse("welcome_aim.html", {"request": request, "error": error, "pageheader": PAGE_HEADER, "pagefooter": PAGE_FOOTER})

    return templates.TemplateResponse("welcome_aim.html", {"request": request, "error": error,  "pageheader": PAGE_HEADER, "pagefooter": PAGE_FOOTER})

# Login / Logout / Authorization Handler (IF AUTHORIZED will RE-DIRECT TO AUTHORIZED API ENDPOINT)
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    
    #auth_result = authenticate(username, password) #authenticate using LDAP3
    #auth_result = authenticate_netmiko(username, password) #authenticate using NETMIKO
    #auth_result = authenticate_dummy(username, password) #authenticate using NETMIKO
    auth_result = authenticate_Xuser(username, password) # use sqlite 

    if auth_result is True:
        return handle_authenticated_response(username, password)
    else:
        return handle_error_response(auth_result)


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

#######################################################################


# AUTHORIZED API ENDPOINT TO ACCESS
def render_page(route: str, template_path: str):
    @app.get(route, response_class=HTMLResponse)
    async def page(request: Request, current_user: tuple = Depends(get_current_user)):
        username, password = current_user
        return templates.TemplateResponse(template_path, {
            "request": request,
            "username": username,
            "password": password,
            "pageheader": PAGE_HEADER,
            "pagefooter": PAGE_FOOTER
        })
    return page


render_page("/dashboard", "restricted/dashboard.html")
render_page("/clock1", "restricted/clock1.html")
render_page("/clock2", "restricted/clock2.html")



# AUTHORIZED API ENDPOINT TO ACCESS
@app.get("/clock22", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: tuple = Depends(get_current_user)):
    username, password = current_user
    return templates.TemplateResponse("restricted/clock2.html", {
        "request": request, 
        "username": username, 
        "password": password,
        "pageheader": PAGE_HEADER, 
        "pagefooter": PAGE_FOOTER
        })




if __name__ == "__main__":
    # Get port from command-line argument or use default 8857
   # port = int(sys.argv[1]) if len(sys.argv) > 1 else 8857

    cert_dir = os.path.join(os.path.dirname(__file__), "certs")
    ssl_keyfile = os.path.join(cert_dir, "server_unencrypted.key")
    ssl_certfile = os.path.join(cert_dir, "server.crt")

    #uvicorn.run(app, host="0.0.0.0", port=port, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
    uvicorn.run(app, host="0.0.0.0", port=8856, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
