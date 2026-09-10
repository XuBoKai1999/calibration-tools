from pathlib import Path

from PySide6.QtCore import QDate, QEvent, QSettings, Qt
from PySide6.QtGui import QCloseEvent, QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QWidget,
)

from calibration_manager.cases.model import Case
from calibration_manager.cases.service import calibration_warning, create_case, load_case_by_id, save_case
from calibration_manager.cases.storage import delete_case, load_all_cases
from calibration_manager.gui.dialogs.new_case_dialog import NewCaseDialog
from calibration_manager.gui.dialogs.system_settings_dialog import SystemSettingsDialog
from calibration_manager.gui.pages.case_page import CasePage
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
from calibration_manager.intake.reservation import discard_reservation_staging, stage_reservation_photo
from calibration_manager.systems.loader import load_systems


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: QSettings | None = None,
        data_root: Path | None = None,
        systems_root: Path | None = None,
    ):
        super().__init__()
        self.settings = settings or QSettings()
        self.data_root = data_root or Path.cwd() / "data"
        self.cases_root = self.data_root / "cases"
        self.staging_root = self.data_root / "staging"
        self.systems_root = systems_root or Path.cwd() / "config" / "systems"
        self.systems = load_systems(self.systems_root)
        if not self.systems:
            raise ValueError(f"找不到校正系統設定：{self.systems_root}")
        self.system_codes = {item["code"] for item in self.systems}
        self.base_font_size = QApplication.font().pointSizeF()
        self.scale = 100
        self.pending_reservation: Path | None = None
        self.setWindowTitle("校正文件管理工具")
        self.setMinimumSize(640, 480)

        self.home_page = HomePage()
        self.calendar_page = CalendarPage()
        self.history_page = HistoryPage(self.systems)
        self.case_page = CasePage(self.systems)
        self.pages = QStackedWidget()
        for page in (self.home_page, self.calendar_page, self.history_page, self.case_page):
            self.pages.addWidget(page)
        self.setCentralWidget(self.pages)

        self.home_page.calendar_requested.connect(lambda: self.show_page(self.calendar_page))
        self.home_page.new_case_requested.connect(
            lambda: self.open_new_case_dialog(QDate.currentDate())
        )
        self.home_page.history_requested.connect(lambda: self.show_page(self.history_page))
        self.home_page.settings_requested.connect(self.open_settings)
        self.calendar_page.home_requested.connect(lambda: self.show_page(self.home_page))
        self.calendar_page.new_case_requested.connect(self.open_new_case_dialog)
        self.calendar_page.photo_requested.connect(
            lambda date: self.open_new_case_dialog(date, "ocr")
        )
        self.calendar_page.open_case_requested.connect(self.open_case)
        self.history_page.home_requested.connect(lambda: self.show_page(self.home_page))
        self.history_page.open_case_requested.connect(self.open_case)
        self.case_page.home_requested.connect(lambda: self.show_page(self.home_page))
        self.case_page.history_requested.connect(self.show_history)
        self.case_page.save_requested.connect(self.save_current_case)
        self.case_page.delete_requested.connect(self.confirm_delete_case)
        self.refresh_cases()

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

    def refresh_cases(self) -> None:
        cases = load_all_cases(self.cases_root)
        self.calendar_page.set_cases(cases)
        self.history_page.set_cases(cases)

    def open_new_case_dialog(self, date: QDate, initial_method: str = "manual") -> None:
        dialog = NewCaseDialog(self.systems, initial_method, self)
        if dialog.exec() != QDialog.Accepted:
            return
        system, method = dialog.selection()
        if method == "ocr":
            self.choose_reservation_photo(date, system)
        else:
            self.start_new_case(date, system)

    def start_new_case(self, date: QDate, system: str | None = None) -> None:
        self.discard_pending_reservation()
        self.pending_reservation = None
        system = system or self.systems[0]["code"]
        case = create_case(
            self.cases_root, date.toString(Qt.ISODate), system, self.system_codes
        )
        self.case_page.set_case(case, is_new=True)
        self.show_page(self.case_page)

    def choose_reservation_photo(self, date: QDate, system: str) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "選擇預約單照片", "", "影像 (*.jpg *.jpeg *.png *.bmp *.tif *.tiff)"
        )
        if filename:
            self.import_reservation_photo(Path(filename), date, system)

    def import_reservation_photo(self, path: Path, date: QDate, system: str) -> None:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            staging_dir, draft = stage_reservation_photo(path, self.staging_root)
        except (OSError, ValueError, RuntimeError) as error:
            QMessageBox.critical(self, "影像辨識失敗", str(error))
            return
        finally:
            QApplication.restoreOverrideCursor()
        self.start_new_case(date, system)
        self.pending_reservation = staging_dir
        self.case_page.apply_ocr_fields(draft["fields"])

    def save_current_case(self, case: Case) -> None:
        try:
            save_case(case, self.cases_root, self.pending_reservation)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "無法儲存案件", str(error))
            return
        self.case_page.set_case(case)
        warning = calibration_warning(case)
        self.case_page.message.setText("已儲存" + (f"；{warning}" if warning else ""))
        self.pending_reservation = None
        self.refresh_cases()

    def open_case(self, case_id: str) -> None:
        self.discard_pending_reservation()
        case = load_case_by_id(self.cases_root, case_id)
        self.case_page.set_case(case)
        self.show_page(self.case_page)

    def show_history(self, system: str | None = None) -> None:
        self.refresh_cases()
        if system:
            self.history_page.select_system(system)
        self.show_page(self.history_page)

    def confirm_delete_case(self, case_id: str) -> None:
        answer = QMessageBox.question(
            self,
            "刪除案件",
            f"確定要永久刪除 {case_id}？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            delete_case(self.cases_root, case_id)
        except OSError as error:
            QMessageBox.critical(self, "無法刪除案件", str(error))
            return
        self.refresh_cases()
        self.show_history()

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

    def open_settings(self) -> None:
        dialog = SystemSettingsDialog(self.systems_root, self.systems, self.scale, self)
        dialog.scale_changed.connect(self.set_scale)
        dialog.exec()

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
        self.discard_pending_reservation()
        self.settings.setValue(WINDOW_GEOMETRY_KEY, self.saveGeometry())
        super().closeEvent(event)

    def discard_pending_reservation(self) -> None:
        if self.pending_reservation:
            discard_reservation_staging(self.pending_reservation, self.staging_root)
            self.pending_reservation = None
