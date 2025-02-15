import os
import uvicorn

from fastapi import FastAPI, Form, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse 

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jose import jwt, JWTError
from datetime import datetime, timedelta
from auth.authentication import authenticate_dummy

# import datetime
from datetime import datetime

#######################################################################
from routes.itemlog_routes import router as itemlog_router
from routes.program_routes import router as program_router
from routes.product_routes import router as product_router
#######################################################################
SECRET_KEY = "your-secret-key"  # Replace with a strong secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Set token expiration as needed

# Header file path
PAGE_HEADER = os.getenv("PAGE_HEADER", "DevApp Inventory Logger - Version 0")  # Default to 'Page Footer' if not specified
# Footer file path
PAGE_FOOTER = os.getenv("PAGE_FOOTER", "2024 DevApps. All Rights Reserved.")  # Default to 'Page Footer' if not specified


app = FastAPI()
# Mount static files
app.mount("/statics", StaticFiles(directory="statics"), name="statics")

# Initialize templates
templates = Jinja2Templates(directory="templates")

################## JSON WEB TOKEN for Authentication  ##################################

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
            return templates.TemplateResponse("login.html", {"request": request, "error": error, "pageheader": PAGE_HEADER, "pagefooter": PAGE_FOOTER})

    return templates.TemplateResponse("login.html", {"request": request, "error": error,  "pageheader": PAGE_HEADER, "pagefooter": PAGE_FOOTER})

# Login / Logout / Authorization Handler (IF AUTHORIZED will RE-DIRECT TO AUTHORIZED API ENDPOINT)
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    
    #auth_result = authenticate(username, password) #authenticate using LDAP3
    #auth_result = authenticate_netmiko(username, password) #authenticate using NETMIKO
    auth_result = authenticate_dummy(username, password) #authenticate using Dummy User
    #auth_result = authenticate_Xuser(username, password) # use sqlite 

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

# Include API routers with prefix
app.include_router(itemlog_router, prefix="/entryAPI", tags=["itemlogs"])
app.include_router(program_router, prefix="/FM_API", tags=["programs"])
app.include_router(product_router, prefix="/FM_API", tags=["products"])
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
render_page("/items-log", "restricted/items-log.html")      #   https://127.0.0.1:8801/items-log
render_page("/programs", "restricted/programs.html") 
render_page("/products", "restricted/products.html") 




print("Main.py Line 154")
#######################################################################
'''
print("Main.py Line 157)
# AUTHORIZED API ENDPOINT TO ACCESS
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

# AUTHORIZED API ENDPOINT TO ACCESS     https://127.0.0.1:8801/items-log
@app.get("/items-log", response_class=HTMLResponse)
async def itemlog(request: Request, current_user: tuple = Depends(get_current_user)):
    username, password = current_user
    return templates.TemplateResponse("restricted/items-log.html", {
        "request": request, 
        "username": username, 
        "password": password,
        "pageheader": PAGE_HEADER, 
        "pagefooter": PAGE_FOOTER
        })
'''
#######################################################################
print("Main.py Line 183")





if __name__ == "__main__":
    # Get port from command-line argument or use default 8857
   # port = int(sys.argv[1]) if len(sys.argv) > 1 else 8857

    cert_dir = os.path.join(os.path.dirname(__file__), "certs")
    ssl_keyfile = os.path.join(cert_dir, "server_unencrypted.key")
    ssl_certfile = os.path.join(cert_dir, "server.crt")

    #uvicorn.run(app, host="0.0.0.0", port=port, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)
    uvicorn.run(app, host="0.0.0.0", port=8856, ssl_keyfile=ssl_keyfile, ssl_certfile=ssl_certfile)