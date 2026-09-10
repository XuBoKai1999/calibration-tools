from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QRadioButton,
    QVBoxLayout,
)


class NewCaseDialog(QDialog):
    def __init__(self, systems: list[dict], initial_method: str = "manual", parent=None):
        super().__init__(parent)
        self.setWindowTitle("建立新案件")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.system = QComboBox()
        for item in systems:
            self.system.addItem(f"{item['code']}－{item['name']}", item["code"])
        form.addRow("校正系統", self.system)
        layout.addLayout(form)

        self.manual = QRadioButton("手動輸入")
        self.ocr = QRadioButton("OCR 預約單")
        (self.ocr if initial_method == "ocr" else self.manual).setChecked(True)
        layout.addWidget(self.manual)
        layout.addWidget(self.ocr)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selection(self) -> tuple[str, str]:
        return self.system.currentData(), "ocr" if self.ocr.isChecked() else "manual"
