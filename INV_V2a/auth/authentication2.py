from ldap3 import Server, Connection, ALL

# Define LDAP server details and base OU
LDAP_SERVER = "ldap://winserver2022.devapp.local:389"
BASE_OU = "OU=IT_NOC,DC=devapp,DC=local"
USE_LIVE_AUTH = True  # Toggle between live and dummy authentication

def authenticate(username, password):
    if USE_LIVE_AUTH:
        return live_authenticate(username, password)
    else:
        return dummy_authenticate(username, password)

def live_authenticate(username, password):
    user_dn = f"CN={username},{BASE_OU}"
    server = Server(LDAP_SERVER, get_info=ALL)
    try:
        conn = Connection(server, user=user_dn, password=password)
        if conn.bind():
            conn.unbind()
            return "True"  # Return "True" on successful authentication
        return "False"
    except Exception as e:
        return "False"

def dummy_authenticate(username, password):
    fixed_username = "admin"
    fixed_password = "123456"
    if username == fixed_username and password == fixed_password:
        return "True"
    else:
        return "False"

# Main script to authenticate
import sys
username = sys.argv[1]
password = sys.argv[2]
result = authenticate(username, password)
print(result)
