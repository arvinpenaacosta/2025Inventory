import bcrypt
import sys

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password  # Return as bytes, no need to decode to UTF-8

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <password>")
        sys.exit(1)
    
    password = sys.argv[1]
    hashed = hash_password(password)
    print(f"Hashed Password: {hashed.decode('utf-8')}")  # Decode for printing only
