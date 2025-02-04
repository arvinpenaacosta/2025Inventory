from ldap3 import Server, Connection, ALL
from netmiko import ConnectHandler


# Define LDAP server details and base OU
LDAP_SERVER = "ldap://winserver2022.devapp.local:389"
BASE_OU = "OU=IT_NOC,DC=devapp,DC=local"

#LDAP_SERVER = "ldap://ADDC1S.eperformax.com:389"
#BASE_OU = "OU=Support,OU=IT Division,DC=eperformax,DC=com"

# Toggle between live and dummy authentication
USE_LIVE_AUTH = False  # Set to True for live authentication, False for dummy authentication

# Environment variable to toggle between live and dummy mode
# USE_LIVE_AUTH = os.getenv("USE_LIVE_AUTH", "False").lower() == "true"



def authenticate(username, password):
    """
    Authenticates a user either through a live connection to the domain or a dummy connection.
    The method used is determined by the `USE_LIVE_AUTH` setting.
    """
    if USE_LIVE_AUTH:
        # LIVE Connection to DOMAIN
        return authenticate_live(username, password)
    else:
        # Dummy Connection
        return authenticate_dummy(username, password)

def authenticate_live(username, password):
    """Attempts to authenticate a user within a specific OU."""
    user_dn = f"CN={username},{BASE_OU}"
    server = Server(LDAP_SERVER, get_info=ALL)
    try:
        conn = Connection(server, user=user_dn, password=password)
        if conn.bind():
            conn.unbind()
            return True
        return False
    except Exception as e:
        # Catch all exceptions and provide a generic error message
        return "Can't connect to server to validate user or an unexpected error occurred."

def authenticate_dummy(username, password):
    # Hardcoded credentials for testing
    fixed_username = "admin"
    fixed_password = "123456"
    
    # Check if provided credentials match the fixed ones
    if username == fixed_username and password == fixed_password:
        return True
    else:
        return False



def authenticate_netmiko(username, password):
    device = {
        'device_type': 'cisco_ios',
        'ip': "10.16.0.80",
        'username': username,
        'password': password,
    }

    print(f"Username: {username}")
    print(f"Password: {password}")

    try:
        print("Connecting to the device...")
        connection = ConnectHandler(**device)
        print("Connected successfully.")
        return True
    except Exception as e:
        print(f"Failed to connect to the device: {e}")
        return False