import polars as pl
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QWidget, QMessageBox, QLabel, QFrame, 
                           QProgressBar, QGroupBox, QGridLayout, QSpacerItem, 
                           QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
import sys
import webbrowser

class WorkerThread(QThread):
    """Background thread for data processing"""
    finished = pyqtSignal(bool, str, int, float)
    progress = pyqtSignal(str)
    
    def __init__(self, file_path, file_sqlite, js_path, js_data):
        super().__init__()
        self.file_path = file_path
        self.file_sqlite = file_sqlite
        self.js_path = js_path
        self.js_data = js_data
    
    def run(self):
        try:
            start_time = datetime.now()
            
            self.progress.emit("Normalizing paths...")
            file_path = normalize_network_path(self.file_path)
            js_path = normalize_network_path(self.js_path)
            db_path = os.path.join(file_path, f"{self.file_sqlite}.db")
            js_output_path = os.path.join(js_path, self.js_data)

            self.progress.emit("Checking network access...")
            if not check_network_access(file_path):
                raise Exception(f"Cannot access database directory: {file_path}")
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"Database file not found: {db_path}")

            self.progress.emit("Extracting data from database...")
            data = extract_inventory_data_with_polars(db_path)
            
            self.progress.emit("Processing data...")
            processed_data = process_data(data)
            
            self.progress.emit("Saving to JavaScript file...")
            save_to_js(processed_data, js_output_path)
            
            self.progress.emit("Data extraction completed successfully!")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.finished.emit(True, js_output_path, len(processed_data), duration)
            
        except Exception as e:
            self.finished.emit(False, str(e), 0, 0)

def load_environment():
    from dotenv import load_dotenv
    load_dotenv()

    file_path = os.getenv('FILE_PATH')
    file_sqlite = os.getenv('FILE_SQLITE')
    js_path = os.getenv('JS_PATH')
    js_data = os.getenv('JS_DATA')

    if not all([file_path, file_sqlite, js_path, js_data]):
        raise ValueError("Missing required environment variables. Check your .env file.")

    return file_path, file_sqlite, js_path, js_data

def normalize_network_path(path):
    return os.path.normpath(path)

def check_network_access(path):
    """Check if network path is accessible, create if it doesn't exist"""
    try:
        path = os.path.normpath(path)
        
        if os.path.exists(path):
            return True
        else:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"✅ Created directory: {path}")
                return True
            except PermissionError:
                print(f"❌ Permission denied creating directory: {path}")
                return False
            except Exception as e:
                print(f"❌ Failed to create directory {path}: {e}")
                return False
                
    except (OSError, PermissionError) as e:
        print(f"❌ Network access error: {e}")
        return False

def extract_inventory_data_with_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    query = """
    SELECT 
        id, floor, roomname, loc1, loc2, loceam, log_user, hostname,
        serial_number, processor, windows_version, windows_display_version,
        manufacturer, model, total_ram, num_ram_slots, ram_per_slot,
        ram_speed, ram_type, ip_address, mac_address, citrix_name,
        citrix_version, timestamp
    FROM inventory 
    ORDER BY timestamp DESC
    """

    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    data = [{column: row[column] for column in row.keys()} for row in rows]
    conn.close()
    return data

def extract_inventory_data_with_polars(db_path):
    return extract_inventory_data_with_sqlite(db_path)

def process_data(data):
    try:
        if len(data) > 1000:
            df = pl.DataFrame(data)
            if 'timestamp' in df.columns:
                df = df.with_columns([
                    pl.col('timestamp').str.strptime(pl.Datetime, format='%Y-%m-%d %H:%M:%S', strict=False)
                    .fill_null(pl.col('timestamp'))
                    .alias('timestamp')
                ])
            df = df.sort('timestamp', descending=True)
            return df.to_dicts()
        else:
            return data
    except Exception as e:
        print(f"Warning during processing: {e}")
        return data

