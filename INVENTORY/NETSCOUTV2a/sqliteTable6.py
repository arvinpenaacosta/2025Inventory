import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableView, QLineEdit, QPushButton, 
    QHBoxLayout, QMessageBox, QLabel, QGridLayout, QTabWidget, QGroupBox, QComboBox
)
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from configparser import ConfigParser
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt

class DatabaseApp(QWidget):
    def __init__(self):
        super().__init__()

        # Only store dictionary for the second table
        self.second_table_selected_rows_dict = {}

        self.user_level = self.get_user_level()
        self.init_db()
        self.current_page = 0
        self.rows_per_page = 20
        self.total_rows = self.get_total_rows()

        # First Table
        self.process_table_view = QTableView()
        self.process_model = QStandardItemModel(0, 4)
        self.process_model.setHorizontalHeaderLabels(["Station", "Port", "Interface", "Info2"])

        # Main Model for the first table
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable("mapping")
        self.model.select()

        self.init_ui()
        self.load_data()

    def get_user_credentials(self):
        """Read username and password from app.config."""
        config = ConfigParser()
        config.read("app.config")

        # ✅ Read username and password from CREDENTIALS section
        username = config.get("CREDENTIALS", "username", fallback="default_user")
        password = config.get("CREDENTIALS", "password", fallback="default_pass")

        return username, password
    
    def get_db_path(self):
        config = ConfigParser()
        config.read("app.config")
        # ✅ 
        dbPath = config.get("DATABASE", "db", fallback="default_user")
        return dbPath
       
    def get_user_level(self):
        config = ConfigParser()
        config.read("app.config")
        if "LEVEL" in config and config["LEVEL"].get("access", "").lower() == "admin":
            return "admin"
        return "read-only"

    def init_db(self):
        dbPath = self.get_db_path()
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(dbPath)
        if self.user_level == "admin":
            self.db.setConnectOptions("")
        else:
            self.db.setConnectOptions("QSQLITE_OPEN_READONLY")
        if not self.db.open():
            sys.exit(1)
        
        username, password = self.get_user_credentials()
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"DB Path: {dbPath}")

    def init_ui(self):
        self.setWindowTitle("Network Mappings Viewer")
        self.setGeometry(100, 100, 1300, 600)

        layout = QVBoxLayout(self)
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Tabs
        self.tab_mappings = QWidget()
        self.init_mappings_tab()

        self.tab_process = QWidget()
        self.init_process_task_tab()

        self.tab_widget.addTab(self.tab_mappings, "Network Mappings")
        self.tab_widget.addTab(self.tab_process, "Process Task")
        self.setLayout(layout)

    def init_mappings_tab(self):
        mappings_layout = QVBoxLayout()
        filter_group = QGroupBox("Filter Records")
        filter_layout = QGridLayout()

        # Filter Inputs
        filter_layout.addWidget(QLabel("Floor:"), 0, 0)
        self.floor_filter = QLineEdit()
        filter_layout.addWidget(self.floor_filter, 0, 1)

        filter_layout.addWidget(QLabel("Station:"), 1, 0)
        self.station_filter = QLineEdit()
        filter_layout.addWidget(self.station_filter, 1, 1)

        filter_layout.addWidget(QLabel("Port:"), 0, 2)
        self.port_filter = QLineEdit()
        filter_layout.addWidget(self.port_filter, 0, 3)

        filter_layout.addWidget(QLabel("Interface:"), 1, 2)
        self.interface_filter = QLineEdit()
        filter_layout.addWidget(self.interface_filter, 1, 3)

        filter_layout.addWidget(QLabel("Info2:"), 2, 0)
        self.info2_filter = QLineEdit()
        filter_layout.addWidget(self.info2_filter, 2, 1)

        # Search and Transfer Buttons
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.search_button, 2, 3)

        self.select_button = QPushButton("Select for Process")
    # Set button size
        #self.select_button.setFixedSize(220, 100)  # Width: 220, Height: 100
    # Set font size
        #font = self.select_button.font()
        #font.setPointSize(12)  # Increase the font size
        #self.select_button.setFont(font)

        self.select_button.clicked.connect(self.select_for_process)
        filter_layout.addWidget(self.select_button, 2, 4)

        filter_group.setLayout(filter_layout)
        mappings_layout.addWidget(filter_group)

        # First Table
        self.table_view = QTableView()
        self.table_view.setModel(self.model)

        # Connect selection handler (without dictionary creation)
        selection_model = self.table_view.selectionModel()
        selection_model.selectionChanged.connect(self.print_selected_rows)

        mappings_layout.addWidget(self.table_view)

        button_layout = QHBoxLayout()
        self.first_button = QPushButton("First")
        self.first_button.clicked.connect(self.go_first)
        button_layout.addWidget(self.first_button)

        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.go_previous)
        button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.go_next)
        button_layout.addWidget(self.next_button)

        self.last_button = QPushButton("Last")
        self.last_button.clicked.connect(self.go_last)
        button_layout.addWidget(self.last_button)

        self.page_label = QLabel("Page 1 of 1")
        button_layout.addWidget(self.page_label)
        mappings_layout.addLayout(button_layout)
        self.tab_mappings.setLayout(mappings_layout)

    def init_process_task_tab(self):
        layout = QHBoxLayout(self.tab_process)

        # Second Table Layout
        table_layout = QVBoxLayout()
        self.process_table_view.setModel(self.process_model)

        # Connect selection handler (dictionary creation only for second table)
        self.process_table_view.selectionModel().selectionChanged.connect(self.on_process_row_selected)

        table_layout.addWidget(self.process_table_view)

        # ✅ Row count label
        self.row_count_label = QLabel("Selected Rows: 0")
        table_layout.addWidget(self.row_count_label)
        layout.addLayout(table_layout)
        
        # Action Tab Widget with buttons
        self.action_tab_widget = QTabWidget()
        # ✅ ***********************************
    # --- Clear Port Tab ---
        clear_port_tab = QWidget()
        clear_port_layout = QVBoxLayout(clear_port_tab)
        
        clear_port_button = QPushButton("Clear Port Execute")
        clear_port_button.setFixedSize(300, 100)
        clear_port_layout.setAlignment(Qt.AlignCenter)
        clear_port_button.clicked.connect(self.display_second_table_rows)

        # ✅ Increase the font size
        font = clear_port_button.font()
        font.setPointSize(16)  # Adjust the font size (larger)
        clear_port_button.setFont(font)
        
        clear_port_layout.addWidget(clear_port_button)
        self.action_tab_widget.addTab(clear_port_tab, "Clear Port")


    # --- Clear Sticky Port Tab ---
        clear_sticky_tab = QWidget()
        clear_sticky_layout = QVBoxLayout(clear_sticky_tab)
        
        clear_sticky_button = QPushButton("Clear Sticky Port Execute")
        clear_sticky_button.setFixedSize(350, 100)
        clear_sticky_layout.setAlignment(Qt.AlignCenter)
        clear_sticky_button.clicked.connect(self.display_second_table_rows)
        
        # ✅ Increase the font size
        font = clear_sticky_button.font()
        font.setPointSize(16)  # Adjust the font size (larger)
        clear_sticky_button.setFont(font)
        
        clear_sticky_layout.addWidget(clear_sticky_button)
        self.action_tab_widget.addTab(clear_sticky_tab, "Clear Sticky Port")

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        # --- Change VLAN Tab ---
        change_vlan_tab = QWidget()
        change_vlan_layout = QGridLayout(change_vlan_tab)

        # VLAN Dropdown
        self.vlan_dropdown = QComboBox()
        self.vlan_dropdown.setFixedSize(200, 40)  # Width: 200px, Height: 40px (slightly taller)
        self.vlan_dropdown.currentIndexChanged.connect(self.toggle_custom_vlan)

        # Add VLAN Dropdown with Label
        change_vlan_layout.addWidget(QLabel("Select VLAN:"), 0, 0, alignment=Qt.AlignRight)
        change_vlan_layout.addWidget(self.vlan_dropdown, 0, 1)

        # Custom VLAN Textbox
        self.custom_vlan_input = QLineEdit()
        self.custom_vlan_input.setFixedSize(200, 40)
        self.custom_vlan_input.setPlaceholderText("Enter custom VLAN")
        self.custom_vlan_input.setEnabled(False)  # Initially disabled

        # Add Custom VLAN Textbox with Label
        change_vlan_layout.addWidget(QLabel("Custom VLAN:"), 1, 0, alignment=Qt.AlignRight)
        change_vlan_layout.addWidget(self.custom_vlan_input, 1, 1)

        # VLAN Execute Button
        change_vlan_button = QPushButton("Change VLAN Execute")
        change_vlan_button.setFixedSize(350, 120)  # Larger button size
        change_vlan_button.clicked.connect(self.execute_vlan_change)

        # ✅ Increase the font size
        font = change_vlan_button.font()
        font.setPointSize(14)  # Bigger font size
        change_vlan_button.setFont(font)

        # Center the button across the grid columns
        change_vlan_layout.addWidget(change_vlan_button, 2, 0, 1, 2, alignment=Qt.AlignCenter)





        # Add the tab
        self.action_tab_widget.addTab(change_vlan_tab, "Change VLAN")

        # ✅ Load VLANs into the dropdown
        self.load_vlans()


        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # --- Change Voice Tab ---
        change_voice_tab = QWidget()
        change_voice_layout = QVBoxLayout(change_voice_tab)
        
        change_voice_button = QPushButton("Change Voice Execute")
        change_voice_button.clicked.connect(self.display_second_table_rows)
        
        change_voice_layout.addWidget(change_voice_button)
        self.action_tab_widget.addTab(change_voice_tab, "Change Voice")

    # --- Show Interface VLAN Tab ---
        show_interface_vlan_tab = QWidget()
        show_interface_vlan_layout = QVBoxLayout(show_interface_vlan_tab)
        
        show_interface_vlan_button = QPushButton("Show Interface VLAN Execute")
        show_interface_vlan_button.clicked.connect(self.display_second_table_rows)
        
        show_interface_vlan_layout.addWidget(show_interface_vlan_button)
        self.action_tab_widget.addTab(show_interface_vlan_tab, "Show Interface VLAN")

        # Add the single QTabWidget to the main layout
        layout.addWidget(self.action_tab_widget)

        # ✅ ***********************************

    # ✅ Toggle logic function
    def toggle_custom_vlan(self):
        print(f"Current xVLAN selection: {self.vlan_dropdown.currentText()}")  # Debug
        if self.vlan_dropdown.currentText().endswith("Custom"):
            self.custom_vlan_input.setEnabled(True)
        else:
            self.custom_vlan_input.setEnabled(False)
            self.custom_vlan_input.clear()

    # ✅ load_vlans
    def load_vlans(self):
        """Load VLANs into the dropdown from the database."""
        query = QSqlQuery("SELECT vlan, name FROM vlans", self.db)

        # Add VLANs with their name in the dropdown
        while query.next():
            vlan_value = query.value(0)
            vlan_name = query.value(1)
            self.vlan_dropdown.addItem(f"{vlan_value} - {vlan_name}", vlan_value)

        # Add "Custom" option
        self.vlan_dropdown.addItem("Custom")


    # ✅ First Table: Print selected rows only
    def print_selected_rows(self):
        """Print the selected rows from the first table (no dictionary)."""
        selection_model = self.table_view.selectionModel()
        if selection_model.hasSelection():
            print("\nFirst Table Selection:")
            for index in selection_model.selectedRows():
                row_data = {
                    "Station": self.model.data(self.model.index(index.row(), 0)),
                    "Port": self.model.data(self.model.index(index.row(), 1)),
                    "Interface": self.model.data(self.model.index(index.row(), 2)),
                    "Info2": self.model.data(self.model.index(index.row(), 3))
                }
                print(row_data)

    # ✅ Second Table Selection Handler (with dictionary storage)
    def on_process_row_selected(self):
        self.second_table_selected_rows_dict.clear()
        selection_model = self.process_table_view.selectionModel()

        if selection_model.hasSelection():
            for index in selection_model.selectedRows():
                row_data = {
                    "Station": self.process_model.item(index.row(), 0).text(),
                    "Port": self.process_model.item(index.row(), 1).text(),
                    "Interface": self.process_model.item(index.row(), 2).text(),
                    "Info2": self.process_model.item(index.row(), 3).text()
                }
                self.second_table_selected_rows_dict[index.row()] = row_data

        self.row_count_label.setText(f"Selected Rows: {len(self.second_table_selected_rows_dict)}")
        print("Second Table Selection:", self.second_table_selected_rows_dict)

    # ✅ Display Second Table Rows
    def display_second_table_rows(self):
        msg = QMessageBox()
        msg.setWindowTitle("Selected Rows from Second Table")
        msg.setText(str(self.second_table_selected_rows_dict))
        msg.exec_()

    def load_data(self):
        """Load paginated data."""
        offset = self.current_page * self.rows_per_page
        query = QSqlQuery(self.db)
        query.prepare("SELECT * FROM mapping LIMIT ? OFFSET ?")
        query.addBindValue(self.rows_per_page)
        query.addBindValue(offset)

        if not query.exec_():
            print("❌ Query failed:", query.lastError().text())
            return

        self.model.setQuery(query)

        total_pages = max(1, (self.total_rows + self.rows_per_page - 1) // self.rows_per_page)
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")


    def get_total_rows(self):
        query = QSqlQuery("SELECT COUNT(*) FROM mapping", self.db)
        if query.next():
            return query.value(0)
        return 0

    def apply_filters(self):
        """Apply filters to the table."""
        filters = []

        # ✅ Ensure column names match the SQLite table schema
        if self.floor_filter.text():
            filters.append(f"floor LIKE '%{self.floor_filter.text()}%'")
        if self.station_filter.text():
            filters.append(f"station LIKE '%{self.station_filter.text()}%'")
        if self.port_filter.text():
            filters.append(f"port LIKE '%{self.port_filter.text()}%'")
        if self.interface_filter.text():
            filters.append(f"interface LIKE '%{self.interface_filter.text()}%'")
        if self.info2_filter.text():
            filters.append(f"info2 LIKE '%{self.info2_filter.text()}%'")

        # ✅ Apply the filter directly to the model
        if filters:
            filter_query = " AND ".join(filters)
            print("Applying Filter:", filter_query)
            self.model.setFilter(filter_query)  # 🔥 Apply the filter to the model
        else:
            self.model.setFilter("")  # Remove the filter if no input is provided

        self.model.select()


    def select_for_process(self):
        """Display only selected rows in the Process Task tab table with desired headers."""
        selected = self.table_view.selectionModel().selectedRows()

        if not selected:
            QMessageBox.information(self, "No Selection", "No rows selected.")
            return

        # ✅ Ensure we're working with the right model
        if not isinstance(self.process_model, QStandardItemModel):
            print("⚠️ Switching to QStandardItemModel.")
            self.process_model = QStandardItemModel(0, 4)
            self.process_model.setHorizontalHeaderLabels(["Station", "Port", "Interface", "Info2"])
            self.process_table_view.setModel(self.process_model)

        # ✅ Clear previous data
        self.process_model.removeRows(0, self.process_model.rowCount())

        headers = ["station", "port", "interface", "info2"]

        # ✅ Extract only the required columns
        for index in selected:
            row_data = []
            for header in headers:
                col_index = self.model.record().indexOf(header)
                if col_index != -1:
                    value = str(self.model.data(self.model.index(index.row(), col_index)))
                    row_data.append(value)

            # ✅ Append the selected row to the table
            items = [QStandardItem(value) for value in row_data]
            self.process_model.appendRow(items)

        print("✅ Process Task Table updated with selected rows!")       
        
        # ✅ Automatically switch to the "Process Task" tab
        self.tab_widget.setCurrentIndex(1)  # "Process Task" tab index (0-based)
    


    def execute_vlan_change(self):
        """Execute VLAN change with dropdown or custom value."""
        vlan_value = ""

        #print(f"Dropdown: {self.vlan_dropdown.currentText()} | Custom: {self.custom_vlan_input.text().strip()}")

        # Check if "Custom" is selected
        if self.vlan_dropdown.currentText() == "000 - Custom":

            vlan_value = self.custom_vlan_input.text().strip()
            if not vlan_value:  # Ensure input isn't empty
                QMessageBox.warning(self, "Invalid VLAN", "Please enter a custom VLAN value.")
                return
        else:
            vlan_value = self.vlan_dropdown.currentData()  # Use dropdown value

        if not vlan_value:  # Final validation
            QMessageBox.warning(self, "No VLAN Selected", "Please select or enter a VLAN.")
            return


        msg = QMessageBox()
        msg.setWindowTitle("VLAN Execution")
        msg.setText(f"Selected VLANX: {vlan_value}\nRows: {self.second_table_selected_rows_dict}")
        msg.exec_()
    # __________________________________________________
    # ✅ Pagination Controls
    def go_first(self): self.current_page = 0; self.load_data()
    def go_previous(self): self.current_page -= 1; self.load_data()
    def go_next(self): self.current_page += 1; self.load_data()
    def go_last(self): self.current_page = (self.total_rows // self.rows_per_page); self.load_data()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DatabaseApp()
    window.show()
    sys.exit(app.exec_())
