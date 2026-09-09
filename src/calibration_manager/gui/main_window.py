from PySide6.QtCore import QEvent, QSettings, Qt
from PySide6.QtGui import QCloseEvent, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QInputDialog, QLabel, QMainWindow, QPushButton, QStackedWidget, QWidget

from calibration_manager.gui.pages.calendar_page import CalendarPage
from calibration_manager.gui.pages.history_page import HistoryPage
from calibration_manager.gui.pages.home_page import HomePage
from calibration_manager.settings import (
    GUI_SCALE_KEY,
    MAXIMUM_SCALE,
    MINIMUM_SCALE,
    SCALE_STEP,
    WINDOW_GEOMETRY_KEY,
)


class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        self.settings = settings or QSettings()
        self.base_font_size = QApplication.font().pointSizeF()
        self.scale = 100
        self.setWindowTitle("校正文件管理工具")
        self.setMinimumSize(640, 480)

        self.home_page = HomePage()
        self.calendar_page = CalendarPage()
        self.history_page = HistoryPage()
        self.pages = QStackedWidget()
        for page in (self.home_page, self.calendar_page, self.history_page):
            self.pages.addWidget(page)
        self.setCentralWidget(self.pages)

        self.home_page.calendar_requested.connect(lambda: self.show_page(self.calendar_page))
        self.home_page.history_requested.connect(lambda: self.show_page(self.history_page))
        self.home_page.settings_requested.connect(self.choose_scale)
        self.calendar_page.home_requested.connect(lambda: self.show_page(self.home_page))
        self.history_page.home_requested.connect(lambda: self.show_page(self.home_page))

        self.build_zoom_controls()
        for widget in (self, *self.findChildren(QWidget)):
            widget.installEventFilter(self)

        self.resize(720, 480)
        geometry = self.settings.value(WINDOW_GEOMETRY_KEY)
        if geometry:
            self.restoreGeometry(geometry)
        self.set_scale(int(self.settings.value(GUI_SCALE_KEY, 100)))

    def show_page(self, page: QWidget) -> None:
        self.pages.setCurrentWidget(page)

    def build_zoom_controls(self) -> None:
        zoom_out = QPushButton("−")
        zoom_out.setToolTip("縮小（Ctrl+-）")
        zoom_out.clicked.connect(lambda: self.set_scale(self.scale - SCALE_STEP))
        self.zoom_label = QLabel()
        self.zoom_label.setMinimumWidth(48)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_in = QPushButton("+")
        zoom_in.setToolTip("放大（Ctrl++）")
        zoom_in.clicked.connect(lambda: self.set_scale(self.scale + SCALE_STEP))
        reset = QPushButton("重設")
        reset.setToolTip("重設為 100%（Ctrl+0）")
        reset.clicked.connect(lambda: self.set_scale(100))
        for widget in (zoom_out, self.zoom_label, zoom_in, reset):
            self.statusBar().addPermanentWidget(widget)

        for keys in ("Ctrl++", "Ctrl+="):
            QShortcut(QKeySequence(keys), self, activated=lambda: self.set_scale(self.scale + SCALE_STEP))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self.set_scale(self.scale - SCALE_STEP))
        QShortcut(QKeySequence("Ctrl+0"), self, activated=lambda: self.set_scale(100))

    def choose_scale(self) -> None:
        scale, accepted = QInputDialog.getInt(
            self,
            "介面縮放",
            "GUI scale (%)",
            self.scale,
            MINIMUM_SCALE,
            MAXIMUM_SCALE,
            SCALE_STEP,
        )
        if accepted:
            self.set_scale(scale)

    def set_scale(self, percent: int) -> None:
        percent = min(MAXIMUM_SCALE, max(MINIMUM_SCALE, round(percent / SCALE_STEP) * SCALE_STEP))
        font = QFont(QApplication.font())
        font.setPointSizeF(self.base_font_size * percent / 100)
        self.setFont(font)
        self.scale = percent
        self.zoom_label.setText(f"{percent}%")
        self.settings.setValue(GUI_SCALE_KEY, percent)

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Wheel and event.modifiers() & Qt.ControlModifier:
            direction = SCALE_STEP if event.angleDelta().y() > 0 else -SCALE_STEP
            self.set_scale(self.scale + direction)
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.settings.setValue(WINDOW_GEOMETRY_KEY, self.saveGeometry())
        super().closeEvent(event)
