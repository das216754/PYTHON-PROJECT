import sys
from pathlib import Path

# Fix the Python import path
SRC_DIR = Path(__file__).resolve().parents[2]

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QFrame,
    QLineEdit,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

from facultysync.models import DAYS, format_time
from facultysync.repository import load_schedule
from facultysync.scheduler import FacultyScheduler


STYLESHEET = """
QMainWindow {
    background: #0b1120;
}
QWidget {
    color: #e2e8f0;
    font-family: Segoe UI;
    font-size: 13px;
}
QFrame#Sidebar {
    background: #111a2e;
    border-right: 1px solid #26334d;
}
QLabel#Brand {
    color: #60a5fa;
    font-size: 25px;
    font-weight: bold;
}
QLabel#PageTitle {
    color: #f8fafc;
    font-size: 27px;
    font-weight: bold;
}
QLabel#Muted {
    color: #94a3b8;
}
QFrame#Panel {
    background: #111a2e;
    border: 1px solid #26334d;
    border-radius: 12px;
}
QPushButton#NavButton {
    text-align: left;
    padding: 13px;
    background: transparent;
    border: none;
    border-radius: 8px;
    color: #cbd5e1;
}
QPushButton#NavButton:hover {
    background: #1e293b;
}
QPushButton#NavButton:checked {
    background: #1d4ed8;
    color: white;
    font-weight: bold;
}
QPushButton#Primary {
    background: #2563eb;
    border: none;
    border-radius: 8px;
    padding: 11px;
    color: white;
    font-weight: bold;
}
QPushButton#Primary:hover {
    background: #3b82f6;
}
QPushButton#Secondary {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px;
}
QLineEdit, QComboBox {
    background: #0b1120;
    border: 1px solid #334155;
    border-radius: 7px;
    padding: 9px;
}
QTableWidget {
    background: #111a2e;
    alternate-background-color: #162238;
    gridline-color: #26334d;
    border: 1px solid #26334d;
    border-radius: 8px;
    selection-background-color: #1d4ed8;
}
QHeaderView::section {
    background: #1e293b;
    color: #93c5fd;
    padding: 10px;
    border: none;
    font-weight: bold;
}
"""


class FacultySyncWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("FacultySync | Appointment Manager")
        self.resize(1200, 760)
        self.setMinimumSize(900, 600)

        self.availability = []
        self.appointments = []
        self.scheduler = FacultyScheduler([], [])
        self.data_error = None

        try:
            self.availability, self.appointments = load_schedule()
            self.scheduler = FacultyScheduler(
                self.availability,
                self.appointments,
            )
        except Exception as error:
            self.data_error = str(error)

        self.nav_buttons = []
        self.pages = QStackedWidget()

        self.build_ui()
        self.navigate(0)

    def label(self, text, object_name=None):
        widget = QLabel(text)
        if object_name:
            widget.setObjectName(object_name)
        return widget

    def panel(self):
        widget = QFrame()
        widget.setObjectName("Panel")
        return widget

    def button(self, text, primary=False):
        widget = QPushButton(text)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        widget.setObjectName("Primary" if primary else "Secondary")
        return widget

    def heading(self, layout, title, subtitle):
        layout.addWidget(self.label(title, "PageTitle"))
        layout.addWidget(self.label(subtitle, "Muted"))
        layout.addSpacing(14)

    def table(self, headers):
        widget = QTableWidget(0, len(headers))
        widget.setHorizontalHeaderLabels(headers)
        widget.setAlternatingRowColors(True)
        widget.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        widget.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        widget.verticalHeader().setVisible(False)
        widget.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        return widget

    def add_row(self, table, values):
        row = table.rowCount()
        table.insertRow(row)
        for col, value in enumerate(values):
            table.setItem(row, col, QTableWidgetItem(str(value)))

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(230)

        side = QVBoxLayout(sidebar)
        side.setContentsMargins(18, 25, 18, 20)
        side.setSpacing(10)

        side.addWidget(self.label("FacultySync", "Brand"))
        side.addWidget(self.label("SMART APPOINTMENT SYSTEM", "Muted"))
        side.addSpacing(25)
        side.addWidget(self.label("WORKSPACE", "Muted"))

        items = [
            ("▦   Dashboard", 0),
            ("⌕   Find Faculty", 1),
            ("▤   My Appointments", 2),
            ("♙   Faculty Directory", 3),
        ]

        for text, index in items:
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.clicked.connect(
                lambda checked=False, i=index: self.navigate(i)
            )
            side.addWidget(btn)
            self.nav_buttons.append(btn)

        side.addStretch()
        side.addWidget(self.label("FACULTYSYNC • DSA PROJECT", "Muted"))

        self.pages.addWidget(self.dashboard_page())
        self.pages.addWidget(self.find_page())
        self.pages.addWidget(self.appointments_page())
        self.pages.addWidget(self.directory_page())

        root.addWidget(sidebar)
        root.addWidget(self.pages, 1)

    def navigate(self, index):
        self.pages.setCurrentIndex(index)

        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

        if index == 0:
            self.refresh_dashboard()
        elif index == 2:
            self.refresh_appointments()
        elif index == 3:
            self.refresh_directory()

    def dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        self.heading(
            layout,
            "Dashboard",
            "Your faculty appointment workspace at a glance.",
        )

        cards = QHBoxLayout()
        self.faculty_value = self.stat_card(cards, "FACULTY MEMBERS")
        self.availability_value = self.stat_card(
            cards, "AVAILABILITY RECORDS"
        )
        self.appointment_value = self.stat_card(
            cards, "APPOINTMENTS"
        )
        layout.addLayout(cards)

        welcome = self.panel()
        box = QVBoxLayout(welcome)
        box.setContentsMargins(20, 20, 20, 20)
        box.addWidget(self.label("Welcome to FacultySync"))
        box.addWidget(
            self.label(
                "Find faculty availability and explore appointment records.",
                "Muted",
            )
        )

        find_btn = self.button("Find Available Slots", True)
        find_btn.clicked.connect(lambda: self.navigate(1))
        box.addWidget(find_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(welcome)

        self.status_label = self.label("", "Muted")
        layout.addWidget(self.status_label)
        layout.addStretch()
        return page

    def stat_card(self, layout, title):
        card = self.panel()
        card.setMinimumHeight(120)

        box = QVBoxLayout(card)
        box.setContentsMargins(16, 16, 16, 16)
        box.addWidget(self.label(title, "Muted"))

        value = self.label("0")
        value.setFont(QFont("Segoe UI", 25, QFont.Weight.Bold))
        value.setStyleSheet("color: #60a5fa;")
        box.addWidget(value)

        layout.addWidget(card, 1)
        return value

    def refresh_dashboard(self):
        faculty = {item.faculty for item in self.availability}
        self.faculty_value.setText(str(len(faculty)))
        self.availability_value.setText(str(len(self.availability)))
        self.appointment_value.setText(str(len(self.appointments)))

        self.status_label.setText(
            f"Data error: {self.data_error}"
            if self.data_error
            else "Schedule data loaded successfully."
        )

    def find_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        self.heading(
            layout,
            "Find Faculty",
            "Search available appointment slots.",
        )

        form_panel = self.panel()
        form = QVBoxLayout(form_panel)
        form.setContentsMargins(18, 18, 18, 18)
        form.setSpacing(10)

        form.addWidget(self.label("Day"))
        self.day_combo = QComboBox()
        self.day_combo.addItems([str(day) for day in DAYS])
        form.addWidget(self.day_combo)

        form.addWidget(self.label("Start time (HH:MM)"))
        self.start_input = QLineEdit()
        self.start_input.setPlaceholderText("e.g. 09:00")
        form.addWidget(self.start_input)

        form.addWidget(self.label("End time (HH:MM)"))
        self.end_input = QLineEdit()
        self.end_input.setPlaceholderText("e.g. 12:00")
        form.addWidget(self.end_input)

        form.addWidget(self.label("Slot duration"))
        self.duration_combo = QComboBox()
        self.duration_combo.addItems(["15", "30", "45", "60"])
        self.duration_combo.setCurrentText("30")
        form.addWidget(self.duration_combo)

        search_btn = self.button("Search Availability", True)
        search_btn.clicked.connect(self.search_slots)
        form.addWidget(search_btn)
        layout.addWidget(form_panel)

        results_panel = self.panel()
        results = QVBoxLayout(results_panel)
        results.addWidget(self.label("Available Slots"))
        self.slots_table = self.table(
            ["Faculty", "Day", "Start", "End"]
        )
        results.addWidget(self.slots_table)
        layout.addWidget(results_panel, 1)
        return page

    @staticmethod
    def parse_time(value):
        parts = value.strip().split(":")
        if len(parts) != 2:
            raise ValueError("Enter time in HH:MM format.")

        hours, minutes = int(parts[0]), int(parts[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError("Enter a valid 24-hour time.")

        return hours * 60 + minutes

    def search_slots(self):
        if self.data_error:
            QMessageBox.warning(
                self, "Data unavailable", self.data_error
            )
            return

        try:
            day = self.day_combo.currentText()
            start = self.parse_time(self.start_input.text())
            end = self.parse_time(self.end_input.text())
            duration = int(self.duration_combo.currentText())

            if end <= start:
                raise ValueError("End time must be later than start time.")

            slots = self.scheduler.find_slots(
                day, start, end, duration
            )

            self.slots_table.setRowCount(0)
            for slot in slots:
                self.add_row(
                    self.slots_table,
                    [
                        slot["faculty"],
                        slot["day"],
                        format_time(slot["start"]),
                        format_time(slot["end"]),
                    ],
                )

            if not slots:
                QMessageBox.information(
                    self, "No slots", "No matching slots were found."
                )

        except (ValueError, TypeError) as error:
            QMessageBox.warning(self, "Invalid search", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Search failed", str(error))

    def appointments_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        self.heading(
            layout,
            "My Appointments",
            "Appointment records loaded from your schedule file.",
        )

        panel = self.panel()
        box = QVBoxLayout(panel)
        self.appointments_table = self.table(
            ["Faculty", "Day", "Start", "End"]
        )
        box.addWidget(self.appointments_table)
        layout.addWidget(panel, 1)

        refresh = self.button("Refresh")
        refresh.clicked.connect(self.refresh_appointments)
        layout.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignRight)
        return page

    def refresh_appointments(self):
        self.appointments_table.setRowCount(0)
        for item in self.appointments:
            self.add_row(
                self.appointments_table,
                [
                    item.faculty,
                    item.day,
                    format_time(item.start),
                    format_time(item.end),
                ],
            )

    def directory_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 28, 28, 28)
        self.heading(
            layout,
            "Faculty Directory",
            "Browse faculty from the loaded availability records.",
        )

        self.directory_search = QLineEdit()
        self.directory_search.setPlaceholderText("Search faculty...")
        self.directory_search.textChanged.connect(self.filter_directory)
        layout.addWidget(self.directory_search)

        panel = self.panel()
        box = QVBoxLayout(panel)
        self.directory_table = self.table(
            ["Faculty Name", "Availability Records"]
        )
        box.addWidget(self.directory_table)
        layout.addWidget(panel, 1)
        return page

    def refresh_directory(self):
        self.directory_table.setRowCount(0)
        counts = {}

        for item in self.availability:
            counts[item.faculty] = counts.get(item.faculty, 0) + 1

        for name in sorted(counts):
            self.add_row(
                self.directory_table,
                [name, counts[name]],
            )

        self.filter_directory(self.directory_search.text())

    def filter_directory(self, text):
        query = text.strip().lower()
        for row in range(self.directory_table.rowCount()):
            item = self.directory_table.item(row, 0)
            self.directory_table.setRowHidden(
                row, query not in item.text().lower()
            )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    window = FacultySyncWindow()
    window.show()

    if window.data_error:
        QMessageBox.warning(
            window,
            "Schedule data unavailable",
            "FacultySync could not load the schedule:\n\n"
            + window.data_error,
        )

    sys.exit(app.exec())


if __name__ == "__main__":
    main()