def save_to_js(data, output_path):
    try:
        output_path = normalize_network_path(output_path)
        output_dir = os.path.dirname(output_path)
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"✅ Created JS output directory: {output_dir}")
            except Exception as e:
                raise Exception(f"Cannot create output directory {output_dir}: {e}")

        js_content = f"""// Inventory Data - Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Total records: {len(data)}

const inventoryData = {str(data).replace("None", "null")};

// Make data available globally
if (typeof window !== 'undefined') {{
    window.inventoryData = inventoryData;
}}

// For Node.js environments
if (typeof module !== 'undefined' && module.exports) {{
    module.exports = inventoryData;
}}
"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(js_content)

        print(f"✅ JavaScript file saved to: {output_path}")
        return True
    except Exception as e:
        raise Exception(f"Error saving JavaScript file: {e}")

class ModernButton(QPushButton):
    """Custom modern button with enhanced styling"""
    def __init__(self, text, button_type="primary"):
        super().__init__(text)
        self.button_type = button_type
        self.setMinimumHeight(50)
        self.setFont(QFont("Segoe UI", 11, QFont.Medium))
        self.setCursor(Qt.PointingHandCursor)
        self.apply_style()
    
    def apply_style(self):
        if self.button_type == "primary":
            style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4A90E2, stop:1 #357ABD);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 600;
                text-align: center;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #5BA0F2, stop:1 #4A90E2);
                border: 1px solid #357ABD;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #357ABD, stop:1 #2E6DA4);
            }
            QPushButton:disabled {
                background: #CCCCCC;
                color: #666666;
            }
            """
        elif self.button_type == "secondary":
            style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #F8F9FA, stop:1 #E9ECEF);
                color: #495057;
                border: 2px solid #DEE2E6;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #E9ECEF, stop:1 #DEE2E6);
                border-color: #ADB5BD;
            }
            QPushButton:pressed {
                background: #DEE2E6;
            }
            QPushButton:disabled {
                background: #F8F9FA;
                color: #ADB5BD;
                border-color: #E9ECEF;
            }
            """
        else:  # report buttons
            style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #28A745, stop:1 #1E7E34);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #34CE57, stop:1 #28A745);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #1E7E34, stop:1 #155724);
            }
            """
        
        self.setStyleSheet(style)

