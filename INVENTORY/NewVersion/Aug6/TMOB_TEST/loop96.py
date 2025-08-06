# FileWatcher.py

import os
import sqlite3
import time
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import polars as pl
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox,
                            QMenuBar, QMenu, QAction)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QFont
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Global debug flag
DEBUG_MODE = False

def debug_print(message):
    """Print message only if debugging is enabled"""
    if DEBUG_MODE:
        print(message)

class FileChangeHandler(FileSystemEventHandler):
    """Handle file system events for the database file"""
    def __init__(self, file_path, callback):
        self.file_path = file_path
        self.callback = callback
        self.last_modified = None
        debug_print(f"Initializing FileChangeHandler for {file_path}")

    def on_any_event(self, event):
        """Handle any file system event (modified, created, opened, etc.)"""
        if event.src_path == self.file_path and not event.is_directory:
            debug_print(f"Event detected: {event.src_path}, type: {event.event_type}")
            try:
                current_modified = os.path.getmtime(self.file_path)
                if self.last_modified != current_modified:
                    debug_print(f"File changed: {self.file_path}, timestamp: {current_modified}")
                    self.last_modified = current_modified
                    self.callback()
            except Exception as e:
                debug_print(f"Error checking file modification: {e}")

class ExtractorThread(QThread):
    """Thread for running extraction process"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.running = True
        
    def run(self):
        try:
            self.extract_and_save()
        except Exception as e:
            self.log_signal.emit(f"❌ Error: {str(e)}")
        finally:
            self.finished_signal.emit()
    
    def stop(self):
        self.running = False
        
    def extract_and_save(self):
        # Reload .env file before extraction
        try:
            if os.path.exists('.env'):
                load_dotenv('.env')  # Explicitly load .env from current directory
                self.gui.load_env_config()  # Update configuration via GUI instance
                self.config = self.gui.config  # Sync config with GUI's updated config
                self.log_signal.emit("✅ Reloaded .env file")
            else:
                self.log_signal.emit("⚠️ No .env file found in current directory, using existing config")
        except Exception as e:
            self.log_signal.emit(f"❌ Error reloading .env: {e}, using existing config")


        db_path = os.path.join(self.config['file_path'], f"{self.config['db_name']}.db")
        query_file = os.path.join(self.config['file_path'], 'queries.json')
        
        # Check if queries.json exists
        if not os.path.exists(query_file):
            self.log_signal.emit(f"⚠️ Query file not found: {query_file}, using default query")
            # Fallback to default query
            js_file_path = os.path.join(self.config['js_path'], self.config['js_data'])
            sql = f"SELECT * FROM {self.config['sqlite_table']}"
            self.log_signal.emit("🚀 Starting extraction for default query")
            data = self.extract_table_data(db_path, self.config['sqlite_table'], sql)
            if not data:
                self.log_signal.emit("⚠️ No data extracted for default query")
                return
                
            self.log_signal.emit("🔄 Processing data for default query...")
            processed = self.process_data(data)
            self.log_signal.emit(f"👍👍👍 Saving to {self.config['js_data']}...")
            self.save_to_js(processed, js_file_path, "default query")
            return
            
        # Load queries from JSON file
        try:
            with open(query_file, 'r') as file:
                json_data = json.load(file)
                queries = json_data.get('queries', {})
        except Exception as e:
            self.log_signal.emit(f"❌ Error reading query file: {e}")
            return
            
        if not queries:
            self.log_signal.emit("⚠️ No queries found in JSON file")
            return
            
        # Loop through each query
        for query_key, query_info in queries.items():
            if not self.running:
                self.log_signal.emit("🛑 Extraction stopped")
                break
                
            sql = query_info.get('query')
            js_file_name = query_info.get('jsfile')
            if not sql:
                self.log_signal.emit(f"❌ No query found for key: {query_key}")
                continue
            if not js_file_name:
                self.log_signal.emit(f"❌ No jsfile specified for query: {query_key}")
                continue
                
            # Append .js extension to the filename
            js_file_name = f"{js_file_name}.js"
            js_file_path = os.path.join(self.config['js_path'], js_file_name)
            
            # Extract data
            self.log_signal.emit(f"🚀 Starting extraction for query '{query_key}'")
            data = self.extract_table_data(db_path, self.config['sqlite_table'], sql)
            if not data:
                self.log_signal.emit(f"⚠️ No data extracted for query: {query_key}")
                continue
                
            # Process data
            self.log_signal.emit(f"🔄⚠️ Processing data for '{query_key}'...")
            processed = self.process_data(data)
            
            # Save to JS file
            self.log_signal.emit(f"👍👍👍 Saving to {js_file_name}...")
            self.save_to_js(processed, js_file_path, query_key)
        
    def extract_table_data(self, db_path, table_name, sql_query):
        """Extract data from specified table using provided query"""
        if not os.path.exists(db_path):
            self.log_signal.emit(f"❌ Database not found: {db_path}")
            return []
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                self.log_signal.emit(f"❌ Table '{table_name}' not found")
                conn.close()
                return []
            
            rows = conn.execute(sql_query).fetchall()
            conn.close()
            
            data = [{k: row[k] for k in row.keys()} for row in rows]
            self.log_signal.emit(f"✅ Extracted {len(data)} rows using query")
            return data
            
        except Exception as e:
            self.log_signal.emit(f"❌ Database error: {e}")
            if 'conn' in locals():
                conn.close()
            return []

    def process_data(self, data):
        """Process data using Polars"""
        try:
            if not data:
                return []
                
            df = pl.DataFrame(data)
            
            # Process timestamp columns
            timestamp_cols = [col for col in df.columns if 'timestamp' in col.lower() or 'date' in col.lower()]
            for col in timestamp_cols:
                try:
                    df = df.with_columns([
                        pl.col(col)
                        .str.strptime(pl.Datetime, format='%Y-%m-%d %H:%M:%S', strict=False)
                        .fill_null(pl.col(col))
                        .alias(col)
                    ])
                except:
                    pass
            
            # Sort by timestamp if available
            if timestamp_cols:
                processed = df.sort(timestamp_cols[0], descending=True).to_dicts()
            else:
                processed = df.to_dicts()
                
            self.log_signal.emit(f"✅ Processed {len(processed)} records")
            return processed
            
        except Exception as e:
            self.log_signal.emit(f"⚠️ Processing error: {e}")
            return data

    def save_to_js(self, data, output_path, query_key):
        """Save data to JavaScript file with QueryName and DataIn variables"""
        try:
            # Create directory if needed
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            js_content = f"""// Auto-generated on {datetime.now()}
// Generated by SQLite Extractor GUI
var QueryName = "{query_key}";
const DataIn = {json.dumps(data, ensure_ascii=False, indent=2, default=str)};

