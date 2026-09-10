from PySide6.QtCore import QDate, Signal, Qt
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
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from calibration_manager.cases.model import Case


class CasePage(QWidget):
    home_requested = Signal()
    history_requested = Signal()
    save_requested = Signal(object)
    delete_requested = Signal(str)

    def __init__(self, systems: list[dict]):
        super().__init__()
        self._case: Case | None = None
        self.is_new = False
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        back = QPushButton("返回首頁")
        back.clicked.connect(self.home_requested.emit)
        header.addWidget(back)
        history = QPushButton("返回歷史案件")
        history.clicked.connect(self.history_requested.emit)
        header.addWidget(history)
        header.addWidget(QLabel("Case Workspace"))
        header.addStretch()
        layout.addLayout(header)
        self.identity = QLabel()
        layout.addWidget(self.identity)

        self.workspace_tabs = QTabWidget()
        basic_page = QWidget()
        basic_layout = QVBoxLayout(basic_page)

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        self.case_id = QLineEdit()
        self.case_id.setReadOnly(True)
        self.system = QComboBox()
        for item in systems:
            self.system.addItem(f"{item['code']}－{item['name']}", item["code"])
        self.status = QComboBox()
        self.status.addItems(["reserved", "received", "in_progress", "completed"])
        self.reserved_date = QDateEdit(calendarPopup=True)
        self.reserved_date.setDisplayFormat("yyyy-MM-dd")
        self.customer = QLineEdit()
        self.tax_id = QLineEdit()
        self.contact = QLineEdit()
        self.phone = QLineEdit()
        self.fax = QLineEdit()
        self.postal_code = QLineEdit()
        self.email = QLineEdit()
        self.address = QLineEdit()
        self.instrument_name = QLineEdit()
        self.brand = QLineEdit()
        self.model = QLineEdit()
        self.serial_number = QLineEdit()
        self.previous_report = QLineEdit()
        self.current_report = QLineEdit()
        self.calibration_points = QPlainTextEdit()
        self.calibration_points.setPlaceholderText("每行一個校正點")
        self.calibration_notes = QPlainTextEdit()
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
            ("傳真", self.fax),
            ("郵遞區號", self.postal_code),
            ("E-mail", self.email),
            ("地址", self.address),
            ("預約件名稱", self.instrument_name),
            ("廠牌", self.brand),
            ("型號", self.model),
            ("Serial number", self.serial_number),
            ("前次報告編號", self.previous_report),
            ("本次報告編號", self.current_report),
            ("校正點", self.calibration_points),
            ("校正需求說明", self.calibration_notes),
            ("報告附註", self.report_notes),
        ):
            form.addRow(label, widget)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_widget)
        basic_layout.addWidget(scroll)

        self.save_button = QPushButton("儲存案件")
        self.save_button.clicked.connect(lambda: self.save_requested.emit(self.case_data()))
        basic_layout.addWidget(self.save_button)
        self.message = QLabel()
        basic_layout.addWidget(self.message)
        self.workspace_tabs.addTab(basic_page, "基本資料")
        for title, message in (
            ("歷史資料", "歷史／參考資料將於 Step 2 實作"),
            ("本次量測", "本次量測功能尚未實作"),
            ("不確定度", "不確定度計算尚未實作"),
            ("產生報告", "報告產生功能尚未實作"),
        ):
            placeholder = QLabel(message)
            placeholder.setAlignment(Qt.AlignCenter)
            self.workspace_tabs.addTab(placeholder, title)
        layout.addWidget(self.workspace_tabs)

        self.delete_button = QPushButton("刪除案件")
        self.delete_button.clicked.connect(lambda: self.delete_requested.emit(self.case_id.text()))
        layout.addWidget(self.delete_button)

    def set_case(self, case: Case, is_new: bool = False) -> None:
        self._case = case
        self.is_new = False
        self.case_id.setText(case.case_id)
        self.system.setCurrentIndex(self.system.findData(case.system))
        self.status.setCurrentText(case.status)
        self.reserved_date.setDate(QDate.fromString(case.schedule.get("reserved_date", ""), "yyyy-MM-dd"))
        self.customer.setText(case.customer.get("name", ""))
        self.tax_id.setText(case.customer.get("tax_id", ""))
        self.contact.setText(case.customer.get("contact", ""))
        self.phone.setText(case.customer.get("phone", ""))
        self.fax.setText(case.customer.get("fax", ""))
        self.postal_code.setText(case.customer.get("postal_code", ""))
        self.email.setText(case.customer.get("email", ""))
        self.address.setText(case.customer.get("address", ""))
        self.instrument_name.setText(case.instrument.get("name", ""))
        self.brand.setText(case.instrument.get("brand", ""))
        self.model.setText(case.instrument.get("model", ""))
        self.serial_number.setText(case.instrument.get("serial_number", ""))
        self.previous_report.setText(case.report.get("previous_report_number", ""))
        self.current_report.setText(case.report.get("current_report_number", ""))
        self.calibration_points.setPlainText("\n".join(case.calibration_request.get("points", [])))
        self.calibration_notes.setPlainText(case.calibration_request.get("notes", ""))
        self.report_notes.setPlainText("\n".join(case.report.get("notes", [])))
        self.is_new = is_new
        self.system.setEnabled(False)
        self.save_button.setText("建立案件" if is_new else "儲存案件")
        self.delete_button.setEnabled(not is_new)
        self.identity.setText(
            f"{case.case_id}　|　{case.system}　|　"
            f"{case.instrument.get('name', '') or '未填 DUT'}　|　{case.status}"
        )
        self.workspace_tabs.setCurrentIndex(0)
        self.message.clear()

    def apply_ocr_fields(self, fields: dict) -> None:
        widgets = {
            "customer_name": self.customer,
            "tax_id": self.tax_id,
            "contact": self.contact,
            "phone": self.phone,
            "fax": self.fax,
            "postal_code": self.postal_code,
            "email": self.email,
            "address": self.address,
            "instrument_name": self.instrument_name,
            "brand": self.brand,
            "model": self.model,
            "serial_number": self.serial_number,
        }
        for name, widget in widgets.items():
            if fields.get(name):
                widget.setText(fields[name])
        if fields.get("calibration_notes"):
            self.calibration_notes.setPlainText(fields["calibration_notes"])
        if fields.get("previous_report_number"):
            self.previous_report.setText(fields["previous_report_number"])
        self.message.setText("影像辨識完成；請逐欄確認後再儲存案件")

    def case_data(self) -> Case:
        if self._case is None:
            raise ValueError("尚未載入案件")
        case = self._case
        case.case_id = self.case_id.text()
        case.system = self.system.currentData()
        case.status = self.status.currentText()
        case.customer.update({
            "name": self.customer.text().strip(),
            "tax_id": self.tax_id.text().strip(),
            "contact": self.contact.text().strip(),
            "phone": self.phone.text().strip(),
            "fax": self.fax.text().strip(),
            "postal_code": self.postal_code.text().strip(),
            "email": self.email.text().strip(),
            "address": self.address.text().strip(),
        })
        case.instrument.update({
            "name": self.instrument_name.text().strip(),
            "brand": self.brand.text().strip(),
            "model": self.model.text().strip(),
            "serial_number": self.serial_number.text().strip(),
        })
        case.schedule["reserved_date"] = self.reserved_date.date().toString("yyyy-MM-dd")
        case.report.update({
            "previous_report_number": self.previous_report.text().strip(),
            "current_report_number": self.current_report.text().strip(),
            "notes": [line for line in self.report_notes.toPlainText().splitlines() if line],
        })
        case.calibration_request.update({
            "points": [line for line in self.calibration_points.toPlainText().splitlines() if line],
            "notes": self.calibration_notes.toPlainText().strip(),
        })
        return case
