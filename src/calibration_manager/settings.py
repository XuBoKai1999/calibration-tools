from pathlib import Path

from PySide6.QtCore import QStandardPaths


ORGANIZATION_NAME = "CalibrationLab"
APPLICATION_NAME = "CalibrationCaseManager"

GUI_SCALE_KEY = "gui/scale"
WINDOW_GEOMETRY_KEY = "window/geometry"
MINIMUM_SCALE = 80
MAXIMUM_SCALE = 1000
SCALE_STEP = 10


def default_data_root() -> Path:
    return Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
