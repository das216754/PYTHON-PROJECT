from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
    QListWidget,
    QMessageBox,
    QHBoxLayout,
    QSpinBox,
    QGroupBox
)

from ..models import DAYS, to_minutes, format_time
from ..repository import load_schedule
from ..scheduler import FacultyScheduler


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "FacultySync - Faculty Availability Matcher"
        )
        self.resize(850, 620)

        # Load faculty schedules and existing appointments
        try:
            availability, appointments = load_schedule()
            self.scheduler = FacultyScheduler(
                availability, appointments
            )
        except (OSError, ValueError, KeyError) as error:
            QMessageBox.critical(
                self,
                "Data Loading Error",
                f"Could not load the schedule:\n{error}"
            )
            raise

        self.build_ui()

    def build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Heading
        title = QLabel("FacultySync")
        title.setStyleSheet("""
            font-size: 30px;
            font-weight: bold;
            color: #22c55e;
        """)

        subtitle = QLabel(
            "Student-Driven Faculty Availability Matching"
        )
        subtitle.setStyleSheet(
            "font-size: 14px; color: #a7f3d0;"
        )

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # Student availability form
        group = QGroupBox("Your Availability")
        form = QFormLayout(group)

        self.day = QComboBox()
        self.day.addItems(DAYS[:5])

        self.start = QLineEdit("14:00")
        self.end = QLineEdit("16:00")

        self.duration = QSpinBox()
        self.duration.setRange(15, 120)
        self.duration.setSingleStep(15)
        self.duration.setValue(30)
        self.duration.setSuffix(" minutes")

        form.addRow("Day:", self.day)
        form.addRow("Available from (HH:MM):", self.start)
        form.addRow("Available until (HH:MM):", self.end)
        form.addRow("Appointment duration:", self.duration)

        main_layout.addWidget(group)

        # Buttons
        button_layout = QHBoxLayout()

        search_button = QPushButton("Find Faculty")
        search_button.clicked.connect(self.find_faculty)

        clear_button = QPushButton("Clear Results")
        clear_button.clicked.connect(self.clear_results)

        button_layout.addWidget(search_button)
        button_layout.addWidget(clear_button)

        main_layout.addLayout(button_layout)

        # Results list
        results_label = QLabel(
            "Suitable Appointment Slots"
        )
        main_layout.addWidget(results_label)

        self.results = QListWidget()
        main_layout.addWidget(self.results)

        self.status = QLabel("Ready to search.")
        self.status.setStyleSheet("color: #4ade80;")
        main_layout.addWidget(self.status)

        self.setCentralWidget(central)

        # Dark green interface
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #101713;
                color: #e8f2eb;
                font-size: 14px;
            }

            QGroupBox {
                border: 1px solid #345442;
                border-radius: 8px;
                margin-top: 12px;
                padding: 12px;
                font-weight: bold;
            }

            QLineEdit, QComboBox, QSpinBox, QListWidget {
                background-color: #18251d;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #42624d;
                border-radius: 5px;
            }

            QPushButton {
                background-color: #22c55e;
                color: #07140b;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }

            QPushButton:hover {
                background-color: #86efac;
            }
        """)

    def find_faculty(self):
        try:
            start = to_minutes(self.start.text())
            end = to_minutes(self.end.text())

            if start >= end:
                raise ValueError(
                    "End time must be later than start time."
                )

            # Search using the augmented interval tree
            slots = self.scheduler.find_slots(
                day=self.day.currentText(),
                student_start=start,
                student_end=end,
                duration=self.duration.value()
            )

            self.results.clear()

            for slot in slots:
                faculty_name = slot["faculty"]
                day = slot["day"]
                slot_start = format_time(slot["start"])
                slot_end = format_time(slot["end"])

                self.results.addItem(
                    f"{faculty_name} | {day} | "
                    f"{slot_start} - {slot_end}"
                )

            if not slots:
                self.results.addItem(
                    "No suitable slots found. "
                    "Try another day or time."
                )

            self.status.setText(
                f"{len(slots)} matching appointment slot(s) found."
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Input",
                str(error)
            )

    def clear_results(self):
        self.results.clear()
        self.status.setText("Results cleared.")