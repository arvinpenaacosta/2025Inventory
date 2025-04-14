#!/usr/bin/env python3

from netmiko import ConnectHandler
import re
import sys

def get_interface_vlan(device_ip, interface, device_type="cisco_ios"):
    """
    Connect to a network device and retrieve the VLAN for a specific interface
    
    Args:
        device_ip (str): IP address of the network device
        interface (str): Interface name to check (e.g., 'GigabitEthernet0/1')
        device_type (str): Device type for Netmiko connection
        
    Returns:
        str: VLAN number or error message
    """
    username = "a.acosta"
    password = "MS043ms-64.,"

    # Define device connection parameters
    device = {
        'device_type': 'cisco_ios',
        'ip': device_ip,
        'username': username,
        'password': password,
    }
    
    try:
        # Establish connection to the device
        print(f"\nConnecting to {device_ip}...")
        connection = ConnectHandler(**device)
        
        # Execute the command to check interface switchport status
        command = f"show interfaces {interface} switchport | include Access"
        print(f"Executing command: {command}")
        output = connection.send_command(command)
        
        # Close the connection
        connection.disconnect()
        
        # Process the output to extract VLAN information
        if "Access Mode VLAN:" in output:
            # Use regex to extract the VLAN number
            match = re.search(r"Access Mode VLAN: (\d+)", output)
            if match:
                vlan = match.group(1)
                return f"Interface {interface} is on VLAN {vlan}"
            else:
                return f"Could not parse VLAN information from output: {output}"
        else:
            return f"No access VLAN information found for interface {interface}. Output: {output}"
            
    except Exception as e:
        return f"Error occurred: {str(e)}"



if __name__ == "__main__":
    # Check if command line arguments are provided
    if len(sys.argv) < 3:
        print("Usage: python script.py <device_suffix> <interface>")
        print("Example: python script.py 1 GigabitEthernet0/1")
        sys.exit(1)
    
    # Get parameters from command line arguments
    base_ip = "10.16.0."
    device_suffix = sys.argv[1]
    interface = sys.argv[2]
    
    # Execute the function and print the result
    result = get_interface_vlan(f"{base_ip}{device_suffix}", interface)
    print(result)
