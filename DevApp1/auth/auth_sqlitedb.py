import sqlite3
import os
import bcrypt  # Import bcrypt for password hashing

# Get the absolute path of the db folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the directory of this script
DB_PATH = os.path.join(BASE_DIR, "../db/epmap.db")  # Move up one level, then into db/

# Resolve absolute path
DB_NAME = os.path.abspath(DB_PATH)  
print(f"Database Path: {DB_NAME}")  # Debugging step

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME)


def authenticate_user(login_name: str, password: str) -> bool:
    """Authenticates a user from the users table without hashing."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch user from database
    cursor.execute("SELECT password, status FROM users WHERE login_name = ?", (login_name,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password, status = user
        if status == "active" and password == stored_password:
            return True

    return False




def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def authenticate_Xuser(login_name: str, password: str) -> bool:
    """Authenticates a user from the users table using bcrypt."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch user from database
    cursor.execute("SELECT password, status FROM users WHERE login_name = ?", (login_name,))
    user = cursor.fetchone()
    conn.close()

    if user:
        stored_password, status = user
        if status == "active" and bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
            return True

    return False