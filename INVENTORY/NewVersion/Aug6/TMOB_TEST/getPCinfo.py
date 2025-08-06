# GetPCInfo.py

import threading
import sys
import json
import os
import sqlite3
import time
from dataclasses import asdict
from tabulate import tabulate
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QWidget, QTableWidget, QTableWidgetItem, 
                             QVBoxLayout, QPushButton, QCheckBox, QHBoxLayout, 
                             QMessageBox, QLabel, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon

from loc_entry import LocationRecorder
from system_info_module import SystemInfoCollector, SystemInfo

# Load environment variables
load_dotenv()

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
    "windows_version": "OS Version",
    "windows_display_version": "Display Version",
    "manufacturer": "Manufacturer",
    "model": "Model",
    "total_ram": "Total RAM",
    "num_ram_slots": "Number of RAM Slots",
    "ram_per_slot": "RAM per Slot",
    "ram_speed": "RAM Speed",
    "ram_type": "RAM Type",
    "ip_address": "IP Address",
    "mac_address": "MAC Address",
    "citrix_name": "Citrix Name",
    "citrix_version": "Citrix Version",
    "timestamp": "Timestamp",
    "floor": "Floor",
    "room": "Selections",
    "room_name": "Name",
    "D1": "Code",
    "E1": "Loc1",
    "E2": "Seat",
    "location_code": "Room Desc",
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
            print("✅ System information collected in background thread.\n")
        except Exception as e:
            error_msg = f"Error collecting system info: {e}"
            print(error_msg)
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
        self.setWindowTitle("Loading System Information")
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

        self.setGeometry(100, 150, 600, 700)         
        self.setWindowTitle("Summary Data")
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
        # Try to set back icon (will use text if icon not found)
        try:
            self.back_button.setIcon(QIcon("back.png"))
        except:
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
        # Try to set save icon (will use text if icon not found)
        try:
            self.save_button.setIcon(QIcon("save.png"))
        except:
            self.save_button.setText("💾 Save")
        
        self.save_button.clicked.connect(self.save_data_to_db)
        button_layout.addWidget(self.save_button)
        
        self.layout.addLayout(button_layout)
        self.setLayout(self.layout)

    def populate_table(self, data):
        # Define location fields that should appear at the top
        location_fields = ["floor", "room", "room_name", "D1", "E1", "E2", "location_code"]
        
        # Get location data first
        location_data = [(key, value) for key, value in data.items() if key in location_fields]
        
        # Get system data (everything else)
        system_data = [(key, value) for key, value in data.items() if key not in location_fields]
        
        # Combine with location data first
        all_data = location_data + system_data
        
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
                except ValueError:
                    display_value = str(value)
            else:
                display_value = str(value)
            self.table.setItem(row, 0, QTableWidgetItem(display_name))
            self.table.setItem(row, 1, QTableWidgetItem(display_value))

    def go_back(self):
        """Go back to main form"""
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
        db_path = os.path.join(db_folder, f"{db_name}.db")

        print(db_folder)

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
                    manufacturer TEXT,
                    model TEXT,
                    total_ram TEXT,
                    num_ram_slots TEXT,
                    ram_per_slot TEXT,
                    ram_speed TEXT,
                    ram_type TEXT,
                    ip_address TEXT,
                    mac_address TEXT,
                    citrix_name TEXT,
                    citrix_version TEXT,
                    timestamp TEXT
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
                    manufacturer,
                    model,
                    total_ram,
                    num_ram_slots,
                    ram_per_slot,
                    ram_speed,
                    ram_type,
                    ip_address,
                    mac_address,
                    citrix_name,
                    citrix_version,
                    timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Format E1 with leading zero for single-digit numbers
            e1_value = data.get("E1")
            try:
                e1_num = int(e1_value)
                if 0 < e1_num < 10:
                    formatted_e1 = f"{e1_num:02d}"
                else:
                    formatted_e1 = str(e1_value)
            except ValueError:
                formatted_e1 = str(e1_value)

            # Format E2 with leading zero for single-digit numbers
            e2_value = data.get("E2")
            try:
                e2_num = int(e2_value)
                if 0 < e2_num < 10:
                    formatted_e2 = f"{e2_num:02d}"
                else:
                    formatted_e2 = str(e2_value)
            except ValueError:
                formatted_e2 = str(e2_value)

            # Prepare values
            values = (
                data.get("floor"),
                data.get("room_name"),
                f"{data.get('D1', '')}{formatted_e1}",  # combined loc1 with formatted E1
                formatted_e2,                           # loc2 with leading zero
                None,
                data.get("log_user"),
                data.get("hostname"),
                data.get("serial_number"),
                data.get("processor"),
                data.get("windows_version"),
                data.get("windows_display_version"),
                data.get("manufacturer"),
                data.get("model"),
                data.get("total_ram"),
                data.get("num_ram_slots"),
                data.get("ram_per_slot"),
                data.get("ram_speed"),
                data.get("ram_type"),
                data.get("ip_address"),
                data.get("mac_address"),
                data.get("citrix_name"),
                data.get("citrix_version"),
                data.get("timestamp"),
            )

            # Execute
            cur.execute(insert_query, values)
            conn.commit()
            conn.close()

            print("✅ Record inserted into", db_path)

            # Show success message with appropriate text
            if self.reboot_checkbox.isChecked():
                message = "Thank you, Desktop Inventory is Saved to Database... Rebooting your System.."
                title = "Rebooting System"
            else:
                message = "Thank you, Desktop Inventory is Saved to Database... Closing this App"
                title = "Closing Application"

            # Show message box
            msg_box = QMessageBox()
            msg_box.setWindowTitle(title)
            msg_box.setText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()

            # Check reboot checkbox
            if self.reboot_checkbox.isChecked():
                print("⚡️ Reboot checkbox is checked. Rebooting now...")
                os.system("shutdown /r /t 0")
            else:
                print("✅ Closing application...")

            # Quit the app
            QApplication.quit()

        except Exception as e:
            # Show error message
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Database Error")
            error_msg.setText(f"Failed to save to database: {str(e)}")
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.exec_()

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
        
        # Start system info collection immediately after form is loaded
        self.start_system_info_collection()

    def start_system_info_collection(self):
        """Start collecting system information immediately"""
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

    def on_system_info_finished(self, result):
        """Called when system info collection is complete"""
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None
        print("✅ System information collection completed!")

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

            # If system info is still being collected, show message
            if system_info_collecting:
                msg = QMessageBox()
                msg.setWindowTitle("Please Wait")
                msg.setText("System information is still being collected. Please wait and try again.")
                msg.exec_()
                return

            # If system info is not available and not collecting, something went wrong
            if system_info_result is None:
                msg = QMessageBox()
                msg.setWindowTitle("Error")
                msg.setText("System information is not available. Please restart the application.")
                msg.exec_()
                return

            location_data = self.window.answers
            combined = {**asdict(system_info_result), **location_data}

            # Hide main window
            self.window.hide()

            # Create or update summary window
            if self.summary_window is None:
                self.summary_window = SummaryWindow(combined, self.window)
            else:
                self.summary_window.update_data(combined)
            
            self.summary_window.show()

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
    # No longer start system info collection immediately
    run_loc_entry()