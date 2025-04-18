import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('locations.db')
cur = conn.cursor()

# Create the Locations table
cur.execute('''
CREATE TABLE IF NOT EXISTS Locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    xPercent REAL,
    yPercent REAL,
    locNumber INTEGER,
    locStation INTEGER,
    fillColor TEXT,
    strokeColor TEXT
)
''')

# Data to insert
data = [
    {"xPercent": 0.035, "yPercent": 0.050, "locNumber": 10, "locStation": 12, "fillColor": "lightblue", "strokeColor": "blue"},
    {"xPercent": 0.035, "yPercent": 0.130, "locNumber": 9, "locStation": 6, "fillColor": "lightgreen", "strokeColor": "darkgreen"},
    {"xPercent": 0.035, "yPercent": 0.210, "locNumber": 8, "locStation": 1, "fillColor": "lightcoral", "strokeColor": "darkred"},
    {"xPercent": 0.035, "yPercent": 0.290, "locNumber": 7, "locStation": 4, "fillColor": "lightyellow", "strokeColor": "gold"},
    {"xPercent": 0.035, "yPercent": 0.370, "locNumber": 6, "locStation": 0, "fillColor": "lightgray", "strokeColor": "black"},
    {"xPercent": 0.035, "yPercent": 0.450, "locNumber": 5, "locStation": 12, "fillColor": "lightblue", "strokeColor": "blue"},
    {"xPercent": 0.035, "yPercent": 0.530, "locNumber": 4, "locStation": 6, "fillColor": "lightgreen", "strokeColor": "darkgreen"},
    {"xPercent": 0.035, "yPercent": 0.610, "locNumber": 3, "locStation": 1, "fillColor": "lightcoral", "strokeColor": "darkred"},
    {"xPercent": 0.035, "yPercent": 0.690, "locNumber": 2, "locStation": 4, "fillColor": "lightyellow", "strokeColor": "gold"},
    {"xPercent": 0.035, "yPercent": 0.770, "locNumber": 1, "locStation": 0, "fillColor": "lightgray", "strokeColor": "black"},
    {"xPercent": 0.110, "yPercent": 0.050, "locNumber": 1, "locStation": 12, "fillColor": "lightblue", "strokeColor": "blue"},
    {"xPercent": 0.110, "yPercent": 0.130, "locNumber": 2, "locStation": 6, "fillColor": "lightgreen", "strokeColor": "darkgreen"},
    {"xPercent": 0.110, "yPercent": 0.210, "locNumber": 3, "locStation": 1, "fillColor": "lightcoral", "strokeColor": "darkred"},
    {"xPercent": 0.110, "yPercent": 0.290, "locNumber": 4, "locStation": 4, "fillColor": "lightyellow", "strokeColor": "gold"},
    {"xPercent": 0.110, "yPercent": 0.370, "locNumber": 5, "locStation": 0, "fillColor": "lightgray", "strokeColor": "black"}
]

# Insert the data into the Locations table
for entry in data:
    cur.execute('''
    INSERT INTO Locations (xPercent, yPercent, locNumber, locStation, fillColor, strokeColor)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (entry["xPercent"], entry["yPercent"], entry["locNumber"], entry["locStation"], entry["fillColor"], entry["strokeColor"]))

# Commit changes and close the connection
conn.commit()
conn.close()
