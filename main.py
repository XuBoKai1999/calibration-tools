import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).parent / "src"))

from calibration_manager.gui.main_window import MainWindow
from calibration_manager.cases.storage import migrate_cases_root
from calibration_manager.settings import APPLICATION_NAME, ORGANIZATION_NAME, legacy_app_data_root


def main() -> int:
    app = QApplication(sys.argv)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationName(APPLICATION_NAME)
    root = Path(__file__).parent
    data_root = root / "data"
    migrate_cases_root(legacy_app_data_root() / "cases", data_root / "cases")
    window = MainWindow(QSettings(), data_root, root / "config" / "systems")
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
