from authentication import authenticate, authenticate_netmiko  # Import the authenticate function
#import getpass
import pwinput as pin

# Prompt the user for their credentials
username = input("Enter your username (e.g., user1): ")

#password = getpass.getpass("Enter your password: ")
password = pin.pwinput(prompt = 'Enter your password: ', mask='#')


# Call the authenticate function and check the result
#if authenticate(username, password):           # Use this for LDAP Authentication
if authenticate_netmiko(username, password):    # Use this for Cisco Netmiko Authentication
    print("Login successful")
else:
    print("Login failed")
