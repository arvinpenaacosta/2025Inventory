import bcrypt

# Given hash and password
stored_hash = b"$2b$12$pWyLXPBKhO5jtTGBvCkAiO2B0VrzdD05t29nmy9uGcsWRo0Zk4/9K"
password_to_check = "!@#$1qaZ"

# Check if the password matches the hash
if bcrypt.checkpw(password_to_check.encode('utf-8'), stored_hash):
    print("Password matches")
else:
    print("Password does not match")
