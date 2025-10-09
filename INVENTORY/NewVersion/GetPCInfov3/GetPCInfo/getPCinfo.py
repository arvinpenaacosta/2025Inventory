import subprocess
import threading
import sys
import json
import os
import sqlite3
import time
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from tabulate import tabulate
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QWidget, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QPushButton, QCheckBox, QHBoxLayout, 
                             QMessageBox, QLabel, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon, QBrush, QColor

from loc_entry2 import LocationRecorder
from system_info_module import SystemInfoCollector, SystemInfo

# Load environment variables
load_dotenv()

# Define default status
statusActive = "ACTIVE"
ENABLE_LOGGING = os.getenv("LOGGING", "False").lower() in ("1", "true", "yes")


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running as a script
        base_path = os.path.abspath(".")
    full_path = os.path.join(base_path, relative_path)
    # Debug: Log the resolved path to a file (since --noconsole hides console)

    if ENABLE_LOGGING:    
        with open("debug.log", "a", encoding='utf-8') as f:
            f.write(f"[{datetime.now()}] Resolved path for {relative_path}: {full_path}\n")
            if not os.path.exists(full_path):
                f.write(f"[{datetime.now()}] Warning: File {full_path} does not exist\n")

    return full_path

# ------------------------
# Global variable to hold system info
# ------------------------
system_info_result = None
system_info_collecting = False

# ------------------------
# Aliases mapping for prettier display
# ------------------------
field_aliases = {
    "log_user": "User",
    "hostname": "Hostname",
    "serial_number": "Serial Number",
    "processor": "Processor",
    "model": "Model",
    "manufacturer": "Manufacturer",
    "windows_version": "OS Version",
    "windows_display_version": "Display Version",
    "windows_install_date": "Windows Install Date",
    "citrix_name": "Citrix Name",
    "citrix_version": "Citrix Version",
    "office_name": "Office Name",
    "office_version": "Office Version",
    "total_ram": "Total RAM",
    "num_ram_slots": "Number of RAM Slots",
    "ram_per_slot": "RAM per Slot",
    "ram_speed": "RAM Speed",
    "ram_type": "RAM Type",
    "ip_address": "IP Address",
    "mac_address": "MAC Address",
    "total_hdd_capacity": "Total Storage Capacity",
    "drive_types": "Drive Types",
    "timestamp": "Timestamp",
    "floor": "Floor",
    "room": "Selections",
    "room_name": "Name",
    "D1": "Code",
    "E1": "Loc1",
    "E2": "Seat",
    "location_code": "Room Desc",
    "taskfor": "Task",
    "status": "Status"
}

# ------------------------
# System Info Collection Thread
# ------------------------
class SystemInfoThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def run(self):
        import pythoncom
        pythoncom.CoInitialize()
        
        global system_info_result, system_info_collecting
        system_info_collecting = True
        
        try:
            collector = SystemInfoCollector()
            system_info_result = collector.collect()
            self.finished.emit(system_info_result)

            if ENABLE_LOGGING:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] System information collected in background thread.\n")

        except Exception as e:
            error_msg = f"Error collecting system info: {e}"

            if ENABLE_LOGGING:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] {error_msg}\n")

            self.error.emit(error_msg)
        finally:
            system_info_collecting = False
            pythoncom.CoUninitialize()

# ------------------------
# Loading Dialog
# ------------------------
class LoadingDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Collecting System Information")
        self.setWindowIcon(QIcon(resource_path("app.png")))
        self.setFixedSize(400, 120)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint)
        
        layout = QVBoxLayout()
        
        # Label
        self.label = QLabel("Collecting hardware information, please wait...")
        self.label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        layout.addWidget(self.label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress)

        self.setLayout(layout)
        
        # Center the dialog on screen
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