class StatusLabel(QLabel):
    """Modern status label with styling"""
    def __init__(self, text="Ready"):
        super().__init__(text)
        self.setFont(QFont("Segoe UI", 9))
        self.setStyleSheet("""
            QLabel {
                color: #6C757D;
                background-color: #F8F9FA;
                border: 1px solid #E9ECEF;
                border-radius: 4px;
                padding: 8px 12px;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.templates_folder = "templates"  # Define templates folder
        self.html_files = []  # Store discovered HTML files
        self.report_buttons = []  # Store dynamically created buttons
        
        self.setup_ui()
        self.setup_connections()
        self.load_config()
        self.discover_html_files()  # Discover HTML files and create buttons

    def discover_html_files(self):
        """Discover HTML files in templates folder and create buttons dynamically"""
        try:
            # Get the directory where the script is located
            script_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
            templates_path = os.path.join(script_dir, self.templates_folder)
            
            print(f"Looking for HTML files in: {templates_path}")
            
            # Check if templates folder exists
            if not os.path.exists(templates_path):
                # Create templates folder if it doesn't exist
                try:
                    os.makedirs(templates_path, exist_ok=True)
                    print(f"✅ Created templates directory: {templates_path}")
                    self.status_label.setText(f"Created templates folder: {self.templates_folder}")
                except Exception as e:
                    print(f"❌ Failed to create templates directory: {e}")
                    self.status_label.setText("Failed to create templates folder")
                    return
            
            # Discover HTML files
            self.html_files = []
            if os.path.exists(templates_path):
                for filename in os.listdir(templates_path):
                    if filename.lower().endswith('.html'):
                        # Validate that it's a proper HTML file (basic check)
                        file_path = os.path.join(templates_path, filename)
                        if self.is_valid_html_file(file_path):
                            self.html_files.append(filename)
                            print(f"✅ Found valid HTML file: {filename}")
            
            # Sort files for consistent ordering
            self.html_files.sort()
            
            # Create buttons dynamically
            self.create_dynamic_report_buttons()
            
            # Update status
            if self.html_files:
                self.status_label.setText(f"Found {len(self.html_files)} HTML report(s) in {self.templates_folder}")
            else:
                self.status_label.setText(f"No HTML files found in {self.templates_folder} folder")
                
        except Exception as e:
            print(f"❌ Error discovering HTML files: {e}")
            self.status_label.setText("Error discovering HTML files")

    def is_valid_html_file(self, file_path):
        """Basic validation to check if file is a valid HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500).lower()  # Read first 500 chars
                # Basic check for HTML content
                return any(tag in content for tag in ['<html', '<head', '<body', '<!doctype'])
        except Exception as e:
            print(f"❌ Error validating HTML file {file_path}: {e}")
            return False

    def create_dynamic_report_buttons(self):
        """Create buttons dynamically based on discovered HTML files"""
        # Clear existing buttons if any
        for button in self.report_buttons:
            button.setParent(None)
            button.deleteLater()
        self.report_buttons.clear()
        
        if not self.html_files:
            # If no HTML files found, show a message
            no_files_label = QLabel("No HTML files found in templates folder")
            no_files_label.setStyleSheet("""
                QLabel {
                    color: #6C757D;
                    font-style: italic;
                    text-align: center;
                    padding: 20px;
                    background-color: #F8F9FA;
                    border: 2px dashed #DEE2E6;
                    border-radius: 8px;
                }
            """)
            no_files_label.setAlignment(Qt.AlignCenter)
            self.reports_layout.addWidget(no_files_label, 0, 0, 1, 2)
            return
        
        # Create buttons for each HTML file
        for i, filename in enumerate(self.html_files):
            # Create a nice display name (remove .html extension and format)
            display_name = self.format_button_name(filename)
            
            # Create button
            button = ModernButton(f"📊 {display_name}", "report")
            button.clicked.connect(lambda checked, f=filename: self.view_report(f))
            self.report_buttons.append(button)
            
            # Add to grid layout (2 columns)
            row = i // 2
            col = i % 2
            self.reports_layout.addWidget(button, row, col)
            
            print(f"✅ Created button for: {filename} -> {display_name}")

    def format_button_name(self, filename):
        """Format filename into a nice button display name"""
        # Remove .html extension
        name = os.path.splitext(filename)[0]
        
        # Replace underscores and hyphens with spaces
        name = name.replace('_', ' ').replace('-', ' ')
        
        # Capitalize words
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name

    def setup_ui(self):
        self.setWindowTitle("Inventory Manager Pro")
        self.setGeometry(100, 100, 700, 700)
        self.setFixedSize(700, 700)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FFFFFF;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #E9ECEF;
                border-radius: 8px;
                margin: 10px 0px;
                padding-top: 20px;
                background-color: #F8F9FA;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px 0 10px;
                color: #495057;
                background-color: #FFFFFF;
                border-radius: 4px;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        self.create_header(main_layout)
        
        # Main actions group
        self.create_main_actions_group(main_layout)
        
        # Reports group (will be populated dynamically)
        self.create_reports_group(main_layout)
        
        # Status and progress
        self.create_status_section(main_layout)
        
        # Add stretch to push everything up
        main_layout.addStretch()

    def create_header(self, parent_layout):
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4A90E2, stop:1 #357ABD);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        title = QLabel("Inventory Manager Pro")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet("color: white; margin: 0;")
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Extract • Transform • Load")
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.8); margin: 0;")
        subtitle.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        parent_layout.addWidget(header_frame)

    def create_main_actions_group(self, parent_layout):
        group = QGroupBox("Data Operations")
        group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Extract button
        self.extract_js_button = ModernButton("🔄 Extract & Convert to JavaScript", "primary")
        self.extract_js_button.setMinimumHeight(60)
        layout.addWidget(self.extract_js_button)
        
        # Refresh templates button
        self.refresh_templates_button = ModernButton("🔄 Refresh Templates", "secondary")
        self.refresh_templates_button.clicked.connect(self.refresh_templates)
        layout.addWidget(self.refresh_templates_button)
        
        parent_layout.addWidget(group)

    def create_reports_group(self, parent_layout):
        self.reports_group = QGroupBox("HTML Reports")
        self.reports_group.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.reports_layout = QGridLayout(self.reports_group)
        self.reports_layout.setSpacing(10)
        
        # Buttons will be added dynamically by discover_html_files()
        
        parent_layout.addWidget(self.reports_group)

    def create_status_section(self, parent_layout):
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #E9ECEF;
                border-radius: 8px;
                text-align: center;
                background-color: #F8F9FA;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4A90E2, stop:1 #357ABD);
                border-radius: 6px;
            }
        """)
        
        # Status label
        self.status_label = StatusLabel("Ready")
        
        parent_layout.addWidget(self.progress_bar)
        parent_layout.addWidget(self.status_label)

    def setup_connections(self):
        self.extract_js_button.clicked.connect(self.extract_and_convert_js)

    def load_config(self):
        try:
            self.file_path, self.file_sqlite, self.js_path, self.js_data = load_environment()
            self.status_label.setText("Configuration loaded successfully")
        except Exception as e:
            QMessageBox.critical(self, "Configuration Error", f"Failed to load environment: {e}")
            self.status_label.setText("Configuration error")
            sys.exit(1)

    def refresh_templates(self):
        """Refresh the templates folder and recreate buttons"""
        self.status_label.setText("Refreshing templates...")
        self.discover_html_files()

    def show_progress(self, show=True):
        self.progress_bar.setVisible(show)
        if show:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.extract_js_button.setEnabled(not show)

    def extract_and_convert_js(self):
        self.show_progress(True)
        self.status_label.setText("Starting extraction...")
        
        # Create and start worker thread
        self.worker = WorkerThread(self.file_path, self.file_sqlite, self.js_path, self.js_data)
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.progress.connect(self.on_progress_update)
        self.worker.start()

    def on_progress_update(self, message):
        self.status_label.setText(message)

    def on_extraction_finished(self, success, message, record_count, duration):
        self.show_progress(False)
        
        if success:
            self.status_label.setText(f"Success! {record_count} records exported in {duration:.2f}s")
            QMessageBox.information(
                self,
                "✅ Export Successful",
                f"Successfully exported {record_count} records to JavaScript.\n\n"
                f"📁 Location: {message}\n"
                f"⏱️ Duration: {duration:.2f} seconds\n\n"
                f"JavaScript data file has been created successfully!\n"
                f"You can now view the HTML reports using the buttons below."
            )
        else:
            self.status_label.setText("Export failed")
            QMessageBox.critical(
                self, 
                "❌ Export Failed", 
                f"The export process encountered an error:\n\n{message}"
            )

    def view_report(self, filename):
        try:
            # Look for the HTML file in the templates folder
            script_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
            html_path = os.path.join(script_dir, self.templates_folder, filename)
            
            if not os.path.exists(html_path):
                QMessageBox.warning(
                    self, 
                    "⚠️ HTML Report Not Found", 
                    f"The report file '{filename}' was not found.\n\n"
                    f"Expected location: {html_path}\n\n"
                    f"To use the HTML reports:\n"
                    f"1. Make sure the HTML report files are in the '{self.templates_folder}' folder\n"
                    f"2. First run 'Extract & Convert to JavaScript' to generate the data\n"
                    f"3. Ensure the HTML files reference the correct JavaScript data file\n\n"
                    f"Click 'Refresh Templates' to rescan the templates folder."
                )
                return

            html_url = f'file:///{html_path.replace(os.sep, "/")}'
            
            if webbrowser.open(html_url):
                self.status_label.setText(f"Opened {filename} in browser")
                QTimer.singleShot(3000, lambda: self.status_label.setText("Ready"))
            else:
                raise Exception("Failed to open default browser")
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "❌ Browser Error", 
                f"Could not open the report:\n\n{str(e)}\n\n"
                f"Try opening the file manually:\n{html_path}"
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Inventory Manager Pro")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Your Organization")
    
    # Apply modern font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())