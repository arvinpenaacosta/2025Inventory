import sys
import json
import os
import ast

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox,
    QPushButton, QMenuBar, QAction, QMessageBox
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get JSON_FILE and TASKFOR values
json_file = os.getenv("JSON_FILE", "devappData.json")  # fallback to "devappData.json" if not set
taskfor_values = ast.literal_eval(os.getenv("TASKFOR", "[]"))  # Parse TASKFOR list from .env

ENABLE_LOGGING = os.getenv("LOGGING", "False").lower() in ("1", "true", "yes")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    full_path = os.path.join(base_path, relative_path)
    log_path = os.path.join(os.path.abspath("."), "debug.log")

    if ENABLE_LOGGING:
        with open(log_path, "a") as f:
            f.write(f" Resolved path for {relative_path}: {full_path}\n")
            f.write(f" Files in {base_path}: {os.listdir(base_path)}\n")
            if not os.path.exists(full_path):
                f.write(f" Error: File {full_path} does not exist\n")
            else:
                f.write(f" File {full_path} exists\n")

    return full_path


def load_devapp_data():
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

class LocationRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ePx - GetPCInfo V3a")
        # Set window icon
        icon_path = resource_path("app.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.devappData = load_devapp_data()
        app_font = QFont("Segoe UI", 12)
        self.setFont(app_font)

        self.floor_data = None
        self.room_data = None
        self.answers = {}

        # Create menu bar
        self.menu_bar = QMenuBar(self)
        help_menu = self.menu_bar.addMenu("Help")
        
        # Add About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setFixedSize(300, 400)

        # Place menu bar at the top
        self.layout.setMenuBar(self.menu_bar)

        self.floor_label = QLabel("Select Floor")
        self.floor_combo = QComboBox()
        self.floor_combo.addItem("-- Choose Floor --")
        for floor in self.devappData:
            self.floor_combo.addItem(floor["floor"])
        
        self.floor_combo.currentIndexChanged.connect(self.on_floor_change)

        self.room_label = QLabel("Select Room Type")
        self.room_combo = QComboBox()
        self.room_combo.addItem("-- Choose Room Type --")
        self.room_combo.currentIndexChanged.connect(self.on_room_change)
        self.room_combo.hide()
        self.room_label.hide()

        self.l1_label = QLabel()
        self.l1_combo = QComboBox()
        self.l1_combo.currentIndexChanged.connect(self.on_l1_change)
        self.l1_combo.hide()
        self.l1_label.hide()

        self.e1_label = QLabel()
        self.e1_combo = QComboBox()
        self.e1_combo.currentIndexChanged.connect(self.on_e1_change)
        self.e1_combo.hide()
        self.e1_label.hide()

        self.e2_label = QLabel()
        self.e2_combo = QComboBox()
        self.e2_combo.currentIndexChanged.connect(self.on_e2_change)
        self.e2_combo.hide()
        self.e2_label.hide()

        self.taskfor_label = QLabel("Select Task")
        self.taskfor_combo = QComboBox()
        self.taskfor_combo.addItem("-- Choose Task --")
        for task in taskfor_values:
            self.taskfor_combo.addItem(task)
        if taskfor_values:  # Set default to first value if available
            self.taskfor_combo.setCurrentText(taskfor_values[0])
        self.taskfor_combo.currentIndexChanged.connect(self.on_taskfor_change)
        self.taskfor_combo.hide()
        self.taskfor_label.hide()

        self.submit_btn = QPushButton("Submit")
        self.submit_btn.clicked.connect(self.on_submit)
        self.submit_btn.hide()

        self.layout.addWidget(self.floor_label)
        self.layout.addWidget(self.floor_combo)
        self.layout.addWidget(self.room_label)
        self.layout.addWidget(self.room_combo)
        self.layout.addWidget(self.l1_label)
        self.layout.addWidget(self.l1_combo)
        self.layout.addWidget(self.e1_label)
        self.layout.addWidget(self.e1_combo)
        self.layout.addWidget(self.e2_label)
        self.layout.addWidget(self.e2_combo)
        self.layout.addWidget(self.taskfor_label)
        self.layout.addWidget(self.taskfor_combo)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

    def show_about_dialog(self):
        """Show dialog with information about the application"""
        about_message = """
ePx GetPCInfo Collector
Version: 1.0.3a
2025 Oct. 5

This application is designed to collect and store desktop computer inventory information.

It gathers system details such as hardware specifications, operating system information, and network details. Users can also input location information (floor, room, etc.). All collected data is stored in a SQLite database for inventory management.

Features:
    - Allows users to specify location details
    - Collects system information in the background
    - Displays a summary of all collected data
    - Saves data to a configurable SQLite database
    - Option to reboot system after saving

Developed by: Arvin Acosta
System Engineer, IT NOC, ePerformax © 2025
        """
        QMessageBox.about(self, "ePx GetPCInfo Collector", about_message)

    def on_floor_change(self, index):
        self.room_combo.clear()
        self.room_combo.addItem("-- Choose Room Type --")
        self.room_combo.hide()
        self.room_label.hide()
        self.l1_combo.hide()
        self.l1_label.hide()
        self.e1_combo.hide()
        self.e1_label.hide()
        self.e2_combo.hide()
        self.e2_label.hide()
        self.taskfor_combo.hide()
        self.taskfor_label.hide()
        self.submit_btn.hide()

        if index == 0:
            self.floor_data = None
            return

        self.floor_data = self.devappData[index - 1]
        for room in self.floor_data["rooms"]:
            key = list(room["CO"].keys())[0]
            name = room["CO"][key]
            self.room_combo.addItem(f"{key} - {name}", userData=key)
        self.room_combo.show()
        self.room_label.show()

        self.answers["floor"] = self.floor_data["floor"]

    def on_room_change(self, index):
        self.l1_combo.hide()
        self.l1_label.hide()
        self.e1_combo.hide()
        self.e1_label.hide()
        self.e2_combo.hide()
        self.e2_label.hide()
        self.taskfor_combo.hide()
        self.taskfor_label.hide()
        self.submit_btn.hide()

        if index == 0 or self.floor_data is None:
            self.room_data = None
            return

        key = self.room_combo.itemData(index)
        self.room_data = next((r for r in self.floor_data["rooms"] if key in r["CO"]), None)

        if self.room_data is None:
            return

        self.answers["room"] = key
        self.answers["room_name"] = self.room_data["CO"][key]
        self.answers["D1"] = self.room_data["D1"]

        if "L1" in self.room_data and self.room_data["L1"]:
            self.l1_label.setText(self.room_data["L1"])
            self.populate_combo(self.l1_combo, self.room_data["E1"]["Range"])
            self.l1_label.show()
            self.l1_combo.show()
        else:
            self.show_e1()

    def on_l1_change(self, index):
        if index == 0:
            return
        self.answers["L1"] = self.l1_combo.currentText()

        self.e2_label.setText(self.room_data["E2"]["label"])
        self.populate_combo(self.e2_combo, self.room_data["E2"]["Range"])
        self.e2_label.show()
        self.e2_combo.show()

    def populate_combo(self, combo, range_data):
        combo.clear()
        combo.addItem("-- Choose --")
        if isinstance(range_data, dict):
            for val in range_data.values():
                combo.addItem(str(val))
        else:
            for val in range_data:
                combo.addItem(str(val))

    def show_e1(self):
        if self.room_data is None:
            return

        self.e1_label.setText(self.room_data["E1"]["label"])
        self.populate_combo(self.e1_combo, self.room_data["E1"]["Range"])
        self.e1_label.show()
        self.e1_combo.show()

    def on_e1_change(self, index):
        if index == 0 or self.room_data is None:
            return
        self.answers["E1"] = self.e1_combo.currentText()

        self.e2_label.setText(self.room_data["E2"]["label"])
        self.populate_combo(self.e2_combo, self.room_data["E2"]["Range"])
        self.e2_label.show()
        self.e2_combo.show()

    def on_e2_change(self, index):
        if index == 0:
            return
        self.answers["E2"] = self.e2_combo.currentText()
        self.taskfor_label.show()
        self.taskfor_combo.show()
        self.submit_btn.show()
        if taskfor_values:  # Set default taskfor value to the first item in taskfor_values
            self.answers["taskfor"] = taskfor_values[0]

    def on_taskfor_change(self, index):
        if index == 0:
            self.answers.pop("taskfor", None)  # Remove taskfor if "-- Choose Task --" is selected
            return
        self.answers["taskfor"] = self.taskfor_combo.currentText()

    def generate_location_code(self):
        code_parts = []

        if "floor" in self.answers:
            code_parts.append(self.answers["floor"])
        if "D1" in self.answers:
            code_parts.append(self.answers["D1"])
        if "E1" in self.answers:
            # Add leading zero for single-digit numeric E1
            e1_value = self.answers["E1"]
            try:
                e1_num = int(e1_value)
                if 0 < e1_num < 10:
                    code_parts.append(f"{e1_num:02d}")
                else:
                    code_parts.append(str(e1_value))
            except ValueError:
                code_parts.append(str(e1_value))
        if "E2" in self.answers:
            # Add leading zero for single-digit numeric E2
            e2_value = self.answers["E2"]
            try:
                e2_num = int(e2_value)
                if 0 < e2_num < 10:
                    code_parts.append(f"{e2_num:02d}")
                else:
                    code_parts.append(str(e2_value))
            except ValueError:
                code_parts.append(str(e2_value))

        return "_".join(code_parts)

    def on_submit(self):
        """Generate location code and set flag for VACANT task"""
        self.answers["location_code"] = self.generate_location_code()
        # Set flag to skip system info if taskfor is VACANT
        self.answers["skip_system_info"] = self.answers.get("taskfor") == "VACANT"
        
        # Show confirmation if running standalone (for debugging)
        if __name__ == "__main__":
            floor = self.answers.get("floor", "")
            d1 = self.answers.get("D1", "")
            e1 = self.answers.get("E1", "")
            e2 = self.answers.get("E2", "")
            taskfor = self.answers.get("taskfor", "")
            display_text = (
                f"📌 Selected Info:\n"
                f"Floor: {floor}\n"
                f"D1: {d1}\n"
                f"E1: {e1}\n"
                f"E2: {e2}\n"
                f"Task: {taskfor}"
            )
            QMessageBox.information(self, "Submission Complete", display_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LocationRecorder()
    window.show()
    sys.exit(app.exec_())