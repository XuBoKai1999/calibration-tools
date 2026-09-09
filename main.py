import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent / "src"))

from calibration_manager.gui.main_window import MainWindow
from calibration_manager.settings import APPLICATION_NAME, ORGANIZATION_NAME


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    window = MainWindow(QSettings(), Path(__file__).parent / "data")
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
