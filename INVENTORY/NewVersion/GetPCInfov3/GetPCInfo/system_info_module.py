# system_info_module.py (updated version with separated Citrix and Office columns)

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
    windows_install_date: str
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
    office_name: str
    office_version: str
    total_hdd_capacity: str
    drive_types: str
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
        
        # Get Windows installation date
        windows_install_date = self.get_windows_install_date()

        # Get Citrix and Office information separately
        citrix_name, citrix_version = self.get_citrix_info()
        office_name, office_version = self.get_office_info()

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

        # Collect hard drive information
        total_hdd_capacity, drive_types = self.get_hdd_info()

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
            windows_install_date=windows_install_date,
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
            office_name=office_name,
            office_version=office_version,
            total_hdd_capacity=total_hdd_capacity,
            drive_types=drive_types,
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

    def get_windows_install_date(self) -> str:
        try:
            # Open the registry key
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
                0,
                winreg.KEY_READ
            )
            
            # Read the InstallDate value (stored as Unix timestamp)
            install_date_timestamp, _ = winreg.QueryValueEx(key, "InstallDate")
            
            # Convert Unix timestamp to readable date (YYYY-MM-DD format)
            install_date = datetime.fromtimestamp(install_date_timestamp)
            install_date_str = install_date.strftime("%Y-%m-%d")
            
            # Close the registry key
            winreg.CloseKey(key)
            
            return install_date_str
            
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

    def get_office_info(self) -> Tuple[str, str]:
        """
        Retrieve MS Office information from multiple registry locations
        """
        office_found = False
        office_name = "Not found"
        office_version = "Not found"
        
        # Registry paths to check for Office installations
        registry_paths = [
            # Standard uninstall entries (both 64-bit and 32-bit)
            r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
            r"SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
            # Direct Office registry keys
            r"SOFTWARE\\Microsoft\\Office",
            r"SOFTWARE\\WOW6432Node\\Microsoft\\Office"
        ]
        
        # Method 1: Check uninstall entries for Office installations
        for reg_path in registry_paths[:2]:  # Only uninstall paths
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)

                        try:
                            display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                            display_name_lower = display_name.lower()
                            
                            # Look for various Office product names
                            office_indicators = [
                                "microsoft office professional",
                                "microsoft office standard",
                                "microsoft office home",
                                "microsoft office personal",
                                "microsoft 365",
                                "office 365",
                                "microsoft office 365",
                                "office professional",
                                "office standard",
                                "office home"
                            ]
                            
                            for indicator in office_indicators:
                                if indicator in display_name_lower and not office_found:
                                    try:
                                        display_version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                                        office_name = display_name
                                        office_version = display_version
                                        office_found = True
                                        break
                                    except FileNotFoundError:
                                        # Try to get version from display name if DisplayVersion is not available
                                        version_keywords = ["2019", "2021", "2016", "2013", "365"]
                                        for keyword in version_keywords:
                                            if keyword in display_name:
                                                office_name = display_name
                                                office_version = f"Office {keyword}"
                                                office_found = True
                                                break
                                        
                        except FileNotFoundError:
                            pass

                        winreg.CloseKey(subkey)
                        i += 1
                        
                        if office_found:
                            break
                            
                    except OSError:
                        break
                        
                winreg.CloseKey(key)
                
                if office_found:
                    break
                    
            except (FileNotFoundError, OSError):
                continue
        
        # Method 2: If not found in uninstall entries, check Office-specific registry keys
        if not office_found:
            try:
                # Check for Office version in the Office registry key
                office_versions = ["16.0", "15.0", "14.0", "12.0"]  # 2019/2016/365, 2013, 2010, 2007
                version_names = {
                    "16.0": "Office 2016/2019/365",
                    "15.0": "Office 2013", 
                    "14.0": "Office 2010",
                    "12.0": "Office 2007"
                }
                
                for version in office_versions:
                    try:
                        key_path = f"SOFTWARE\\Microsoft\\Office\\{version}\\Common\\InstallRoot"
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
                        
                        # If we can open this key, Office is installed
                        try:
                            path, _ = winreg.QueryValueEx(key, "Path")
                            if path and os.path.exists(path):
                                office_name = f"Microsoft {version_names[version]}"
                                office_version = version
                                office_found = True
                                winreg.CloseKey(key)
                                break
                        except FileNotFoundError:
                            # Key exists but no Path value, still indicates Office installation
                            office_name = f"Microsoft {version_names[version]}"
                            office_version = version
                            office_found = True
                            
                        winreg.CloseKey(key)
                        
                        if office_found:
                            break
                            
                    except (FileNotFoundError, OSError):
                        continue
                        
            except (FileNotFoundError, OSError):
                pass
        
        # Method 3: Check for specific Office applications if main Office suite not found
        if not office_found:
            app_paths = [
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\WINWORD.EXE",
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\EXCEL.EXE",
                r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\POWERPNT.EXE"
            ]
            
            for app_path in app_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, app_path, 0, winreg.KEY_READ)
                    path, _ = winreg.QueryValueEx(key, "")
                    if path and os.path.exists(path):
                        office_name = "Microsoft Office (Individual Apps)"
                        office_version = "Detected"
                        office_found = True
                        winreg.CloseKey(key)
                        break
                    winreg.CloseKey(key)
                except (FileNotFoundError, OSError):
                    continue
        
        return office_name, office_version

    def get_ip_and_mac(self) -> Tuple[str, str]:
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            
            # Storage for different priority levels of addresses
            priority_1_result = None  # For 10.x.x.x addresses (highest priority)
            priority_2_result = None  # For 172.x.x.x addresses (medium priority)
            priority_3_result = None  # For 192.x.x.x addresses (lower priority)
            fallback_result = None    # For any other valid addresses (lowest priority)
            
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
                            
                            # Priority 1: 10.x.x.x addresses (corporate networks)
                            if ipv4_addr.startswith('10.'):
                                priority_1_result = (ipv4_addr, formatted_mac)
                            # Priority 2: 172.x.x.x addresses (private networks)
                            elif ipv4_addr.startswith('192.') and priority_2_result is None:
                                priority_2_result = (ipv4_addr, formatted_mac)
                            # Priority 3: 192.x.x.x addresses (home/small office networks)
                            elif ipv4_addr.startswith('172.') and priority_3_result is None:
                                priority_3_result = (ipv4_addr, formatted_mac)
                            # Fallback: any other valid address
                            elif fallback_result is None:
                                fallback_result = (ipv4_addr, formatted_mac)
            
            # Return the highest priority result available
            if priority_1_result:
                return priority_1_result
            elif priority_2_result:
                return priority_2_result
            elif priority_3_result:
                return priority_3_result
            elif fallback_result:
                return fallback_result
                
        except Exception:
            pass
        return "Not found", "Not found"

    def detect_ssd_advanced(self, disk, model: str) -> bool:
        """
        Advanced SSD detection using multiple methods
        """
        model_lower = model.lower()
        
        # Method 1: Check model name for SSD indicators
        ssd_indicators = [
            'ssd', 'nvme', 'pcie', 'm.2', 'solid state', 'flash',
            # Specific SSD model patterns
            'samsung ssd', 'crucial mx', 'crucial bx', 'intel ssd',
            'wd blue sn', 'wd black sn', 'seagate firecuda',
            'kingston snv', 'kingston nv', 'kingston a2000',
            'toshiba ssd', 'sandisk ssd', 'micron ssd',
            # NVMe patterns
            'nvme', 'gen3', 'gen4', 'pcie',
            # Common SSD suffixes/prefixes
            'sata ssd', 'msata', 'ngff'
        ]
        
        for indicator in ssd_indicators:
            if indicator in model_lower:
                return True
        
        # Method 2: Check interface type more thoroughly
        try:
            interface_type = getattr(disk, 'InterfaceType', None)
            if interface_type:
                interface_lower = str(interface_type).lower()
                # NVMe is almost always SSD
                if 'nvme' in interface_lower:
                    return True
                # Check for PCIe interface (common for NVMe SSDs)
                if 'pcie' in interface_lower or 'pci express' in interface_lower:
                    return True
        except:
            pass
        
        # Method 3: Check media type
        try:
            media_type = getattr(disk, 'MediaType', None)
            if media_type:
                media_lower = str(media_type).lower()
                if any(indicator in media_lower for indicator in ['ssd', 'solid state', 'flash', 'nvme']):
                    return True
        except:
            pass
        
        # Method 4: Check additional WMI properties
        try:
            # Check PNPDeviceID for SSD indicators
            pnp_id = getattr(disk, 'PNPDeviceID', None)
            if pnp_id:
                pnp_lower = str(pnp_id).lower()
                if any(indicator in pnp_lower for indicator in ['nvme', 'ssd', 'ufs']):
                    return True
        except:
            pass
        
        # Method 5: Use Win32_PhysicalMedia for additional detection
        try:
            # Get physical media info
            physical_media = list(self.wmi_client.Win32_PhysicalMedia())
            for media in physical_media:
                if hasattr(media, 'Tag') and hasattr(disk, 'DeviceID'):
                    # Try to match the physical media to the disk drive
                    media_type = getattr(media, 'MediaType', None)
                    if media_type and 'ssd' in str(media_type).lower():
                        return True
        except:
            pass
        
        # Method 6: Last resort - check for common SSD manufacturer patterns
        manufacturer_patterns = [
            'samsung', 'crucial', 'intel', 'micron', 'sandisk', 
            'western digital', 'wd', 'kingston', 'corsair', 
            'adata', 'transcend', 'patriot', 'mushkin', 'ocz'
        ]
        
        # If it's from a known SSD manufacturer and relatively small (< 4TB), likely SSD
        if any(pattern in model_lower for pattern in manufacturer_patterns):
            try:
                capacity_gb = float(disk.Size) / (1024 * 1024 * 1024) if disk.Size else 0
                # Most consumer SSDs are under 4TB, while most large drives are HDDs
                if capacity_gb < 4000:  # Less than 4TB
                    # Additional heuristic: if it's a common SSD size
                    common_ssd_sizes = [128, 256, 512, 1000, 1024, 2000, 2048]  # GB
                    if any(abs(capacity_gb - size) < 50 for size in common_ssd_sizes):
                        return True
            except:
                pass
        
        return False

    def get_hdd_info(self) -> Tuple[str, str]:
        try:
            disk_info = list(self.wmi_client.Win32_DiskDrive())
            total_capacity = 0
            drive_types = []

            for disk in disk_info:
                try:
                    # Convert capacity from bytes to GB
                    capacity = int(disk.Size) if disk.Size else 0
                    capacity_gb = float(capacity) / (1024 * 1024 * 1024)
                    total_capacity += capacity

                    model = disk.Model if disk.Model else "Unknown Model"
                    
                    # Enhanced SSD detection with multiple methods
                    is_ssd = self.detect_ssd_advanced(disk, model)
                    
                    # Final classification
                    if is_ssd:
                        drive_types.append(f"SSD ({model})")
                    else:
                        drive_types.append(f"HDD ({model})")
                            
                except (ValueError, TypeError) as e:
                    drive_types.append(f"Unknown ({model if 'model' in locals() else 'Unknown'})")

            total_capacity_gb = float(total_capacity) / (1024 * 1024 * 1024)
            total_capacity_str = f"{total_capacity_gb:.2f} GB"
            drive_types_str = " > ".join(drive_types) if drive_types else "Unknown"

            return total_capacity_str, drive_types_str
        except Exception as e:
            return "Not found", "Not found"

    def debug_disk_info(self):
        """
        Debug method to see all available disk information
        """
        try:
            disk_info = list(self.wmi_client.Win32_DiskDrive())
            print("=== DISK DEBUG INFO ===")
            
            for i, disk in enumerate(disk_info):
                print(f"\n--- Disk {i+1} ---")
                
                # Print all available attributes
                attributes_to_check = [
                    'Model', 'Size', 'MediaType', 'InterfaceType', 'PNPDeviceID',
                    'Caption', 'Description', 'Manufacturer', 'FirmwareRevision',
                    'SerialNumber', 'Capabilities', 'Status', 'DeviceID'
                ]
                
                for attr in attributes_to_check:
                    try:
                        value = getattr(disk, attr, 'Not Available')
                        print(f"  {attr}: {value}")
                    except Exception as e:
                        print(f"  {attr}: Error - {e}")
                
                # Also check Win32_PhysicalMedia
                try:
                    physical_media = list(self.wmi_client.Win32_PhysicalMedia())
                    print(f"  Physical Media Count: {len(physical_media)}")
                    for j, media in enumerate(physical_media):
                        print(f"    Media {j+1} - MediaType: {getattr(media, 'MediaType', 'N/A')}")
                        print(f"    Media {j+1} - Tag: {getattr(media, 'Tag', 'N/A')}")
                except Exception as e:
                    print(f"  Physical Media Error: {e}")
            
            print("\n=== END DEBUG INFO ===")
            
        except Exception as e:
            print(f"Debug error: {e}")


def print_system_info_grid(info: SystemInfo):
    data = [
        ["Log User", info.log_user],
        ["Hostname", info.hostname],
        ["Serial Number", info.serial_number],
        ["Processor", info.processor],
        ["OS Version", info.windows_version],
        ["Display Version", info.windows_display_version],
        ["Windows Install Date", info.windows_install_date],
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
        ["Office Name", info.office_name],
        ["Office Version", info.office_version],
        ["Total HDD Capacity", info.total_hdd_capacity],
        ["Drive Types", info.drive_types],
        ["Timestamp", info.timestamp],
    ]
    os.system("cls")
    print(tabulate(data, headers=["Field", "Value"], tablefmt="simple"))
    
    # Also print JSON below the grid
    json_result = json.dumps(asdict(info), indent=2)
    # print("\nJSON Result:")
    # print(json_result)


if __name__ == "__main__":
    try:
        collector = SystemInfoCollector()
        
        # Uncomment the line below to see debug info for disk detection
        # collector.debug_disk_info()
        
        system_info = collector.collect()
        print_system_info_grid(system_info)
        print("✓ [system_info_module.py] System information collected and stored in memory\n")        
    except Exception as e:
        print(f"Error collecting system information: {e}")