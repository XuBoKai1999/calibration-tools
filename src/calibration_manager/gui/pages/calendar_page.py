from PySide6.QtCore import QDate, Signal, Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CalendarPage(QWidget):
    home_requested = Signal()
    new_case_requested = Signal(QDate)

    def __init__(self):
        super().__init__()
        self.cases_by_date = {
            QDate.currentDate().toString(Qt.ISODate): ["E05　範例客戶　預約"]
        }

        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("返回首頁")
        back.clicked.connect(self.home_requested.emit)
        header.addWidget(back)
        header.addWidget(QLabel("月曆"))
        header.addStretch()
        layout.addLayout(header)

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.update_selected_date)
        layout.addWidget(self.calendar)
        self.selected_date_label = QLabel()
        layout.addWidget(self.selected_date_label)
        self.day_cases = QListWidget()
        layout.addWidget(self.day_cases)
        new_case = QPushButton("建立新案件")
        new_case.clicked.connect(lambda: self.new_case_requested.emit(self.calendar.selectedDate()))
        layout.addWidget(new_case)
        self.update_selected_date()

    def update_selected_date(self) -> None:
        date = self.calendar.selectedDate().toString(Qt.ISODate)
        self.selected_date_label.setText(f"{date} 的案件")
        self.day_cases.clear()
        self.day_cases.addItems(self.cases_by_date.get(date, ["尚無案件"]))
