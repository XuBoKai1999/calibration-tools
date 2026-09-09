import sys

from PySide6.QtCore import QSettings
from PySide6.QtGui import QCloseEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        self.settings = settings or QSettings()
        self.base_font_size = QApplication.font().pointSizeF()
        self.setWindowTitle("校正文件管理工具")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("校正文件管理工具"))
        for title in ("月曆", "歷史案件"):
            layout.addWidget(QPushButton(title))
        settings_button = QPushButton("設定")
        settings_button.clicked.connect(self.choose_scale)
        layout.addWidget(settings_button)
        layout.addStretch()

        page = QWidget()
        page.setLayout(layout)
        self.setCentralWidget(page)
        self.resize(720, 480)
        geometry = self.settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        self.set_scale(int(self.settings.value("gui/scale", 100)))

    def choose_scale(self) -> None:
        choices = [f"{value}%" for value in range(80, 151, 10)]
        current = f"{self.settings.value('gui/scale', 100)}%"
        choice, accepted = QInputDialog.getItem(
            self, "介面縮放", "GUI scale", choices, choices.index(current), False
        )
        if accepted:
            self.set_scale(int(choice.removesuffix("%")))

    def set_scale(self, percent: int) -> None:
        font = QFont(QApplication.font())
        font.setPointSizeF(self.base_font_size * percent / 100)
        QApplication.setFont(font)
        self.settings.setValue("gui/scale", percent)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.settings.setValue("window/geometry", self.saveGeometry())
        super().closeEvent(event)


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName("CalibrationLab")
    app.setApplicationName("CalibrationCaseManager")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
