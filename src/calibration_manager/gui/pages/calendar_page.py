from PySide6.QtCore import QDate, Signal, Qt
from PySide6.QtWidgets import (
    QCalendarWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from calibration_manager.cases.model import Case


class CalendarPage(QWidget):
    home_requested = Signal()
    new_case_requested = Signal(QDate)
    photo_requested = Signal(QDate)
    open_case_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.cases_by_date: dict[str, list[Case]] = {}

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
        self.day_cases.itemDoubleClicked.connect(
            lambda item: self.open_case_requested.emit(item.data(Qt.UserRole))
            if item.data(Qt.UserRole) else None
        )
        layout.addWidget(self.day_cases)
        new_case = QPushButton("建立新案件")
        new_case.clicked.connect(lambda: self.new_case_requested.emit(self.calendar.selectedDate()))
        layout.addWidget(new_case)
        photo = QPushButton("從照片建立案件")
        photo.clicked.connect(lambda: self.photo_requested.emit(self.calendar.selectedDate()))
        layout.addWidget(photo)
        self.update_selected_date()

    def set_cases(self, cases: list[Case]) -> None:
        self.cases_by_date.clear()
        for case in cases:
            date = case.schedule.get("reserved_date", "")
            self.cases_by_date.setdefault(date, []).append(case)
        self.update_selected_date()

    def update_selected_date(self) -> None:
        date = self.calendar.selectedDate().toString(Qt.ISODate)
        self.selected_date_label.setText(f"{date} 的案件")
        self.day_cases.clear()
        cases = self.cases_by_date.get(date, [])
        if not cases:
            self.day_cases.addItem("尚無案件")
            return
        for case in cases:
            item = QListWidgetItem(
                f"{case.system}　{case.customer.get('name', '')}　{case.status}"
            )
            item.setData(Qt.UserRole, case.case_id)
            self.day_cases.addItem(item)