# ------------------------
# Summary Window
# ------------------------
class SummaryWindow(QWidget):
    def __init__(self, combined_data, main_window):
        super().__init__()

        self.setGeometry(100, 100, 600, 700)         
        self.setWindowTitle("Summary Data")
        # Set window icon
        self.setWindowIcon(QIcon(resource_path("app.png")))
        self.main_window = main_window

        self.layout = QVBoxLayout()

        # Save original data dictionary so we can use it directly for DB
        self.original_data = combined_data

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Field", "Value"])

        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 400)

        # Populate table using aliases
        self.populate_table(combined_data)
        self.layout.addWidget(self.table)

        # Checkbox
        self.reboot_checkbox = QCheckBox("Reboot after save")
        self.layout.addWidget(self.reboot_checkbox)

        # Button layout
        button_layout = QHBoxLayout()
        
        # Back button
        self.back_button = QPushButton("  Back")
        self.back_button.setMinimumSize(120, 45)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """)
        try:
            self.back_button.setIcon(QIcon(resource_path("back.png")))
        except Exception as e:

            if ENABLE_LOGGING:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] Failed to load back.png: {e}\n")

            self.back_button.setText("← Back")
        
        self.back_button.clicked.connect(self.go_back)
        button_layout.addWidget(self.back_button)
        
        # Save button
        self.save_button = QPushButton("  Save.")
        self.save_button.setMinimumSize(120, 45)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        try:
            self.save_button.setIcon(QIcon(resource_path("save.png")))
        except Exception as e:

            if ENABLE_LOGGING:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] Failed to load save.png: {e}\n")

            self.save_button.setText("💾 Save")
        
        self.save_button.clicked.connect(self.save_data_to_db)
        button_layout.addWidget(self.save_button)
        
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def populate_table(self, data):
        # Single custom order for all fields (top to bottom - modify this list as needed)
        custom_order = [
            # Location fields from loc_entry2.py (top priority)
            "floor", "room_name", "D1", "E1", "E2", "location_code", "taskfor", "status",
            
            # Key system identifiers
            "hostname", "serial_number", "log_user",
            
            # OS and software info
            "windows_version", "windows_display_version", "windows_install_date",
            "citrix_name", "citrix_version", "office_name", "office_version",
            
            # Hardware basics
            "processor", "manufacturer", "model", "total_ram", "num_ram_slots", "ram_per_slot","ram_speed", "ram_type",
            
            # Network info
            "ip_address", "mac_address",
            
            # Detailed hardware
            
            "total_hdd_capacity", "drive_types",
            
            # Timestamp last
            "timestamp"
        ]
        
        # Get all available fields and filter to those in custom_order or append remaining
        all_data = []
        used_fields = set()
        
        # First, add fields from custom_order if they exist in data
        for key in custom_order:
            if key == "status":
                # Set status based on taskfor
                status_value = "VACANT" if data.get("taskfor") == "VACANT" else statusActive
                all_data.append(("status", status_value))
            elif key in data:
                all_data.append((key, data[key]))
                used_fields.add(key)
        
        # Then, append any remaining fields not in custom_order (to ensure all data is shown)
        remaining_fields = [(key, data[key]) for key in data.keys() if key not in used_fields and key != "room" and key != "skip_system_info"]
        all_data.extend(remaining_fields)
        
        self.table.setRowCount(len(all_data))
        for row, (key, value) in enumerate(all_data):
            display_name = field_aliases.get(key, key)
            # Add leading zero for single-digit numeric values in E1, E2
            if key in ["E1", "E2"]:
                try:
                    num_value = int(value)
                    if 0 < num_value < 10:
                        display_value = f"{num_value:02d}"
                    else:
                        display_value = str(value)
                except (ValueError, TypeError):
                    display_value = str(value) if value is not None else ""
            else:
                display_value = str(value) if value is not None else ""
            
            # Create table items
            name_item = QTableWidgetItem(display_name)
            value_item = QTableWidgetItem(display_value)
            
            # Apply bold and blue font to specific fields
            if key in ["taskfor", "serial_number", "status", "hostname", "windows_version", "citrix_name","total_ram","num_ram_slots", "ram_per_slot",
                      "citrix_version", "office_name", "office_version", "total_hdd_capacity", "drive_types"]:
                bold_font = QFont()
                bold_font.setBold(True)
                name_item.setFont(bold_font)
                name_item.setForeground(QBrush(QColor("blue")))
                value_item.setFont(bold_font)
                value_item.setForeground(QBrush(QColor("blue")))
            
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, value_item)

    def go_back(self):
        """Go back to main form"""
        global system_info_result, system_info_collecting
        # Reset system info data when going back
        system_info_result = None
        system_info_collecting = False
        
        self.hide()
        self.main_window.show()

    def update_data(self, new_combined_data):
        """Update the summary with new data"""
        self.original_data = new_combined_data
        self.populate_table(new_combined_data)

    def save_data_to_db(self):
        data = self.original_data

        # Get DB path from .env
        db_folder = os.getenv("FILE_PATH", ".")
        db_name = os.getenv("FILE_SQLITE", "default_db")
        
        # Ensure directory exists
        if not os.path.exists(db_folder):
            try:
                os.makedirs(db_folder)
            except Exception as e:
                error_msg = f"Failed to create database directory: {db_folder}\nError: {e}"
                if ENABLE_LOGGING:
                    with open("debug.log", "a", encoding='utf-8') as f:
                        f.write(f"[{datetime.now()}] {error_msg}\n")
                QMessageBox.critical(self, "Directory Error", error_msg)
                return

        db_path = os.path.join(db_folder, f"{db_name}.db")

        if ENABLE_LOGGING:
            with open("debug.log", "a", encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] Attempting to save to database: {db_path}\n")

        try:
            # Connect to SQLite
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            # Create table if not exists
            create_table_query = """
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    floor TEXT,
                    roomname TEXT,
                    loc1 TEXT,
                    loc2 TEXT,
                    loceam TEXT,
                    log_user TEXT,
                    hostname TEXT,
                    serial_number TEXT,
                    processor TEXT,
                    windows_version TEXT,
                    windows_display_version TEXT,
                    windows_install_date TEXT,
                    manufacturer TEXT,
                    model TEXT,
                    total_ram TEXT,
                    num_ram_slots TEXT,
                    ram_per_slot TEXT,
                    ram_speed TEXT,
                    ram_type TEXT,
                    total_hdd_capacity TEXT,
                    drive_types TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    citrix_name TEXT,
                    citrix_version TEXT,
                    office_name TEXT,
                    office_version TEXT,
                    timestamp TEXT,
                    taskfor TEXT,
                    status TEXT
                );
            """
            cur.execute(create_table_query)

            # Insert query
            insert_query = """
                INSERT INTO inventory (
                    floor,
                    roomname,
                    loc1,
                    loc2,
                    loceam,
                    log_user,
                    hostname,
                    serial_number,
                    processor,
                    windows_version,
                    windows_display_version,
                    windows_install_date,
                    manufacturer,
                    model,
                    total_ram,
                    num_ram_slots,
                    ram_per_slot,
                    ram_speed,
                    ram_type,
                    total_hdd_capacity,
                    drive_types,
                    ip_address,
                    mac_address,
                    citrix_name,
                    citrix_version,
                    office_name,
                    office_version,
                    timestamp,
                    taskfor,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Format E1 with leading zero for single-digit numbers
            e1_value = data.get("E1")
            try:
                e1_num = int(e1_value)
                if 0 < e1_num < 10:
                    formatted_e1 = f"{e1_num:02d}"
                else:
                    formatted_e1 = str(e1_value) if e1_value is not None else ""
            except (ValueError, TypeError):
                formatted_e1 = str(e1_value) if e1_value is not None else ""

            # Format E2 with leading zero for single-digit numbers
            e2_value = data.get("E2")
            try:
                e2_num = int(e2_value)
                if 0 < e2_num < 10:
                    formatted_e2 = f"{e2_num:02d}"
                else:
                    formatted_e2 = str(e2_value) if e2_value is not None else ""
            except (ValueError, TypeError):
                formatted_e2 = str(e2_value) if e2_value is not None else ""

            # Prepare values, handle None/blank values
            values = (
                data.get("floor", ""),
                data.get("room_name", ""),
                f"{data.get('D1', '')}{formatted_e1}" if data.get("D1") or formatted_e1 else "",
                formatted_e2,
                None,
                data.get("log_user", ""),
                data.get("hostname", ""),
                data.get("serial_number", ""),
                data.get("processor", ""),
                data.get("windows_version", ""),
                data.get("windows_display_version", ""),
                data.get("windows_install_date", ""),
                data.get("manufacturer", ""),
                data.get("model", ""),
                data.get("total_ram", ""),
                str(data.get("num_ram_slots", "")) if data.get("num_ram_slots") is not None else "",
                data.get("ram_per_slot", ""),
                data.get("ram_speed", ""),
                data.get("ram_type", ""),
                data.get("total_hdd_capacity", ""),
                data.get("drive_types", ""),
                data.get("ip_address", ""),
                data.get("mac_address", ""),
                data.get("citrix_name", ""),
                data.get("citrix_version", ""),
                data.get("office_name", ""),
                data.get("office_version", ""),
                data.get("timestamp", ""),
                data.get("taskfor", ""),
                "VACANT" if data.get("taskfor") == "VACANT" else statusActive
            )

            # Execute
            if ENABLE_LOGGING:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] Executing insert query with values: {values}\n")

            cur.execute(insert_query, values)
            conn.commit()

            if ENABLE_LOGGING:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] Record inserted into {db_path}\n")

            # Show success message with appropriate text
            if self.reboot_checkbox.isChecked():
                message = "Thank you, Desktop Inventory is Saved to Database... Rebooting your System.."
                title = "Rebooting System"
            else:
                message = "Thank you, Desktop Inventory is Saved to Database... Closing this App"
                title = "Closing Application"

            # Show message box at specific coordinates
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.move(50, 200)
            msg_box.exec_()

            # Check reboot checkbox
            if self.reboot_checkbox.isChecked():

                if ENABLE_LOGGING:
                    with open("debug.log", "a", encoding='utf-8') as f:
                        f.write(f"[{datetime.now()}] Reboot checkbox is checked. Rebooting now...\n")

                subprocess.run(["shutdown", "/r", "/t", "0"])
            else:

                if ENABLE_LOGGING:
                    with open("debug.log", "a", encoding='utf-8') as f:
                        f.write(f"[{datetime.now()}] Closing application...\n")

            # Quit the app
            QApplication.quit()

        except Exception as e:
            # Show detailed error message
            error_msg = f"Failed to save to database: {str(e)}\nDB Path: {db_path}\nValues: {values}"

            if ENABLE_LOGGING:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"[{datetime.now()}] {error_msg}\n")

            error_box = QMessageBox()
            error_box.setWindowTitle("Database Error")
            error_box.setText(error_msg)
            error_box.setIcon(QMessageBox.Critical)
            error_box.exec_()
        finally:
            if 'conn' in locals():
                conn.close()

