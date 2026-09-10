import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from PySide6.QtCore import QDate, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QShortcut, QWheelEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton, QTabWidget

from calibration_manager.gui.main_window import MainWindow


class MainWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_required_home_entries_are_present(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings, Path(directory) / "data")
        labels = {button.text() for button in window.findChildren(QPushButton)}
        self.assertTrue({"月曆", "歷史案件", "設定"}.issubset(labels))

    def test_calendar_and_history_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings, Path(directory) / "data")
            home_buttons = window.home_page.findChildren(QPushButton)
            next(button for button in home_buttons if button.text() == "月曆").click()
            self.assertIs(window.pages.currentWidget(), window.calendar_page)
            self.assertIn("的案件", window.calendar_page.selected_date_label.text())

            window.show_page(window.home_page)
            next(button for button in home_buttons if button.text() == "歷史案件").click()
            self.assertIs(window.pages.currentWidget(), window.history_page)
            tabs = window.history_page.findChild(QTabWidget)
            self.assertEqual([tabs.tabText(i) for i in range(tabs.count())], ["E05", "E07", "E27"])
            self.assertIsNotNone(window.history_page.findChild(QLineEdit))

    def test_scale_and_window_geometry_are_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/settings.ini"
            settings = QSettings(path, QSettings.IniFormat)
            window = MainWindow(settings, Path(directory) / "data")
            window.set_scale(120)
            window.close()
            settings.sync()

            saved = QSettings(path, QSettings.IniFormat)
            self.assertEqual(saved.value("gui/scale", type=int), 120)
            self.assertIsNotNone(saved.value("window/geometry"))

            restored = MainWindow(saved, Path(directory) / "data")
            self.assertEqual(restored.scale, 120)
            self.assertEqual(restored.zoom_label.text(), "120%")

    def test_scale_is_kept_in_supported_range(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings, Path(directory) / "data")
            window.set_scale(10)
            self.assertEqual(window.scale, 80)
            window.set_scale(200)
            self.assertEqual(window.scale, 200)
            window.set_scale(9999)
            self.assertEqual(window.scale, 1000)

    def test_control_mouse_wheel_changes_scale_over_child_widgets(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings, Path(directory) / "data")
            event = QWheelEvent(
                QPointF(), QPointF(), QPoint(), QPoint(0, 120), Qt.NoButton,
                Qt.ControlModifier, Qt.NoScrollPhase, False,
            )
            QApplication.sendEvent(window.calendar_page.calendar, event)
            self.assertEqual(window.scale, 110)

    def test_keyboard_zoom_shortcuts_are_registered(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings, Path(directory) / "data")
            keys = {shortcut.key().toString() for shortcut in window.findChildren(QShortcut)}
            self.assertTrue({"Ctrl++", "Ctrl+=", "Ctrl+-", "Ctrl+0"}.issubset(keys))

    def test_case_can_be_created_saved_and_reopened(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "data"
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings, root)
            window.start_new_case(QDate(2026, 9, 9))
            self.assertIs(window.pages.currentWidget(), window.case_page)
            window.case_page.customer.setText("測試客戶")
            window.case_page.model.setText("MODEL-1")
            window.case_page.apply_ocr_fields({
                "system": "E27",
                "previous_report_number": "E240540A",
            })
            case = window.case_page.case_data()
            self.assertEqual(case.system, "E27")
            self.assertIn("-E27-", case.case_id)
            window.save_current_case(case)
            self.assertIn("前次報告", window.case_page.message.text())

            reopened = MainWindow(settings, root)
            reopened.open_case(case.case_id)
            self.assertEqual(reopened.case_page.customer.text(), "測試客戶")
            self.assertEqual(reopened.case_page.model.text(), "MODEL-1")
            self.assertEqual(reopened.case_page.previous_report.text(), "E240540A")
            self.assertFalse(reopened.case_page.system.isEnabled())


if __name__ == "__main__":
    unittest.main()
