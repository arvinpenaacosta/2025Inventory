from netmiko import ConnectHandler
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# Pydantic models
class FormData(BaseModel):
    station: str
    port: str
    interface: str
    floor: str
    info1: str
    info2: str
    trans_time: str
    alterby: str

# Model for each row
class Row(BaseModel):
    station: str
    port: str
    interface: str
    floor: str
    info2: str

# Model for the VLAN change request
class ChangeVlanRequest(BaseModel):
    rows: List[Row]
    vlan: str
    customValue: Optional[str] = None
    username: str
    password: str

# Model for the VOICE change request
class ChangeVoiceRequest(BaseModel):
    rows: List[Row]
    voice: str
    customValue: Optional[str] = None
    username: str
    password: str

class RequestData(BaseModel):
    rows: list
    username: str
    password: str

class RowUpdate(BaseModel):
    id:int
    station: str
    port: str
    interface: str
    info2: str
    floor: str


# NetworkDeviceManager class definition
class NetworkDeviceManager:
    base_ip = "10.16.0."

    def __init__(self, username: str, password: str, base_ip: str = None):
        self.username = username
        self.password = password
        self.log_file = "log_file.txt"  # Log file path
        
        self.connection = None
        self.current_ip = None
        if base_ip:
            self.base_ip = base_ip

    def connect(self, port: str):
        ip = f"{self.base_ip}{port}"
        
        if ip != self.current_ip:
            if self.connection:
                print(f"\n📴 Cleaning up before switching from {self.current_ip}")
                try:
                    self.connection.send_command("end")
                except Exception as e:
                    print(f"⚠️ Could not send 'end' to {self.current_ip}: {e}")
                self.connection.disconnect()
                self.connection = None
                self.current_ip = None
            

            print(f"\n🔌 Connecting : {self.username}@{ip}...")
            try:
                self.connection = ConnectHandler(
                    device_type='cisco_ios',
                    ip=ip,
                    username=self.username,
                    password=self.password
                )
                self.current_ip = ip
                print(f"✅ Connected to {ip}")
            except Exception as e:
                print(f"❌ Failed to connect : {self.username}@{ip}: {e}")
                print(f"❌ ==============================================================")
                self.connection = None
                return str(e)
        
        return self.connection


    # Log Transactions  ++++++++++++++++++++++++++++++++++++++++++++++
    def log(self, message: str):
        with open(self.log_file, "a") as f:
            f.write(f"{message}\n")

    # CLEAR PORT  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CLEAR PORT SECURITY 🔥
    def process_and_clear_ports(self, rows: List[dict]):
        results = []
        last_ip = None
        
        for row in rows:
            ip = f"{self.base_ip}{row['port']}"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"[{timestamp} | {self.username} | Clear Port] {row['floor']} | {row['station']} | {row['port']} | {row['interface']} | {row['info2']}")
            
            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to new device
                error = self.connect(row['port'])
                if error:
                    results.append({"device": ip, "status": f"❌ Connection failed: {error}"})
                    continue
                last_ip = ip
            
            # Clear interface directly (inline implementation of clear_interface)
            interface = row['interface']
            if not self.connection:
                results.append({"device": ip, "interface": interface, "status": "⚠️ No active connection."})
                continue
                
            print(f"⚡ Clearing {interface} configuration...")
            commands = [
                f"interface {interface}",
                "shutdown",
                "no shutdown"
            ]

            output = self.connection.send_config_set(commands)
            print(f"✔️ Port {interface} cleared successfully.")
            
            results.append({"device": ip, "interface": interface, "status": output})
        
        # ✅ Final cleanup after all rows are processed
        if self.connection:
            self.connection.send_command("end")  # Exits config mode (if applicable)

            print(f"\n🔌 Disconnecting from {self.current_ip}")
            self.connection.disconnect()
            self.connection = None
        
        return results


    # CLEAR PORT STICKY  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CLEAR STICKY PORT 🔥
    def process_and_clear_sticky_interface(self, rows: List[dict]):
        results = []
        last_ip = None

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            interface = row['interface']

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"[{timestamp} | {self.username} | Clear Sticky] {row['floor']} | {row['station']} | {row['port']} | {row['interface']} | {row['info2']}")
            
            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to the new device
                error = self.connect(row['port'])
                if error:
                    results.append({"device": ip, "status": f"❌ Connection failed: {error}"})
                    continue
                last_ip = ip
            
            # If no active connection, skip the interface processing
            if not self.connection:
                results.append({"device": ip, "interface": interface, "status": "⚠️ No active connection."})
                continue
            
            # ⚠️ Clear sticky MAC address (Step 1)
            print(f"⚡ Clearing sticky MAC address on {interface}...")
            self.connection.send_command(f"clear port-security sticky interface {interface}")
            print(f"✔️ Sticky MAC address cleared on {interface}.")
            
            # ⚠️ Apply Shutdown & No Shutdown commands (Step 2)
            print(f"⚡ Reapplying configuration on {interface}...")
            config_commands = [
                f"interface {interface}",
                "shutdown",
                "no shutdown"
            ]

            try:
                output = self.connection.send_config_set(commands)
                print(f"✔️ Configuration applied to {interface} successfully - Clear Sticky.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": output
                })
            except Exception as e:
                # Handle any command failure
                print(f"❌ Failed Configuration applied to {interface} - Clear Sticky.")
                print(f"❌ ==============================================================")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": f"❌ Command failure: {str(e)}"
                })


        # ✅ Final cleanup after all rows are processed
        if self.connection:
            self.connection.send_command("end")  # Exits config mode (if applicable)

            print(f"\n🔌 Disconnecting from {self.current_ip}")
            self.connection.disconnect()
            self.connection = None
        
        return results


    # CHANGE VLAN  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CHANGE VLAN 🔥
    def process_and_changeVlans(self, rows: list, vlan: str):
        results = []
        last_ip = None  # Track the previous IP

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"[{timestamp} | {self.username} | Change VLAN] {row['floor']} | {row['station']} | {row['port']} | {row['interface']} | {row['info2']}")

            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from the previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from previous device {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to the new device
                if not self.connect(row['port']):
                    results.append({
                        "device": ip,
                        "interface": row['interface'],
                        "status": "❌ Connection failed."
                    })
                    continue  # Skip to the next row if connection fails
                last_ip = ip  # Update to the current IP
            
            # Proceed with changing the VLAN for the current interface
            interface = row['interface']
            print(f"⚡ Changing VLAN for interface {interface} to vlan {vlan}")
            commands = [
                f"interface {interface}",
                f"switchport access vlan {vlan}",
                "shutdown",
                "no shutdown"
            ]

            try:
                output = self.connection.send_config_set(commands)
                print(f"✔️ VLAN {vlan} applied to interface {interface} successfully.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": output
                })
            except Exception as e:
                # Handle any command failure
                print(f"❌ Failed to apply VLAN {vlan} to interface {interface}: {str(e)}")
                print(f"❌ ==============================================================")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": f"❌ Command failure: {str(e)}"
                })
        
        # ✅ Final cleanup after all rows are processed
        if self.connection:
            try:
                self.connection.send_command("end")  # Exits config mode (if applicable)
                print(f"\n🔌 Disconnecting from {self.current_ip}")
            except Exception as e:
                print(f"⚠️ Could not send 'end' command: {str(e)}")

            # Disconnect from the last device
            self.connection.disconnect()
            self.connection = None

        return results


    # CHANGE VOICE  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CHANGE VOICE 🔥
    def process_and_changeVoices(self, rows: list, voice: str):
        results = []
        last_ip = None  # Track the previous IP

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"[{timestamp} | {self.username} | Change Voice] {row['floor']} | {row['station']} | {row['port']} | {row['interface']} | {row['info2']}")

            # Check if we need to connect to a new device
            if ip != last_ip:
                # Disconnect from the previous device if connected
                if self.connection:
                    print(f"\n🔌 Disconnecting from previous device {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None
                
                # Connect to the new device
                if not self.connect(row['port']):
                    results.append({
                        "device": ip,
                        "interface": row['interface'],
                        "status": "❌ Connection failed."
                    })
                    continue  # Skip to the next row if connection fails
                last_ip = ip  # Update to the current IP
            
            # Proceed with changing the VOICE for the current interface
            interface = row['interface']
            print(f"⚡ Changing VOICE for interface {interface} to voice {voice}")
            commands = [
                f"interface {interface}",
                f"switchport voice vlan {voice}",
                "shutdown",
                "no shutdown"
            ]

            try:
                output = self.connection.send_config_set(commands)
                print(f"✔️ VOICE {voice} applied to interface {interface} successfully.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": output
                })
            except Exception as e:
                # Handle any command failure
                print(f"❌ Failed to apply VOICE VLAN {voice} to interface {interface}: {str(e)}")
                print(f"❌ ==============================================================")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": f"❌ Command failure: {str(e)}"
                })
        
        # ✅ Final cleanup after all rows are processed
        if self.connection:
            try:
                self.connection.send_command("end")  # Exits config mode (if applicable)
                print(f"\n🔌 Disconnecting from {self.current_ip}")
            except Exception as e:
                print(f"⚠️ Could not send 'end' command: {str(e)}")

            # Disconnect from the last device
            self.connection.disconnect()
            self.connection = None

        return results
    


    def get_interface_vlan(self, port: str, interface: str):
        # Construct the device IP address
        ip = f"{self.base_ip}{port}"
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log(f"[{timestamp} | {self.username} | Check VLAN] {port} | {interface}")
        
        try:
            # Connect to the device using the class's connect method
            error = self.connect(port)
            if error:
                return f"❌ Connection failed: {error}"
            
            if not self.connection:
                return "⚠️ No active connection."
            
            # Execute the command to check interface switchport status
            print(f"🔍 Checking VLAN status on {interface}...")
            command = f"show interfaces {interface} switchport | include Access Mode VLAN"
            output = self.connection.send_command(command).strip()
            
            # Process the output to extract VLAN information
            if output:
                import re
                match = re.search(r"Access Mode VLAN: (\d+)", output)
                if match:
                    vlan = match.group(1)
                    print(f"✔️ Interface {interface} is on VLAN {vlan}")
                    return f"Interface {interface} is on VLAN {vlan}"
                else:
                    print(f"⚠️ Could not parse VLAN information")
                    return f"Could not parse VLAN information from output: {output}"
            else:
                print(f"⚠️ No access VLAN information found")
                return f"No access VLAN information found for interface {interface}"
                
        except Exception as e:
            print(f"❌ Error checking VLAN: {str(e)}")
            return f"Error occurred: {str(e)}"
        finally:
            # Note: Not disconnecting here as other methods in the class
            # manage connections across multiple operations
            pass

    def process_showVlan(self, row):
        """
        Process a single row to retrieve VLAN information from a device
        
        Args:
            row (dict): Row data from frontend containing port and interface info
        
        Returns:
            dict: Result of the VLAN check operation
        """
        # Log the row received from frontend
        print(f"⚡ Received request to check VLAN for: {row}")
        
        # Extract necessary information from the row
        port = row.get('port')
        interface = row.get('interface')
        
        if not port or not interface:
            return {
                "status": "❌ Error: Missing port or interface information in row data",
                "row": row
            }
        
        # Use the existing get_interface_vlan method to retrieve VLAN info
        result = self.get_interface_vlan(port, interface)
        
        # Format the response for the frontend
        response = {
            "device": f"{self.base_ip}{port}",
            "interface": interface,
            "status": result
        }
        
        # Include additional information that might be useful for the frontend
        if 'station' in row:
            response['station'] = row['station']
        if 'floor' in row:
            response['floor'] = row['floor']
        if 'info2' in row:
            response['info2'] = row['info2']
        
        return response   
    
    # ✅🔥 SHOW VLAN STATUS 🔥
    def xprocess_show_vlan_status(self, rows: List[dict]):
        results = []
        last_ip = None

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            interface = row['interface']

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log(f"[{timestamp} | {self.username} | Show VLAN] {row['floor']} | {row['station']} | {row['port']} | {row['interface']} | {row['info2']}")


            # Check if we need to connect to a new device
            if ip != last_ip:
                if self.connection:
                    print(f"\n🔌 Disconnecting from {self.current_ip}")
                    self.connection.disconnect()
                    self.connection = None

                # Connect to the new device
                error = self.connect(row['port'])
                if error:
                    results.append({
                        "device": ip,
                        "interface": interface,
                        "status": f"❌ Connection failed: {error}"
                    })
                    continue
                last_ip = ip

            # If still no connection
            if not self.connection:
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": "⚠️ No active connection."
                })
                continue

            # ✅ Show VLAN assignment on this interface
            try:
                print(f"🔍 Checking VLAN status on {interface}...")
                command = f"show interfaces {interface} switchport | include Access Mode VLAN"
                output = self.connection.send_command(command).strip()

                if output:
                    print(f"✔️ {interface}: {output}")
                    results.append({
                        "device": ip,
                        "interface": interface,
                        "status": output
                    })
                else:
                    print(f"⚠️ {interface}: No VLAN info found.")
                    results.append({
                        "device": ip,
                        "interface": interface,
                        "status": "⚠️ No VLAN info returned."
                    })

            except Exception as e:
                print(f"❌ Failed to check VLAN on {interface}")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": f"❌ Command error: {str(e)}"
                })

        # Cleanup
        if self.connection:
            self.connection.send_command("end")
            print(f"\n🔌 Disconnecting from {self.current_ip}")
            self.connection.disconnect()
            self.connection = None

        return results