# ------------------------
# Enhanced Location Recorder Wrapper
# ------------------------
class EnhancedLocationRecorder:
    def __init__(self):
        self.window = LocationRecorder()
        self.window.move(50, 100)
        self.summary_window = None
        self.system_info_thread = None
        self.loading_dialog = None

    def start_system_info_collection(self):
        """Start collecting system information after location is submitted"""
        global system_info_collecting
        
        if system_info_collecting or system_info_result is not None:
            return
            
        # Show loading dialog
        self.loading_dialog = LoadingDialog(self.window)
        self.loading_dialog.show()
        
        # Start system info collection thread
        self.system_info_thread = SystemInfoThread()
        self.system_info_thread.finished.connect(self.on_system_info_finished)
        self.system_info_thread.error.connect(self.on_system_info_error)
        self.system_info_thread.start()

    def create_blank_system_info(self):
        """Create a blank SystemInfo object with only timestamp and log_user populated"""
        utc_now = datetime.now(timezone.utc)
        local_time = utc_now + timedelta(hours=8)
        timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
        log_user = os.getenv("USERNAME", "Unknown")
 
        # Get location data to create serial number
        location_data = self.window.answers
        
        # Create serial number by combining Floor, D1+E1 (Loc1), and E2 (Loc2)
        floor = location_data.get("floor", "")
        d1 = location_data.get("D1", "")
        e1 = location_data.get("E1", "")
        e2 = location_data.get("E2", "")
        
        # Format E1 and E2 with leading zeros for single digits
        try:
            e1_num = int(e1)
            formatted_e1 = f"{e1_num:02d}" if 0 < e1_num < 10 else str(e1)
        except (ValueError, TypeError):
            formatted_e1 = str(e1) if e1 else ""
        
        try:
            e2_num = int(e2)
            formatted_e2 = f"{e2_num:02d}" if 0 < e2_num < 10 else str(e2)
        except (ValueError, TypeError):
            formatted_e2 = str(e2) if e2 else ""
        
        # Combine to create serial number: Floor-Loc1-Loc2
        loc1 = f"{d1}{formatted_e1}" if d1 or formatted_e1 else ""
        serial_number = f"{floor}{loc1}{formatted_e2}" if floor and loc1 and formatted_e2 else ""
  

        return SystemInfo(
            log_user=log_user,
            hostname=None,
            serial_number=serial_number,
            processor=None,
            windows_version=None,
            windows_display_version=None,
            windows_install_date=None,
            manufacturer=None,
            model=None,
            total_ram=None,
            num_ram_slots=None,
            ram_per_slot=None,
            ram_speed=None,
            ram_type=None,
            ip_address=None,
            mac_address=None,
            citrix_name=None,
            citrix_version=None,
            office_name=None,
            office_version=None,
            total_hdd_capacity=None,
            drive_types=None,
            timestamp=timestamp
        )

    def on_system_info_finished(self, result):
        """Called when system info collection is complete or for VACANT case"""
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None
            
        # Get location data and combine with system info
        location_data = self.window.answers
        combined = {**asdict(result), **location_data}

        # Remove skip_system_info flag from combined data
        combined.pop("skip_system_info", None)

        # Hide main window
        self.window.hide()

        # Create or update summary window
        if self.summary_window is None:
            self.summary_window = SummaryWindow(combined, self.window)
        else:
            self.summary_window.update_data(combined)
        
        self.summary_window.show()

        if ENABLE_LOGGING:
            with open("debug.log", "a", encoding='utf-8') as f:
                f.write(f"[{datetime.now()}] System information collection completed!\n")

    def on_system_info_error(self, error_msg):
        """Called when system info collection fails"""
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None
        
        error_box = QMessageBox()
        error_box.setWindowTitle("System Info Error")
        error_box.setText(f"Failed to collect system information: {error_msg}")
        error_box.setIcon(QMessageBox.Warning)
        error_box.exec_()

    def setup_submit_handler(self):
        """Setup the submit button handler"""
        def on_submit():
            global system_info_result, system_info_collecting

            # Validate that location data is complete
            location_data = self.window.answers
            if not location_data or len(location_data) < 6:  # Updated validation to include taskfor
                msg = QMessageBox()
                msg.setWindowTitle("Incomplete Selection")
                msg.setText("Please complete all location and task selections before submitting.")
                msg.exec_()
                return

            # Check if taskfor is VACANT
            if location_data.get("skip_system_info", False):
                # Create blank system info with timestamp and log_user
                result = self.create_blank_system_info()
                self.on_system_info_finished(result)
            else:
                # Start system info collection for non-VACANT cases
                self.start_system_info_collection()

        self.window.submit_btn.clicked.connect(on_submit)

# ------------------------
# PyQt GUI main process
# ------------------------
def run_loc_entry():
    app = QApplication(sys.argv)
    
    # Create enhanced location recorder
    enhanced_recorder = EnhancedLocationRecorder()
    enhanced_recorder.setup_submit_handler()
    
    enhanced_recorder.window.show()
    sys.exit(app.exec_())

# ------------------------
# Entry point
# ------------------------
if __name__ == "__main__":
    run_loc_entry()