import json
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from calibration_manager.settings import MAXIMUM_SCALE, MINIMUM_SCALE, SCALE_STEP
from calibration_manager.systems.loader import CONFIG_NAMES, load_system_config, save_system_config_text


class SystemSettingsDialog(QDialog):
    scale_changed = Signal(int)

    def __init__(self, systems_root: Path, systems: list[dict], scale: int, parent=None):
        super().__init__(parent)
        self.systems_root = systems_root
        self.setWindowTitle("設定")
        self.resize(760, 560)
        layout = QVBoxLayout(self)

        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("GUI scale"))
        self.scale = QSpinBox()
        self.scale.setRange(MINIMUM_SCALE, MAXIMUM_SCALE)
        self.scale.setSingleStep(SCALE_STEP)
        self.scale.setSuffix("%")
        self.scale.setValue(scale)
        self.scale.valueChanged.connect(self.scale_changed.emit)
        scale_row.addWidget(self.scale)
        scale_row.addStretch()
        layout.addLayout(scale_row)

        self.system = QComboBox()
        for item in systems:
            self.system.addItem(f"{item['code']}－{item['name']}", item["code"])
        self.system.currentIndexChanged.connect(self.load_current_system)
        layout.addWidget(self.system)

        self.tabs = QTabWidget()
        self.editors = {}
        labels = {"capability": "能力範圍", "pricing": "計價規則", "measurement_schema": "量測輸入規格"}
        for name in CONFIG_NAMES:
            editor = QPlainTextEdit()
            self.editors[name] = editor
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.addWidget(editor)
            self.tabs.addTab(page, labels[name])
        layout.addWidget(self.tabs)

        save = QPushButton("儲存目前系統設定")
        save.clicked.connect(self.save_current_system)
        layout.addWidget(save)
        self.load_current_system()

    def load_current_system(self) -> None:
        system = self.system.currentData()
        if not system:
            return
        try:
            for name, editor in self.editors.items():
                data = load_system_config(self.systems_root, system, name)
                editor.setPlainText(json.dumps(data, ensure_ascii=False, indent=2))
        except ValueError as error:
            QMessageBox.critical(self, "設定讀取失敗", str(error))

    def save_current_system(self) -> None:
        system = self.system.currentData()
        try:
            for name, editor in self.editors.items():
                save_system_config_text(self.systems_root, system, name, editor.toPlainText())
        except (ValueError, json.JSONDecodeError) as error:
            QMessageBox.critical(self, "設定格式錯誤", str(error))
            return
        QMessageBox.information(self, "設定", "系統設定已儲存")
