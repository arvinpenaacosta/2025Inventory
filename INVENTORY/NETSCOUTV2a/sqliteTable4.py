import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableView, QLineEdit, QPushButton,
    QHBoxLayout, QMessageBox, QLabel, QGridLayout, QTabWidget, QGroupBox, QTextEdit
)
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from configparser import ConfigParser
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class DatabaseApp(QWidget):
    # 1✅-----------------------------------------------
    def __init__(self):
        super().__init__()

        # Initialize User Level
        self.user_level = self.get_user_level()

        # Initialize Database
        self.init_db()

        # Initialize Pagination Variables
        self.current_page = 0
        self.rows_per_page = 20
        self.total_rows = self.get_total_rows()


        self.process_table_view = QTableView()
        self.process_model = QSqlTableModel(self, self.db)
        self.process_model = QStandardItemModel(0, 4)  # 4 columns for Station, Port, Interface, Info2
        self.process_model.setHorizontalHeaderLabels(["Station", "Port", "Interface", "Info2"])


        # Initialize the model
        self.model = QSqlTableModel(self, self.db)
        self.model.setTable("mapping")
        self.model.select()

        # Initialize the UI with tabs
        self.init_ui()

        # Load Data
        self.load_data()

    # 2✅-----------------------------------------------
    def get_user_level(self):
        """Read user level from app.config."""
        config = ConfigParser()
        config.read("app.config")

        if "LEVEL" in config and config["LEVEL"].get("access", "").lower() == "admin":
            return "admin"
        return "read-only"

    # -----------------------------------------------
    def init_db(self):
        """Initialize the SQLite database connection with access permissions."""
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("DB/epmap.db")

        # Set Connection Permissions
        if self.user_level == "admin":
            self.db.setConnectOptions("")  # Full access for admin
            print("✅ Admin: Full access granted.")
        else:
            self.db.setConnectOptions("QSQLITE_OPEN_READONLY")  # Read-only access
            print("🔒 Read-only mode enabled.")

        if not self.db.open():
            print("❌ Failed to open database.")
            sys.exit(1)

        print("✅ Database connected successfully with", self.user_level, "permissions.")

    # -----------------------------------------------
    def init_ui(self):
        """Initialize the UI with tabs."""
        self.setWindowTitle("Network Mappings Viewer")
        self.setGeometry(100, 100, 1200, 600)

        # Main layout
        layout = QVBoxLayout(self)

        # ✅ Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # ✅ Tab 1: Network Mappings
        self.tab_mappings = QWidget()
        self.init_mappings_tab()

        # ✅ Tab 2: Process Task
        self.tab_process = QWidget()
        self.init_process_task_tab()

        # ✅ Add tabs
        self.tab_widget.addTab(self.tab_mappings, "Network Mappings")
        self.tab_widget.addTab(self.tab_process, "Process Task")

        self.setLayout(layout)

    # -----------------------------------------------
    def init_mappings_tab(self):
        """Initialize the mappings tab."""
        mappings_layout = QVBoxLayout()

        # Create filter section inside the tab
        filter_group = QGroupBox("Filter Records")
        filter_layout = QGridLayout()

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

        # ✅ Add Search and "Select for Process" button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.search_button, 2, 3)

        self.select_button = QPushButton("Select for Process")
        self.select_button.clicked.connect(self.select_for_process)
        filter_layout.addWidget(self.select_button, 2, 4)

        filter_group.setLayout(filter_layout)
        mappings_layout.addWidget(filter_group)

        # ✅ Table View
        self.table_view = QTableView()
        self.table_view.setModel(self.model)  # Set model

        # 🔥 Add row selection handler
        selection_model = self.table_view.selectionModel()
        selection_model.selectionChanged.connect(self.on_row_selected)  # ✅ FIXED

        mappings_layout.addWidget(self.table_view)

        # ✅ Navigation and Controls
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

        # Add the Mappings tab layout to the tab widget
        self.tab_mappings.setLayout(mappings_layout)

    # ✅-----------------------------------------------
    def init_process_task_tab(self):
        """Initialize the Process Task tab with a table view for selected rows."""
        layout = QVBoxLayout(self.tab_process)

        # ✅ Ensure the table uses QStandardItemModel
        self.process_model = QStandardItemModel(0, 4)  # 4 columns
        self.process_model.setHorizontalHeaderLabels(["Station", "Port", "Interface", "Info2"])

        # ✅ Use QStandardItemModel for the table view
        self.process_table_view.setModel(self.process_model)

        # ✅ Enable sorting
        self.process_table_view.setSortingEnabled(True)

        layout.addWidget(self.process_table_view)
    
    # -----------------------------------------------
    def on_row_selected(self):
        """Handle row selection event."""
        selection_model = self.table_view.selectionModel()

        if selection_model.hasSelection():
            selected_rows = selection_model.selectedRows()
            if selected_rows:
                print(f"✅ {len(selected_rows)} row(s) selected.")
            else:
                print("No row selected.")
        else:
            print("No selection.")

    # -----------------------------------------------
    def get_total_rows(self):
        """Get the total number of rows."""
        query = QSqlQuery("SELECT COUNT(*) FROM mapping", self.db)
        if query.next():
            return query.value(0)
        return 0

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

    # -----------------------------------------------
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

    # __________________________________________________
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
