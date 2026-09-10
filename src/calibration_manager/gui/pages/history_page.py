from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from calibration_manager.cases.model import Case


class HistoryPage(QWidget):
    home_requested = Signal()
    open_case_requested = Signal(str)

    def __init__(self, systems: list[dict]):
        super().__init__()
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("返回首頁")
        back.clicked.connect(self.home_requested.emit)
        header.addWidget(back)
        header.addWidget(QLabel("歷史案件"))
        header.addStretch()
        layout.addLayout(header)

        self.search = QLineEdit()
        self.search.setPlaceholderText("搜尋 Case ID、報告編號、客戶、型號、序號、日期或狀態")
        layout.addWidget(self.search)
        self.systems = QTabWidget()
        self.lists: dict[str, QListWidget] = {}
        for system in systems:
            cases = QListWidget()
            cases.itemDoubleClicked.connect(
                lambda item: self.open_case_requested.emit(item.data(Qt.UserRole))
            )
            self.lists[system["code"]] = cases
            self.systems.addTab(cases, system["code"])
        layout.addWidget(self.systems)
        self.search.textChanged.connect(self._apply_filter)

    def set_cases(self, cases: list[Case]) -> None:
        for case_list in self.lists.values():
            case_list.clear()
        for case in cases:
            if case.system not in self.lists:
                continue
            text = "　".join((
                case.case_id,
                case.customer.get("name", ""),
                case.instrument.get("name", ""),
                case.status,
            ))
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, case.case_id)
            self.lists[case.system].addItem(item)
        self._apply_filter()

    def select_system(self, system: str) -> None:
        index = next(
            (i for i in range(self.systems.count()) if self.systems.tabText(i) == system), -1
        )
        if index >= 0:
            self.systems.setCurrentIndex(index)

    def _apply_filter(self) -> None:
        query = self.search.text().strip().casefold()
        for case_list in self.lists.values():
            for index in range(case_list.count()):
                item = case_list.item(index)
                item.setHidden(query not in item.text().casefold())
