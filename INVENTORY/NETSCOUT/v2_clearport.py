from netmiko import ConnectHandler
import time


class ClearPortClass:
    """Class to clear port configurations on a Cisco switch."""

    def __init__(self, ip, username, password):
        """Initialize connection details."""
        self.ip = ip
        self.username = username
        self.password = password
        self.device = {
            'device_type': 'cisco_ios',
            'ip': ip,
            'username': username,
            'password': password,
        }
        self.connection = None

    def connect(self):
        """Establishes a connection to the switch."""
        try:
            print(f"🔌 Connecting to {self.ip}...")
            self.connection = ConnectHandler(**self.device)
            print("✅ Connected successfully.")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            self.connection = None

    def disconnect(self):
        """Closes the connection to the switch."""
        if self.connection:
            self.connection.disconnect()
            print("🔌 Disconnected from the device.")
        else:
            print("⚠️ No active connection to disconnect.")

    def execute_commands(self, commands):
        """Executes a list of configuration commands."""
        if not self.connection:
            print("❗ No active connection.")
            return None

        try:
            print("⚙️ Sending configuration commands...")
            output = self.connection.send_config_set(commands)
            print(output)
            self.connection.send_command("end")
            return output
        except Exception as e:
            print(f"❌ Failed to execute commands: {e}")
            return None

    def clearportsmultiple(self, rows):
        """
        Loops through rows and clears each port.
        Reconnects to the device when the port changes.
        """
        previous_port = None  # Keep track of the previous port

        # ✅ Loop here Top ==========================================================
        for idx, row in enumerate(rows, start=1):
            port = row.get("port", "N/A")
            interface = row.get("interface", "N/A")

            if interface == "N/A" or port == "N/A":
                print(f"⚠️ Skipping row {idx}: Missing port or interface.")
                continue  # Skip invalid rows

            # Check if the port has changed
            if port != previous_port:
                # Disconnect from the previous device if switching ports
                if previous_port is not None:
                    print("\n🔌 Port change detected. Reconnecting with new device...")
                    self.disconnect()

                # Reconnect with new port (new instance)
                print(f"🔌 Connecting with new port: {port}")

                self.ip = f"10.16.0.{port}"  # Modify IP for the new port
                
                self.device['ip'] = self.ip
                self.connect()

                if not self.connection:
                    print(f"❌ Failed to connect to port {port}. Skipping row.")
                    continue  # Skip this row if connection fails

            print("\n" + "-" * 50)  # Separator line for readability
            print(f"🔹 Processing Row {idx}")
            print(f"➡️  Port: {port}, Interface: {interface}")

            # Commands to clear the port
            commands = [
                f"interface {interface}",
                "shutdown",
                "no shutdown",
                "exit",
            ]

            # Execute the commands
            self.execute_commands(commands)     # Execute the Netmiko Cisco Command

            print(f"✅ Port {port} on {interface} cleared successfully.")
            
            # Update previous port to current port
            previous_port = port
            
            time.sleep(2)  # Delay between rows
        # ✅ Loop here Buttom ==========================================================


        # Disconnect after all rows are processed
        self.disconnect()


# ✅ Example usage:
if __name__ == "__main__":
    # Replace with your switch credentials
    username = "admin"
    password = "password"

    # Sample rows
    rows = [
        {"Station": "P-456", "Port": "80", "Interface": "G1/0/28", "Floor": "P2", "Info2": "Washington"},
        {"Station": "P-457", "Port": "80", "Interface": "G1/0/29", "Floor": "P3", "Info2": "New York"},   # Same port as previous
        {"Station": "P-458", "Port": "90", "Interface": "G1/0/30", "Floor": "P4", "Info2": "Los Angeles"}, # New port -> reconnect
        {"Station": "P-459", "Port": "90", "Interface": "G1/0/31", "Floor": "P5", "Info2": "Chicago"},    # Same port as previous
        {"Station": "P-460", "Port": "100", "Interface": "G1/0/32", "Floor": "P6", "Info2": "Miami"}      # New port -> reconnect
    ]

    # Create an instance of ClearPortClass
    port_clearer = ClearPortClass(f"10.16.0.{rows[0]['port']}", username, password)

    # Clear multiple ports
    print("\n🔁 Looping through multiple rows...")
    port_clearer.clearportsmultiple(rows)
