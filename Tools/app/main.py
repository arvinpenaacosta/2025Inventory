from fastapi import FastAPI, staticfiles
from fastapi.responses import HTMLResponse
import sqlite3
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Serve static files
app.mount("/static", staticfiles.StaticFiles(directory="static"), name="static")

class Location(BaseModel):
    id: int
    xPercent: float
    yPercent: float
    locNumber: int
    locStation: int
    fillColor: str
    strokeColor: str

@app.get("/api/locations")
async def get_locations():
    conn = sqlite3.connect('locations.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Locations")
    locations = cursor.fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    location_list = []
    for loc in locations:
        location_list.append({
            "id": loc[0],
            "xPercent": loc[1],
            "yPercent": loc[2],
            "locNumber": loc[3],
            "locStation": loc[4],
            "fillColor": loc[5],
            "strokeColor": loc[6]
        })
    
    return {"instances": location_list}

@app.get("/", response_class=HTMLResponse)
async def get_html():
    with open("static/index.html") as f:
        return f.read()