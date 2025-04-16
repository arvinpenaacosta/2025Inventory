from netmiko import ConnectHandler
from typing import List, Optional
from pydantic import BaseModel

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

# NetworkDeviceManager class definition
class NetworkDeviceManager:
    base_ip = "10.16.0."

    def __init__(self, username: str, password: str, base_ip: str = None):
        self.username = username
        self.password = password
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


    # CLEAR PORT  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CLEAR PORT SECURITY 🔥
    def process_and_clear_ports(self, rows: List[dict]):
        results = []
        last_ip = None  # Track the previous IP

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            
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
            
            # Proceed with clear port for the current interface
            interface = row['interface']
            print(f"⚡ Clear Port for interface {interface}")
            commands = [
                f"interface {interface}",
                "shutdown",
                "no shutdown"
            ]

            try:
                output = self.connection.send_config_set(commands)
                print(f"✔️ Clear Port applied to interface {interface} successfully.")
                results.append({
                    "device": ip,
                    "interface": interface,
                    "status": output
                })
            except Exception as e:
                # Handle any command failure
                print(f"❌ Failed to Clear Port to interface {interface}: {str(e)}")
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

    # CLEAR PORT STICKY  ++++++++++++++++++++++++++++++++++++++++++++++
    # ✅🔥 PROCESS AND CLEAR STICKY PORT 🔥
    def process_and_clear_sticky_interface(self, rows: List[dict]):
        results = []
        last_ip = None

        for row in rows:
            ip = f"{self.base_ip}{row['port']}"
            interface = row['interface']
            
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
            

            interface = row['interface']      
            # ⚠️ Clear sticky MAC address (Step 1)
            print(f"⚡ Clearing sticky MAC address on {interface}...")
            self.connection.send_command(f"clear port-security sticky interface {interface}")
            print(f"✔️ Sticky MAC address cleared on {interface}.")
            
            # Proceed with clear port for the current interface
            print(f"⚡ Clear Port for interface {interface}")
            commands = [
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
            self.connection = Nonee

        return results
