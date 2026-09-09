from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class HomePage(QWidget):
    calendar_requested = Signal()
    history_requested = Signal()
    settings_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("校正文件管理工具"))
        for title, signal in (
            ("月曆", self.calendar_requested),
            ("歷史案件", self.history_requested),
            ("設定", self.settings_requested),
        ):
            button = QPushButton(title)
            button.clicked.connect(signal.emit)
            layout.addWidget(button)
        layout.addStretch()
