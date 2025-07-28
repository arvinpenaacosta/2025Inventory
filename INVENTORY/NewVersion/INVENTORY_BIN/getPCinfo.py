# getPCInfo.py

import threading
import sys
import json
import os
import sqlite3
import time
import shutil
import traceback
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
# Network Path Testing Functions
# ------------------------
def check_network_path(path):
    """Check if network path is accessible, create if it doesn't exist"""
    try:
        # Normalize the path
        path = os.path.normpath(path)
        
        # Try to access the directory
        if os.path.exists(path):
            # Try to write a test file
            test_file = os.path.join(path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True, "Network path is accessible and writable"
        else:
            # ✅ TRY TO CREATE THE DIRECTORY
            print(f"🔧 Network path does not exist, attempting to create: {path}")
            try:
                os.makedirs(path, exist_ok=True)
                print(f"✅ Successfully created network directory: {path}")
                
                # Test write permissions after creation
                test_file = os.path.join(path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return True, f"Network path created successfully and is writable: {path}"
                
            except PermissionError:
                return False, f"Permission denied - cannot create network directory: {path}"
            except Exception as create_error:
                return False, f"Failed to create network directory {path}: {str(create_error)}"
                
    except PermissionError:
        return False, f"Permission denied accessing: {path}"
    except Exception as e:
        return False, f"Cannot access network path: {str(e)}"

def backup_network_path(local_db_path, data):
    """Attempt to backup to network path"""
    try:
        network_folder = os.getenv("BACKUP_FILE_PATH")
        backup_db_name = os.getenv("BACKUP_FILE_SQLITE")
        
        if network_folder and backup_db_name:
            network_folder = os.path.normpath(network_folder)
            if os.path.exists(network_folder):
                backup_path = os.path.join(network_folder, f"{backup_db_name}.db")
                
                # Copy the local database to network location
                shutil.copy2(local_db_path, backup_path)
                print(f"✅ Backup created at: {backup_path}")
            else:
                print(f"⚠️  Backup network path not accessible: {network_folder}")
    except Exception as e:
        print(f"⚠️  Backup failed: {e}")

def test_network_connectivity():
    """Test network connectivity to the database path"""
    db_folder = os.getenv("FILE_PATH", "")
    print(f"Testing network path: {db_folder}")
    
    try:
        # Normalize the path
        db_folder = os.path.normpath(db_folder)
        
        # Test if we can list the directory
        if os.path.exists(db_folder):
            files = os.listdir(db_folder)
            print(f"✅ Directory accessible, contains {len(files)} items")
            
            # Test write permissions
            test_file = os.path.join(db_folder, "write_test.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("✅ Write permissions OK")
            return True
        else:
            # ✅ TRY TO CREATE THE DIRECTORY
            print(f"🔧 Directory does not exist, attempting to create: {db_folder}")
            try:
                os.makedirs(db_folder, exist_ok=True)
                print(f"✅ Successfully created directory: {db_folder}")
                
                # Test write permissions after creation
                test_file = os.path.join(db_folder, "write_test.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                print("✅ Write permissions OK after creation")
                return True
                
            except PermissionError:
                print("❌ Permission denied - cannot create directory. Check network credentials/permissions")
                return False
            except Exception as create_error:
                print(f"❌ Failed to create directory: {create_error}")
                return False
            
    except PermissionError:
        print("❌ Permission denied - check network credentials")
        return False
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

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

        # ✅ Save original data dictionary so we can use it directly for DB
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
            self.back_button.setIcon(QIcon("back.png"))  # You can add your own icon file
        except:
            self.back_button.setText("← Back")
        
        self.back_button.clicked.connect(self.go_back)
        button_layout.addWidget(self.back_button)
        
        # Save button
        self.save_button = QPushButton("  Save")
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
            self.save_button.setIcon(QIcon("save.png"))  # You can add your own icon file
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
            self.table.setItem(row, 0, QTableWidgetItem(display_name))
            self.table.setItem(row, 1, QTableWidgetItem(str(value)))

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
        db_folder = os.getenv("FILE_PATH", "./data")
        db_name = os.getenv("FILE_SQLITE", "inventory")
        
        #⚠️ print(f"🔍 Environment variables - Folder: {db_folder}, DB Name: {db_name}")
        
        # Convert network path format and normalize
        db_folder = os.path.normpath(db_folder)
        #⚠️ print(f"🔍 Normalized path: {db_folder}")
        
        # ✅ CHECK NETWORK PATH ACCESSIBILITY AND CREATE IF NEEDED
        is_accessible, access_message = check_network_path(db_folder)
        #⚠️ print(f"🔍 Network path check: {access_message}")
        
        original_db_folder = db_folder
        if not is_accessible:
            # Check if the error is due to missing directory vs other issues
            if "does not exist" in access_message.lower() or "failed to create" in access_message.lower():
                print(f"⚠️  Network path creation failed, falling back to local storage")
            else:
                print(f"⚠️  Network path not accessible, falling back to local storage")
            
            # ✅ FALLBACK TO LOCAL PATH
            fallback_folder = "./local_db"
            print(f"⚠️  Using fallback path: {fallback_folder}")
            
            # Show warning to user with more specific message
            fallback_msg = QMessageBox()
            fallback_msg.setWindowTitle("Network Path Issue")
            
            if "does not exist" in access_message.lower():
                fallback_msg.setText(f"Cannot create network directory:\n{db_folder}\n\nThis may be due to:\n• Network connectivity issues\n• Insufficient permissions\n• Invalid network path\n\nFalling back to local storage:\n{fallback_folder}")
            else:
                fallback_msg.setText(f"Cannot access network path:\n{db_folder}\n\nError: {access_message}\n\nFalling back to local storage:\n{fallback_folder}")
                
            fallback_msg.setIcon(QMessageBox.Warning)
            fallback_msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            fallback_msg.setDetailedText(f"Original error: {access_message}")
            
            if fallback_msg.exec_() == QMessageBox.Cancel:
                return
                
            db_folder = fallback_folder
        
        # ✅ CREATE DIRECTORY IF IT DOESN'T EXIST
        try:
            if not os.path.exists(db_folder):
                os.makedirs(db_folder, exist_ok=True)
                print(f"✅ Created directory: {db_folder}")
        except Exception as e:
            print(f"❌ Failed to create directory {db_folder}: {e}")
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Directory Error")
            error_msg.setText(f"Cannot create directory {db_folder}:\n{str(e)}\n\nPlease check permissions or contact IT support.")
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.exec_()
            return
        
        db_path = os.path.join(db_folder, f"{db_name}.db")
        #⚠️ print(f"🔍 Final database path: {db_path}")

        try:
            # ✅ TEST DATABASE CONNECTION FIRST
            #⚠️ print("🔍 Testing database connection...")
            test_conn = sqlite3.connect(db_path)
            test_conn.close()
            print("✅ Database connection test successful")
            
            # Connect to SQLite
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            # ✅ Create table if not exists
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
            print("✅ Table created/verified")

            # ✅ DEBUG: Print data being inserted
            #⚠️ print("🔍 Data being inserted:")
            #⚠️ for key, value in data.items():
            #⚠️    print(f"  {key}: {value}")

            # Insert query
            insert_query = """
                INSERT INTO inventory (
                    floor, roomname, loc1, loc2, loceam, log_user, hostname,
                    serial_number, processor, windows_version, windows_display_version,
                    manufacturer, model, total_ram, num_ram_slots, ram_per_slot,
                    ram_speed, ram_type, ip_address, mac_address, citrix_name,
                    citrix_version, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Prepare values - Handle None values better
            values = (
                str(data.get("floor", "")) if data.get("floor") is not None else "",
                str(data.get("room_name", "")) if data.get("room_name") is not None else "",
                f"{data.get('D1', '')}{data.get('E1', '')}",  # combined loc1
                str(data.get("E2", "")) if data.get("E2") is not None else "",
                None,  # loceam
                str(data.get("log_user", "")) if data.get("log_user") is not None else "",
                str(data.get("hostname", "")) if data.get("hostname") is not None else "",
                str(data.get("serial_number", "")) if data.get("serial_number") is not None else "",
                str(data.get("processor", "")) if data.get("processor") is not None else "",
                str(data.get("windows_version", "")) if data.get("windows_version") is not None else "",
                str(data.get("windows_display_version", "")) if data.get("windows_display_version") is not None else "",
                str(data.get("manufacturer", "")) if data.get("manufacturer") is not None else "",
                str(data.get("model", "")) if data.get("model") is not None else "",
                str(data.get("total_ram", "")) if data.get("total_ram") is not None else "",
                str(data.get("num_ram_slots", "")) if data.get("num_ram_slots") is not None else "",
                str(data.get("ram_per_slot", "")) if data.get("ram_per_slot") is not None else "",
                str(data.get("ram_speed", "")) if data.get("ram_speed") is not None else "",
                str(data.get("ram_type", "")) if data.get("ram_type") is not None else "",
                str(data.get("ip_address", "")) if data.get("ip_address") is not None else "",
                str(data.get("mac_address", "")) if data.get("mac_address") is not None else "",
                str(data.get("citrix_name", "")) if data.get("citrix_name") is not None else "",
                str(data.get("citrix_version", "")) if data.get("citrix_version") is not None else "",
                str(data.get("timestamp", "")) if data.get("timestamp") is not None else "",
            )

            #⚠️ print("🔍 Values being inserted:")
            #⚠️ for i, val in enumerate(values):
            #⚠️    print(f"  [{i}]: {repr(val)}")

            # Execute
            cur.execute(insert_query, values)
            conn.commit()
            
            # ✅ VERIFY THE INSERT
            cur.execute("SELECT COUNT(*) FROM inventory")
            count = cur.fetchone()[0]
            print(f"✅ Record inserted successfully. Total records: {count}")
            
            conn.close()

            print(f"✅ Record inserted into {db_path}")

            # ✅ ATTEMPT BACKUP TO NETWORK (if original was network path)
            if db_folder != original_db_folder and original_db_folder != db_folder:
                try:
                    backup_network_path(db_path, data)
                except Exception as backup_error:
                    print(f"⚠️  Backup to network failed: {backup_error}")

            # Show success message
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

        except sqlite3.Error as db_error:
            print(f"❌ SQLite Error: {db_error}")
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Database Error")
            error_msg.setText(f"SQLite Database Error:\n{str(db_error)}\n\nDatabase path: {db_path}")
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.exec_()
            
        except Exception as e:
            print(f"❌ General Error: {e}")
            traceback.print_exc()
            
            # Show detailed error message
            error_msg = QMessageBox()
            error_msg.setWindowTitle("Database Error")
            error_msg.setText(f"Failed to save to database:\n{str(e)}\n\nPath: {db_path}")
            error_msg.setDetailedText(traceback.format_exc())
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
    # Test network connectivity first (optional)
    print("🔍 Testing network connectivity...")
    test_network_connectivity()
    print()
    
    # Run the main application
    run_loc_entry()