import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QPushButton

from main import MainWindow


class MainWindowTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_required_home_entries_are_present(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(f"{directory}/settings.ini", QSettings.IniFormat)
            window = MainWindow(settings)
        labels = {button.text() for button in window.findChildren(QPushButton)}
        self.assertEqual(labels, {"月曆", "歷史案件", "設定"})

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


if __name__ == "__main__":
    unittest.main()
