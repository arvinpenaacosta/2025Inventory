# loc_entry.py

import sys
import json
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox,
    QPushButton, QMenuBar, QAction, QMessageBox
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get JSON_FILE value
json_file = os.getenv("JSON_FILE", "devappData.json")  # fallback to "devappData.json" if not set

def load_devapp_data():
    with open(json_file, "r", encoding="utf-8") as f:
        return json.load(f)

class LocationRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ePx Inventory Location Recorder")

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
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

    def show_about_dialog(self):
        """Display the About dialog with application information."""
        about_text = (
            "ePx Inventory Asset Recorder\n"
            "Version: 1.0.2\n\n"
            "Description: The ePx Inventory Location Recorder is a desktop application designed to streamline the process of collecting and managing inventory data for computer systems within an organization.\n\nIt gathers detailed system information, such as hardware specifications (processor, RAM, etc.), network details (IP and MAC addresses), and software details (OS version, Citrix information), and combines it with user-specified location data (floor, room, and seat). \n\nThe application allows users to select location details through an intuitive interface, review collected data in a summary table, and save it to a SQLite database for inventory tracking. \nOptional reboot functionality is provided post-save for system updates.\n"
            "\nDeveloped by: Arvin Acosta \n"
            "System Engineer, IT NOC, ePerformax © 2025"
        )
        QMessageBox.about(self, "About ePx Inventory Asset Recorder", about_text)

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
        self.submit_btn.show()

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
        """Generate location code when submit is clicked"""
        self.answers["location_code"] = self.generate_location_code()
        
        # Show confirmation if running standalone (for debugging)
        if __name__ == "__main__":
            floor = self.answers.get("floor", "")
            d1 = self.answers.get("D1", "")
            e1 = self.answers.get("E1", "")
            e2 = self.answers.get("E2", "")
            display_text = (
                f"📌 Selected Info:\n"
                f"Floor: {floor}\n"
                f"D1: {d1}\n"
                f"E1: {e1}\n"
                f"E2: {e2}"
            )
            QMessageBox.information(self, "Submission Complete", display_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LocationRecorder()
    window.show()
    sys.exit(app.exec_())