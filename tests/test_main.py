import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
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
            window = MainWindow(settings)
        labels = {button.text() for button in window.findChildren(QPushButton)}
        self.assertTrue({"月曆", "歷史案件", "設定"}.issubset(labels))

    def test_calendar_and_history_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings)
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
            window = MainWindow(settings)
            window.set_scale(120)
            window.close()
            settings.sync()

            saved = QSettings(path, QSettings.IniFormat)
            self.assertEqual(saved.value("gui/scale", type=int), 120)
            self.assertIsNotNone(saved.value("window/geometry"))

            restored = MainWindow(saved)
            self.assertEqual(restored.scale, 120)
            self.assertEqual(restored.zoom_label.text(), "120%")

    def test_scale_is_kept_in_supported_range(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings)
            window.set_scale(10)
            self.assertEqual(window.scale, 80)
            window.set_scale(200)
            self.assertEqual(window.scale, 200)
            window.set_scale(9999)
            self.assertEqual(window.scale, 1000)

    def test_control_mouse_wheel_changes_scale_over_child_widgets(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings)
            event = QWheelEvent(
                QPointF(), QPointF(), QPoint(), QPoint(0, 120), Qt.NoButton,
                Qt.ControlModifier, Qt.NoScrollPhase, False,
            )
            QApplication.sendEvent(window.calendar_page.calendar, event)
            self.assertEqual(window.scale, 110)

    def test_keyboard_zoom_shortcuts_are_registered(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings)
            keys = {shortcut.key().toString() for shortcut in window.findChildren(QShortcut)}
            self.assertTrue({"Ctrl++", "Ctrl+=", "Ctrl+-", "Ctrl+0"}.issubset(keys))


if __name__ == "__main__":
    unittest.main()
