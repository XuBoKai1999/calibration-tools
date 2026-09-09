from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from calibration_manager.cases.model import Case


class CasePage(QWidget):
    home_requested = Signal()
    save_requested = Signal(object)
    system_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.is_new = False
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("返回首頁")
        back.clicked.connect(self.home_requested.emit)
        header.addWidget(back)
        header.addWidget(QLabel("案件基本資料"))
        header.addStretch()
        layout.addLayout(header)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.case_id = QLineEdit()
        self.case_id.setReadOnly(True)
        self.system = QComboBox()
        self.system.addItems(["E05", "E07", "E27"])
        self.system.currentTextChanged.connect(self.system_changed.emit)
        self.status = QComboBox()
        self.status.addItems(["reserved", "received", "in_progress", "completed"])
        self.reserved_date = QDateEdit(calendarPopup=True)
        self.reserved_date.setDisplayFormat("yyyy-MM-dd")
        self.customer = QLineEdit()
        self.tax_id = QLineEdit()
        self.contact = QLineEdit()
        self.phone = QLineEdit()
        self.address = QLineEdit()
        self.instrument_name = QLineEdit()
        self.brand = QLineEdit()
        self.model = QLineEdit()
        self.serial_number = QLineEdit()
        self.previous_report = QLineEdit()
        self.current_report = QLineEdit()
        self.calibration_points = QPlainTextEdit()
        self.calibration_points.setPlaceholderText("每行一個校正點")
        self.report_notes = QPlainTextEdit()

        for label, widget in (
            ("Case ID", self.case_id),
            ("系統", self.system),
            ("狀態", self.status),
            ("預約日期", self.reserved_date),
            ("客戶", self.customer),
            ("統一編號", self.tax_id),
            ("聯絡人", self.contact),
            ("聯絡電話", self.phone),
            ("地址", self.address),
            ("預約件名稱", self.instrument_name),
            ("廠牌", self.brand),
            ("型號", self.model),
            ("Serial number", self.serial_number),
            ("前次報告編號", self.previous_report),
            ("本次報告編號", self.current_report),
            ("校正點", self.calibration_points),
            ("報告附註", self.report_notes),
        ):
            form.addRow(label, widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)

        save = QPushButton("儲存案件")
        save.clicked.connect(lambda: self.save_requested.emit(self.case_data()))
        layout.addWidget(save)
        self.message = QLabel()
        layout.addWidget(self.message)

    def set_case(self, case: Case, is_new: bool = False) -> None:
        self.is_new = False
        self.case_id.setText(case.case_id)
        self.system.setCurrentText(case.system)
        self.status.setCurrentText(case.status)
        self.reserved_date.setDate(QDate.fromString(case.schedule.get("reserved_date", ""), "yyyy-MM-dd"))
        self.customer.setText(case.customer.get("name", ""))
        self.tax_id.setText(case.customer.get("tax_id", ""))
        self.contact.setText(case.customer.get("contact", ""))
        self.phone.setText(case.customer.get("phone", ""))
        self.address.setText(case.customer.get("address", ""))
        self.instrument_name.setText(case.instrument.get("name", ""))
        self.brand.setText(case.instrument.get("brand", ""))
        self.model.setText(case.instrument.get("model", ""))
        self.serial_number.setText(case.instrument.get("serial_number", ""))
        self.previous_report.setText(case.report.get("previous_report_number", ""))
        self.current_report.setText(case.report.get("current_report_number", ""))
        self.calibration_points.setPlainText("\n".join(case.calibration_request.get("points", [])))
        self.report_notes.setPlainText("\n".join(case.report.get("notes", [])))
        self.is_new = is_new
        self.system.setEnabled(is_new)
        self.message.clear()

    def apply_ocr_fields(self, fields: dict) -> None:
        widgets = {
            "customer_name": self.customer,
            "tax_id": self.tax_id,
            "contact": self.contact,
            "phone": self.phone,
            "address": self.address,
            "instrument_name": self.instrument_name,
            "brand": self.brand,
            "model": self.model,
            "serial_number": self.serial_number,
        }
        for name, widget in widgets.items():
            if fields.get(name):
                widget.setText(fields[name])
        if fields.get("system"):
            self.system.setCurrentText(fields["system"])
        if fields.get("calibration_notes"):
            self.calibration_points.setPlainText(fields["calibration_notes"])
        self.message.setText("影像辨識完成；請逐欄確認後再儲存案件")

    def case_data(self) -> Case:
        return Case(
            case_id=self.case_id.text(),
            system=self.system.currentText(),
            status=self.status.currentText(),
            customer={
                "name": self.customer.text().strip(),
                "tax_id": self.tax_id.text().strip(),
                "contact": self.contact.text().strip(),
                "phone": self.phone.text().strip(),
                "address": self.address.text().strip(),
            },
            instrument={
                "name": self.instrument_name.text().strip(),
                "brand": self.brand.text().strip(),
                "model": self.model.text().strip(),
                "serial_number": self.serial_number.text().strip(),
            },
            schedule={
                "reserved_date": self.reserved_date.date().toString("yyyy-MM-dd"),
                "received_date": None,
                "completed_date": None,
            },
            report={
                "previous_report_number": self.previous_report.text().strip(),
                "current_report_number": self.current_report.text().strip(),
                "notes": [line for line in self.report_notes.toPlainText().splitlines() if line],
            },
            calibration_request={
                "mode": "specified_points",
                "reference_report": None,
                "points": [line for line in self.calibration_points.toPlainText().splitlines() if line],
            },
        )
