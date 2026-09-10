from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class HistoryPage(QWidget):
    home_requested = Signal()

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
        for system in systems:
            self.systems.addTab(QListWidget(), system["code"])
        layout.addWidget(self.systems)
