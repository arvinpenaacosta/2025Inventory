# system_info_module.py 

import os
import socket
import winreg
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Tuple
import psutil
import wmi
from tabulate import tabulate

@dataclass
class SystemInfo:
    log_user: str
    hostname: str
    serial_number: str
    processor: str
    windows_version: str
    windows_display_version: str
    manufacturer: str
    model: str
    total_ram: str
    num_ram_slots: int
    ram_per_slot: str
    ram_speed: str
    ram_type: str
    ip_address: str
    mac_address: str
    citrix_name: str
    citrix_version: str
    timestamp: str

class SystemInfoCollector:
    RAM_TYPE_MAP = {20: "DDR", 21: "DDR2", 24: "DDR3", 26: "DDR4", 29: "DDR5"}

    def __init__(self):
        self.wmi_client = wmi.WMI()

    def collect(self) -> SystemInfo:
        user = os.getenv("USERNAME", "Unknown")

        cs_info = list(self.wmi_client.Win32_ComputerSystem())
        hostname = cs_info[0].Name if cs_info else "Unknown"
        manufacturer = cs_info[0].Manufacturer if cs_info else "Unknown"
        model = cs_info[0].Model if cs_info else "Unknown"

        bios_info = list(self.wmi_client.Win32_BIOS())
        serial_number = bios_info[0].SerialNumber if bios_info else "Unknown"

        proc_info = list(self.wmi_client.Win32_Processor())
        processor = proc_info[0].Name if proc_info else "Unknown"

        os_info = list(self.wmi_client.Win32_OperatingSystem())
        windows_version = os_info[0].Caption if os_info else "Unknown"

        windows_display_version = self.get_display_version()
        citrix_name, citrix_version = self.get_citrix_info()

        ram_info = list(self.wmi_client.Win32_PhysicalMemory())
        total_ram = 0
        ram_capacities = []
        ram_speed = "Unknown"
        ram_type = "Unknown"
        num_slots = len(ram_info)

        for ram in ram_info:
            try:
                capacity = int(ram.Capacity) if ram.Capacity else 0
                capacity_gb = float(capacity) / (1024 * 1024 * 1024)
                total_ram += capacity
                ram_capacities.append(f"{capacity_gb:.2f} GB")
            except (ValueError, TypeError):
                ram_capacities.append("Unknown GB")

            try:
                speed = int(ram.Speed) if ram.Speed else 0
                if speed > 0:
                    ram_speed = f"{speed} MHz"
            except (ValueError, TypeError):
                pass

            try:
                memory_type = int(ram.SMBIOSMemoryType) if ram.SMBIOSMemoryType else 0
                if memory_type > 0:
                    ram_type = self.RAM_TYPE_MAP.get(memory_type, "Unknown")
            except (ValueError, TypeError):
                pass

        total_ram_gb = float(total_ram) / (1024 * 1024 * 1024)
        total_ram_str = f"{total_ram_gb:.2f} GB"
        ram_per_slot = " > ".join(ram_capacities) if ram_capacities else "Unknown"

        ip_address, mac_address = self.get_ip_and_mac()

        utc_now = datetime.now(timezone.utc)
        local_time = utc_now + timedelta(hours=8)
        timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")

        return SystemInfo(
            log_user=user,
            hostname=hostname,
            serial_number=serial_number,
            processor=processor,
            windows_version=windows_version,
            windows_display_version=windows_display_version,
            manufacturer=manufacturer,
            model=model,
            total_ram=total_ram_str,
            num_ram_slots=num_slots,
            ram_per_slot=ram_per_slot,
            ram_speed=ram_speed,
            ram_type=ram_type,
            ip_address=ip_address,
            mac_address=mac_address,
            citrix_name=citrix_name,
            citrix_version=citrix_version,
            timestamp=timestamp
        )

    def get_display_version(self) -> str:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                0,
                winreg.KEY_READ
            )
            value, _ = winreg.QueryValueEx(key, "DisplayVersion")
            winreg.CloseKey(key)
            return value
        except (FileNotFoundError, OSError):
            return "Unknown"

    def get_citrix_info(self) -> Tuple[str, str]:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
                0,
                winreg.KEY_READ
            )
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)

                    try:
                        display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        if "Citrix Workspace" in display_name:
                            display_version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                            winreg.CloseKey(subkey)
                            winreg.CloseKey(key)
                            return display_name, display_version
                    except FileNotFoundError:
                        pass

                    winreg.CloseKey(subkey)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except (FileNotFoundError, OSError):
            pass

        return "Not found", "Not found"

    def get_ip_and_mac(self) -> Tuple[str, str]:
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for interface_name, addresses in interfaces.items():
                if interface_name.lower().startswith('loopback'):
                    continue
                if interface_name in stats and stats[interface_name].isup:
                    ipv4_addr = None
                    mac_addr = None
                    for addr in addresses:
                        if addr.family == socket.AF_INET:
                            ipv4_addr = addr.address
                        elif addr.family == psutil.AF_LINK:
                            mac_addr = addr.address
                    if ipv4_addr and mac_addr and ipv4_addr != '127.0.0.1':
                        mac_clean = mac_addr.replace(':', '').replace('-', '').lower()
                        if len(mac_clean) == 12:
                            formatted_mac = f"{mac_clean[0:4].upper()}.{mac_clean[4:8].upper()}.{mac_clean[8:12].upper()}"
                            return ipv4_addr, formatted_mac
        except Exception:
            pass
        return "Not found", "Not found"


def print_system_info_grid(info: SystemInfo):
    data = [
        ["Log User", info.log_user],
        ["Hostname", info.hostname],
        ["Serial Number", info.serial_number],
        ["Processor", info.processor],
        ["OS Version", info.windows_version],
        ["Display Version", info.windows_display_version],
        ["Manufacturer", info.manufacturer],
        ["Model", info.model],
        ["Total RAM", info.total_ram],
        ["Number of RAM Slots", info.num_ram_slots],
        ["RAM per Slot", info.ram_per_slot],
        ["RAM Speed", info.ram_speed],
        ["RAM Type", info.ram_type],
        ["IP Address", info.ip_address],
        ["MAC Address", info.mac_address],
        ["Citrix Name", info.citrix_name],
        ["Citrix Version", info.citrix_version],
        ["Timestamp", info.timestamp],
    ]
    os.system("cls")
    # print(tabulate(data, headers=["Field", "Value"], tablefmt="simple"))
    
    # Also print JSON below the grid
    json_result = json.dumps(asdict(info), indent=2)
    # print("\nJSON Result:")
    # print(json_result)

if __name__ == "__main__":
    try:
        collector = SystemInfoCollector()
        system_info = collector.collect()

        #print_system_info_grid(system_info)
        print("✅ [system_info_module.py] System information collected and stored in memory\n")        
    except Exception as e:
        print(f"Error collecting system information: {e}")