//if (typeof window !== 'undefined') {{
//    window.DataIn = DataIn;
//}}
"""

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            self.log_signal.emit(f"✅ Saved {os.path.basename(output_path)} ({len(data)} records) - {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.log_signal.emit(f"❌ Write error: {e}")

class SQLiteExtractorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.extractor_thread = None
        self.observer = None
        self.fallback_timer = None
        self.config = {}
        self.is_listening = False
        self.init_ui()
        self.load_env_config()
        
    def init_ui(self):
        self.setWindowTitle("SQLite to JS Extractor")
        self.setGeometry(100, 100, 400, 350)
        self.setFixedSize(400, 350)
        
        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        file_menu.addAction(about_action)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # WPROGRAM label
        self.wprogram_label = QLabel("Loading...")
        self.wprogram_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.wprogram_label.setStyleSheet("color: #2c3e50; margin: 5px;")
        self.wprogram_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.wprogram_label)
        
        # Status display (process box)
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 10px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.status_text)
        
        # Start Listening button
        self.start_btn = QPushButton("Start Listening")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.start_btn.clicked.connect(self.start_listening)
        self.start_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        self.start_btn.customContextMenuRequested.connect(self.single_extraction)
        layout.addWidget(self.start_btn)
        
        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_listening)
        self.stop_btn.setVisible(False)
        layout.addWidget(self.stop_btn)
        
        # Load .env button
        self.load_env_btn = QPushButton("Load .env")
        self.load_env_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.load_env_btn.clicked.connect(self.load_env_file)
        layout.addWidget(self.load_env_btn)
        
        # PID label
        self.pid_label = QLabel(f"PID: {os.getpid()}")
        self.pid_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #6c757d;
                margin: 5px;
                text-align: center;
            }
        """)
        self.pid_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pid_label)
        
        # Add some styling to the main window
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QLabel {
                font-size: 11px;
            }
        """)
    
    def show_about_dialog(self):
        """Show About dialog with app description and developer info"""
        about_text = (
            "This application monitors a SQLite database file for changes and extracts records "
            "to JavaScript files based on queries in queries.json. If queries.json is not found, "
            "it uses a default SELECT * query and saves to the JS_DATA file. It supports automatic "
            "monitoring with watchdog and polling, as well as manual extraction via right-click. "
            "Configuration is loaded from a .env file.\n\n"
            "Developed by BitKindle - 2025"
        )
        QMessageBox.about(self, "About SQLite to JS Extractor", about_text)
    
    def load_env_config(self):
        """Load configuration from .env file"""
        try:
            if os.path.exists('.env'):
                load_dotenv()
                self.config = {
                    'wprogram': os.getenv('WPROGRAM', 'Unknown'),
                    'file_path': os.getenv('FILE_PATH', ''),
                    'db_name': os.getenv('FILE_SQLITE', ''),
                    'js_path': os.getenv('JS_PATH', ''),
                    'js_data': os.getenv('JS_DATA', 'DataIn.js'),
                    'sqlite_table': os.getenv('SQLITETABLE', ''),
                }
                self.wprogram_label.setText(self.config['wprogram'])
                self.log_message(f"✅ Loaded .env configuration: {self.config['wprogram']}")
                self.log_message(f"===============================================")
            else:
                self.wprogram_label.setText("No .env")
                self.log_message("⚠️ No .env file found")
        except Exception as e:
            self.wprogram_label.setText("Error")
            self.log_message(f"❌ Error loading .env: {e}")
    
    def load_env_file(self):
        """Load .env file via file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .env file", "", "Environment files (*.env);;All files (*)")
        if file_path:
            try:
                load_dotenv(file_path)
                self.load_env_config()
                self.log_message(f"✅ Loaded: {os.path.basename(file_path)}")
            except Exception as e:
                self.log_message(f"❌ Error: {e}")
    
    def log_message(self, message):
        """Add message to status text"""
        self.status_text.append(f"{datetime.now().strftime('%H:%M:%S')} - {message}")
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )
    
    def start_listening(self):
        """Start listening for file changes"""
        if not self.config.get('file_path') or not self.config.get('db_name'):
            QMessageBox.warning(self, "Warning", "Please load a valid .env file first!")
            return
        
        # Hide start button, show stop button, disable load .env
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(True)
        self.load_env_btn.setEnabled(False)
        self.is_listening = True
        
        # Start file monitoring
        self.start_file_monitoring()
        self.log_message("🚀 Started continuous listening")
    
    def stop_listening(self):
        """Stop listening and extraction"""
        if self.extractor_thread:
            self.extractor_thread.stop()
            self.extractor_thread.wait()
        self.stop_file_monitoring()
        self.extraction_finished()
        self.log_message("🛑 Listening stopped")
    
    def xsingle_extraction(self, pos):
        """Perform a single extraction when right-clicking Start Listening"""
        debug_print("Right-click event triggered")
        if not self.config.get('file_path') or not self.config.get('db_name'):
            self.log_message("❌ Missing configuration: FILE_PATH or FILE_SQLITE")
            QMessageBox.warning(self, "Warning", "Please load a valid .env file first!")
            return
        
        if not self.extractor_thread or not self.extractor_thread.isRunning():
            if not self.is_listening:
                self.start_btn.setVisible(False)
                self.stop_btn.setVisible(True)
                self.load_env_btn.setEnabled(False)
            
            self.extractor_thread = ExtractorThread(self.config)
            self.extractor_thread.log_signal.connect(self.log_message)
            self.extractor_thread.finished_signal.connect(self.extraction_completed)
            self.extractor_thread.start()
            self.log_message("🚀 Starting single extraction...")

    def single_extraction(self, pos):
        """Perform a single extraction when right-clicking Start Listening, reloading .env first"""
        debug_print("Right-click event triggered")
        
        # Reload .env file before extraction
        try:
            if os.path.exists('.env'):
                load_dotenv('.env')  # Explicitly load .env from current directory
                self.load_env_config()  # Update configuration
                self.log_message("✅ Reloaded .env file")
            else:
                self.log_message("⚠️ No .env file found in current directory")
                QMessageBox.warning(self, "Warning", "No .env file found in current directory!")
                return
        except Exception as e:
            self.log_message(f"❌ Error reloading .env: {e}")
            QMessageBox.warning(self, "Warning", "Failed to reload .env file!")
            return
        
        if not self.config.get('file_path') or not self.config.get('db_name'):
            self.log_message("❌ Missing configuration: FILE_PATH or FILE_SQLITE")
            QMessageBox.warning(self, "Warning", "Please load a valid .env file first!")
            return
        
        if self.extractor_thread and self.extractor_thread.isRunning():
            self.log_message("⚠️ Extraction already in progress, please wait...")
            return
        
        self.extractor_thread = ExtractorThread(self.config)
        self.extractor_thread.log_signal.connect(self.log_message)
        self.extractor_thread.finished_signal.connect(self.extraction_completed)
        self.extractor_thread.start()
        self.log_message("🚀 Starting single extraction...") 

    def extraction_completed(self):
        """Handle completion of an extraction without stopping listening"""
        self.extractor_thread = None
        if self.is_listening:
            self.log_message("✅ Extraction completed, continuing to monitor...")
        else:
            self.start_btn.setVisible(True)
            self.stop_btn.setVisible(False)
            self.load_env_btn.setEnabled(True)
            self.log_message("✅ Single extraction completed")
            self.log_message("===============================")

    def extraction_finished(self):
        """Reset UI when listening is stopped"""
        self.start_btn.setVisible(True)
        self.stop_btn.setVisible(False)
        self.load_env_btn.setEnabled(True)
        self.is_listening = False
        self.extractor_thread = None
        self.log_message("🏁 Operation completed")
    
    def closeEvent(self, event):
        """Handle form closure to stop monitoring"""
        if self.is_listening:
            self.stop_file_monitoring()
        event.accept()
    
    def start_file_monitoring(self):
        """Start monitoring the database file for changes"""
        if not self.config.get('file_path') or not self.config.get('db_name'):
            self.log_message("❌ Missing configuration: FILE_PATH or FILE_SQLITE")
            return
        db_path = os.path.join(self.config['file_path'], f"{self.config['db_name']}.db")
        db_dir = self.config['file_path']
        query_file = os.path.join(self.config['file_path'], 'queries.json')
        
        if not os.path.exists(db_dir):
            self.log_message(f"❌ Directory not found: {db_dir}")
            return
        if not os.path.exists(db_path):
            self.log_message(f"❌ Database file not found: {db_path}")
            return
            
        self.observer = Observer()
        event_handler = FileChangeHandler(db_path, self.trigger_extraction)
        query_event_handler = FileChangeHandler(query_file, lambda: self.log_message("📝 Query file updated"))
        self.observer.schedule(event_handler, db_dir, recursive=False)
        if os.path.exists(query_file):
            self.observer.schedule(query_event_handler, self.config['file_path'], recursive=False)
        self.observer.start()
        self.log_message(f"🔍 Monitoring {self.config['db_name']}.db" + (f" and {query_file}" if os.path.exists(query_file) else ""))
        
        # Start fallback polling
        self.start_fallback_polling(db_path)
    
    def stop_file_monitoring(self):
        """Stop monitoring the database file"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.log_message("🛑 File monitoring stopped")
        if self.fallback_timer:
            self.fallback_timer.stop()
            self.fallback_timer = None
            self.log_message("🛑 Fallback polling stopped")
    
    def start_fallback_polling(self, db_path):
        """Start fallback polling in case watchdog misses events"""
        self.fallback_timer = QTimer()
        self.fallback_timer.timeout.connect(lambda: self.check_file_update(db_path))
        self.fallback_timer.start(5000)  # Check every 5 seconds
        self.log_message("🔄 Started fallback polling")
    
    def check_file_update(self, db_path):
        """Check if the database file has been updated"""
        try:
            current_modified = os.path.getmtime(db_path)
            if not hasattr(self, 'last_db_modified') or self.last_db_modified != current_modified:
                self.last_db_modified = current_modified
                self.log_message(f"📝 Detected change in {self.config['db_name']}.db (polling)")
                self.trigger_extraction()
        except Exception as e:
            self.log_message(f"❌ Polling error: {e}")
    
    def trigger_extraction(self):
        """Trigger extraction when file changes"""
        if not self.extractor_thread or not self.extractor_thread.isRunning():
            if not self.is_listening:
                self.start_btn.setVisible(False)
                self.stop_btn.setVisible(True)
                self.load_env_btn.setEnabled(False)
                self.is_listening = True
            
            self.extractor_thread = ExtractorThread(self.config)
            self.extractor_thread.log_signal.connect(self.log_message)
            self.extractor_thread.finished_signal.connect(self.extraction_completed)
            self.extractor_thread.start()
            self.log_message(f"📝 Detected change in {self.config['db_name']}.db")

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = SQLiteExtractorGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()