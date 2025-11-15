"""
ویجت تولید و مدیریت صورت‌حساب‌های مهمانان
نسخه: 1.0
"""

import logging
import os
from datetime import datetime
from decimal import Decimal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QDoubleSpinBox,
                            QTextEdit, QSplitter, QTabWidget, QFrame,
                            QCheckBox, QProgressBar, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt5.QtGui import QFont, QColor, QBrush, QTextDocument, QTextCursor
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

from app.services.reception.payment_service import PaymentService
from app.services.reception.guest_service import GuestService
from app.services.reception.report_service import ReportService
from config import config

logger = logging.getLogger(__name__)

class InvoiceGenerationThread(QThread):
    """Thread برای تولید صورت‌حساب در پس‌زمینه"""

    finished = Signal(dict)
    progress = Signal(int)
    error = Signal(str)

    def __init__(self, stay_id, invoice_data):
        super().__init__()
        self.stay_id = stay_id
        self.invoice_data = invoice_data

    def run(self):
        """اجرای تولید صورت‌حساب"""
        try:
            self.progress.emit(10)

            # دریافت اطلاعات صورت‌حساب
            folio_result = PaymentService.get_guest_folio(self.stay_id)
            if not folio_result['success']:
                self.error.emit(f"خطا در دریافت صورت‌حساب: {folio_result.get('error')}")
                return

            self.progress.emit(30)

            # دریافت اطلاعات مهمان
            guest_result = GuestService.get_guest_details(self.stay_id)
            if not guest_result['success']:
                self.error.emit(f"خطا در دریافت اطلاعات مهمان: {guest_result.get('error')}")
                return

            self.progress.emit(50)

            # تولید HTML صورت‌حساب
            html_content = self.generate_invoice_html(
                folio_result['folio'],
                guest_result['guest'],
                self.invoice_data
            )

            self.progress.emit(80)

            # ذخیره فایل
            file_path = self.save_invoice_file(html_content)

            self.progress.emit(100)

            self.finished.emit({
                'success': True,
                'file_path': file_path,
                'html_content': html_content,
                'folio_data': folio_result['folio'],
                'guest_data': guest_result['guest']
            })

        except Exception as e:
            logger.error(f"خطا در تولید صورت‌حساب: {e}")
            self.error.emit(f"خطا در تولید صورت‌حساب: {str(e)}")

    def generate_invoice_html(self, folio_data, guest_data, invoice_data):
        """تولید محتوای HTML صورت‌حساب"""

        invoice_html = f"""
        <!DOCTYPE html>
        <html dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>صورت‌حساب هتل</title>
            <style>
                body {{
                    font-family: 'Tahoma', 'Arial', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .invoice-container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border: 2px solid #dee2e6;
                    border-radius: 10px;
                    box-shadow: 0 0 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 3px solid #007bff;
                    padding-bottom: 20px;
                    margin-bottom: 30px;
                }}
                .hotel-name {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 5px;
                }}
                .invoice-title {{
                    font-size: 22px;
                    color: #007bff;
                    margin: 10px 0;
                }}
                .info-section {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                    flex-wrap: wrap;
                }}
                .guest-info, .invoice-info {{
                    flex: 1;
                    min-width: 300px;
                }}
                .info-row {{
                    display: flex;
                    margin-bottom: 8px;
                }}
                .info-label {{
                    font-weight: bold;
                    width: 120px;
                    color: #495057;
                }}
                .info-value {{
                    flex: 1;
                    color: #6c757d;
                }}
                .table-container {{
                    margin: 30px 0;
                }}
                .invoice-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                }}
                .invoice-table th {{
                    background-color: #007bff;
                    color: white;
                    padding: 12px;
                    text-align: right;
                    border: 1px solid #dee2e6;
                }}
                .invoice-table td {{
                    padding: 10px;
                    border: 1px solid #dee2e6;
                    text-align: right;
                }}
                .invoice-table tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                .total-section {{
                    text-align: left;
                    margin-top: 30px;
                    padding: 20px;
                    background-color: #e9ecef;
                    border-radius: 5px;
                }}
                .total-row {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 10px;
                    font-size: 16px;
                }}
                .grand-total {{
                    font-size: 20px;
                    font-weight: bold;
                    color: #dc3545;
                    border-top: 2px solid #dc3545;
                    padding-top: 10px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #dee2e6;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .notes {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 20px 0;
                }}
                @media print {{
                    body {{
                        background: white;
                        padding: 0;
                    }}
                    .invoice-container {{
                        box-shadow: none;
                        border: none;
                        padding: 0;
                    }}
                    .no-print {{
                        display: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="invoice-container">
                <div class="header">
                    <div class="hotel-name">{config.hotel.name}</div>
                    <div class="invoice-title">صورت‌حساب اقامت</div>
                    <div style="color: #6c757d; font-size: 14px;">
                        {config.hotel.address} | تلفن: {config.hotel.phone}
                    </div>
                </div>

                <div class="info-section">
                    <div class="guest-info">
                        <div class="info-row">
                            <span class="info-label">نام مهمان:</span>
                            <span class="info-value">{guest_data.get('full_name', '--')}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">شماره اتاق:</span>
                            <span class="info-value">{guest_data.get('room_number', '--')}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">دوره اقامت:</span>
                            <span class="info-value">{guest_data.get('stay_period', '--')}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">کد رزرو:</span>
                            <span class="info-value">{folio_data.get('stay_id', '--')}</span>
                        </div>
                    </div>

                    <div class="invoice-info">
                        <div class="info-row">
                            <span class="info-label">شماره فاکتور:</span>
                            <span class="info-value">INV-{folio_data.get('folio_id', '--')}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">تاریخ صدور:</span>
                            <span class="info-value">{datetime.now().strftime("%Y/%m/%d")}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">زمان صدور:</span>
                            <span class="info-value">{datetime.now().strftime("%H:%M")}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">وضعیت:</span>
                            <span class="info-value">
                                {'تسویه شده' if folio_data.get('current_balance', 0) <= 0 else 'در انتظار پرداخت'}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="table-container">
                    <table class="invoice-table">
                        <thead>
                            <tr>
                                <th>ردیف</th>
                                <th>تاریخ</th>
                                <th>شرح</th>
                                <th>دسته‌بندی</th>
                                <th>تعداد</th>
                                <th>مبلغ واحد</th>
                                <th>مبلغ کل</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        # اضافه کردن ردیف‌های تراکنش‌ها
        transactions = folio_data.get('transactions', [])
        for i, transaction in enumerate(transactions, 1):
            transaction_type = 'هزینه' if transaction['type'] == 'charge' else 'پرداخت'
            amount_class = 'text-danger' if transaction['type'] == 'charge' else 'text-success'

            invoice_html += f"""
                            <tr>
                                <td>{i}</td>
                                <td>{transaction['created_at'].strftime("%Y/%m/%d")}</td>
                                <td>{transaction['description']}</td>
                                <td>{transaction.get('category', 'عمومی')}</td>
                                <td>1</td>
                                <td>{transaction['amount']:,.0f}</td>
                                <td style="color: {'#dc3545' if transaction['type'] == 'charge' else '#28a745'}">
                                    {transaction['amount']:,.0f}
                                </td>
                            </tr>
            """

        invoice_html += f"""
                        </tbody>
                    </table>
                </div>

                <div class="total-section">
                    <div class="total-row">
                        <span>جمع کل هزینه‌ها:</span>
                        <span>{folio_data.get('total_charges', 0):,.0f} تومان</span>
                    </div>
                    <div class="total-row">
                        <span>جمع کل پرداخت‌ها:</span>
                        <span style="color: #28a745;">{folio_data.get('total_payments', 0):,.0f} تومان</span>
                    </div>
                    <div class="total-row grand-total">
                        <span>مانده قابل پرداخت:</span>
                        <span>{folio_data.get('current_balance', 0):,.0f} تومان</span>
                    </div>
                </div>

                {self.generate_notes_section(folio_data)}

                <div class="footer">
                    <p>با تشکر از انتخاب هتل {config.hotel.name}</p>
                    <p>این فاکتور به صورت خودکار تولید شده است.</p>
                    <p>تاریخ تولید: {datetime.now().strftime("%Y/%m/%d %H:%M")}</p>
                </div>
            </div>
        </body>
        </html>
        """

        return invoice_html

    def generate_notes_section(self, folio_data):
        """تولید بخش یادداشت‌ها"""
        if folio_data.get('current_balance', 0) > 0:
            return """
                <div class="notes">
                    <strong>تذکر مهم:</strong><br>
                    لطفاً مانده قابل پرداخت را تا قبل از زمان خروج تسویه نمایید.<br>
                    در صورت وجود هرگونه مغایرت، لطفاً با پذیرش تماس بگیرید.
                </div>
            """
        else:
            return """
                <div class="notes" style="background-color: #d1ecf1; border-color: #bee5eb;">
                    <strong>پرداخت تکمیل شده:</strong><br>
                    صورت‌حساب شما به طور کامل تسویه شده است.<br>
                    از اقامت شما در هتل متشکریم.
                </div>
            """

    def save_invoice_file(self, html_content):
        """ذخیره فایل صورت‌حساب"""
        export_dir = config.app.export_dir / "invoices"
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"invoice_{self.stay_id}_{timestamp}.html"
        file_path = export_dir / filename

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(file_path)


class InvoiceGeneratorWidget(QWidget):
    """ویجت تولید و مدیریت صورت‌حساب‌های مهمانان"""

    # سیگنال‌ها
    invoice_generated = pyqtSignal(dict)
    invoice_printed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_stay_id = None
        self.current_invoice_data = None
        self.generation_thread = None
        self.init_ui()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # هدر
        header_layout = QHBoxLayout()

        title_label = QLabel("🧾 تولید کننده صورت‌حساب")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # ایجاد تب‌ها
        self.tabs = QTabWidget()

        # تب تولید صورت‌حساب
        self.generation_tab = self.create_generation_tab()
        self.tabs.addTab(self.generation_tab, "🔄 تولید صورت‌حساب")

        # تب پیش‌نمایش
        self.preview_tab = self.create_preview_tab()
        self.tabs.addTab(self.preview_tab, "👁️ پیش‌نمایش")

        # تب تاریخچه
        self.history_tab = self.create_history_tab()
        self.tabs.addTab(self.history_tab, "📋 تاریخچه")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def create_generation_tab(self):
        """ایجاد تب تولید صورت‌حساب"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فرم انتخاب مهمان
        guest_selection_group = self.create_guest_selection_group()
        layout.addWidget(guest_selection_group)

        # تنظیمات صورت‌حساب
        invoice_settings_group = self.create_invoice_settings_group()
        layout.addWidget(invoice_settings_group)

        # نوار پیشرفت
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # دکمه‌های عملیات
        action_layout = QHBoxLayout()

        self.btn_generate = QPushButton("🔄 تولید صورت‌حساب")
        self.btn_generate.clicked.connect(self.generate_invoice)
        self.btn_generate.setEnabled(False)

        self.btn_preview = QPushButton("👁️ پیش‌نمایش")
        self.btn_preview.clicked.connect(self.preview_invoice)
        self.btn_preview.setEnabled(False)

        self.btn_print = QPushButton("🖨️ چاپ")
        self.btn_print.clicked.connect(self.print_invoice)
        self.btn_print.setEnabled(False)

        self.btn_export = QPushButton("💾 ذخیره PDF")
        self.btn_export.clicked.connect(self.export_invoice_pdf)
        self.btn_export.setEnabled(False)

        action_layout.addWidget(self.btn_generate)
        action_layout.addWidget(self.btn_preview)
        action_layout.addWidget(self.btn_print)
        action_layout.addWidget(self.btn_export)
        action_layout.addStretch()

        layout.addLayout(action_layout)

        widget.setLayout(layout)
        return widget

    def create_guest_selection_group(self):
        """گروه انتخاب مهمان"""
        group = QGroupBox("انتخاب مهمان")
        layout = QHBoxLayout()

        layout.addWidget(QLabel("شماره اقامت:"))

        self.txt_stay_id = QLineEdit()
        self.txt_stay_id.setPlaceholderText("شماره اقامت را وارد کنید...")
        self.txt_stay_id.textChanged.connect(self.on_stay_id_changed)
        layout.addWidget(self.txt_stay_id)

        self.btn_load_guest = QPushButton("بارگذاری اطلاعات")
        self.btn_load_guest.clicked.connect(self.load_guest_info)
        self.btn_load_guest.setEnabled(False)
        layout.addWidget(self.btn_load_guest)

        self.lbl_guest_info = QLabel("اطلاعات مهمان بارگذاری نشده")
        self.lbl_guest_info.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.lbl_guest_info)

        layout.addStretch()

        group.setLayout(layout)
        return group

    def create_invoice_settings_group(self):
        """گروه تنظیمات صورت‌حساب"""
        group = QGroupBox("تنظیمات صورت‌حساب")
        layout = QFormLayout()

        self.cmb_template = QComboBox()
        self.cmb_template.addItems(["قالب استاندارد", "قالب تجاری", "قالب ساده"])
        layout.addRow("قالب صورت‌حساب:", self.cmb_template)

        self.chk_include_details = QCheckBox("نمایش جزئیات کامل تراکنش‌ها")
        self.chk_include_details.setChecked(True)
        layout.addRow(self.chk_include_details)

        self.chk_include_tax = QCheckBox("نمایش تفکیک مالیات و عوارض")
        self.chk_include_tax.setChecked(True)
        layout.addRow(self.chk_include_tax)

        self.txt_custom_notes = QTextEdit()
        self.txt_custom_notes.setPlaceholderText("یادداشت‌های سفارشی (اختیاری)...")
        self.txt_custom_notes.setMaximumHeight(80)
        layout.addRow("یادداشت سفارشی:", self.txt_custom_notes)

        group.setLayout(layout)
        return group

    def create_preview_tab(self):
        """ایجاد تب پیش‌نمایش"""
        widget = QWidget()
        layout = QVBoxLayout()

        self.preview_browser = QTextEdit()
        self.preview_browser.setReadOnly(True)
        self.preview_browser.setPlaceholderText("پیش‌نمایش صورت‌حساب در اینجا نمایش داده می‌شود...")
        layout.addWidget(self.preview_browser)

        widget.setLayout(layout)
        return widget

    def create_history_tab(self):
        """ایجاد تب تاریخچه"""
        widget = QWidget()
        layout = QVBoxLayout()

        # TODO: پیاده‌سازی تاریخچه صورت‌حساب‌های تولید شده
        info_label = QLabel("تاریخچه صورت‌حساب‌های تولید شده\n(به زودی)")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 16px; color: #6c757d; margin: 50px;")

        layout.addWidget(info_label)
        widget.setLayout(layout)
        return widget

    def on_stay_id_changed(self, text):
        """هنگام تغییر شماره اقامت"""
        self.btn_load_guest.setEnabled(bool(text.strip()))

    def load_guest_info(self):
        """بارگذاری اطلاعات مهمان"""
        stay_id = self.txt_stay_id.text().strip()
        if not stay_id:
            return

        try:
            # دریافت اطلاعات مهمان
            guest_result = GuestService.get_guest_details(int(stay_id))

            if guest_result['success']:
                guest_data = guest_result['guest']
                self.lbl_guest_info.setText(
                    f"مهمان: {guest_data.get('full_name', '--')} | "
                    f"اتاق: {guest_data.get('room_number', '--')}"
                )
                self.current_stay_id = int(stay_id)
                self.btn_generate.setEnabled(True)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری اطلاعات مهمان: {guest_result.get('error')}")
                self.lbl_guest_info.setText("خطا در بارگذاری اطلاعات")

        except Exception as e:
            logger.error(f"خطا در بارگذاری اطلاعات مهمان: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اطلاعات: {str(e)}")

    def generate_invoice(self):
        """تولید صورت‌حساب"""
        if not self.current_stay_id:
            QMessageBox.warning(self, "هشدار", "لطفاً ابتدا اطلاعات مهمان را بارگذاری کنید")
            return

        # جمع‌آوری داده‌های صورت‌حساب
        invoice_data = {
            'template': self.cmb_template.currentText(),
            'include_details': self.chk_include_details.isChecked(),
            'include_tax': self.chk_include_tax.isChecked(),
            'custom_notes': self.txt_custom_notes.toPlainText(),
            'generated_at': datetime.now()
        }

        # نمایش نوار پیشرفت
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_generate.setEnabled(False)

        # شروع تولید در Thread
        self.generation_thread = InvoiceGenerationThread(self.current_stay_id, invoice_data)
        self.generation_thread.progress.connect(self.progress_bar.setValue)
        self.generation_thread.finished.connect(self.on_invoice_generated)
        self.generation_thread.error.connect(self.on_invoice_error)
        self.generation_thread.start()

    def on_invoice_generated(self, result):
        """هنگام تکمیل تولید صورت‌حساب"""
        self.progress_bar.setVisible(False)
        self.btn_generate.setEnabled(True)

        if result['success']:
            self.current_invoice_data = result
            self.preview_browser.setHtml(result['html_content'])
            self.tabs.setCurrentIndex(1)  # رفتن به تب پیش‌نمایش

            # فعال کردن دکمه‌ها
            self.btn_preview.setEnabled(True)
            self.btn_print.setEnabled(True)
            self.btn_export.setEnabled(True)

            QMessageBox.information(self, "موفق", "صورت‌حساب با موفقیت تولید شد")
            self.invoice_generated.emit(result)
        else:
            QMessageBox.warning(self, "خطا", "خطا در تولید صورت‌حساب")

    def on_invoice_error(self, error_message):
        """هنگام خطا در تولید صورت‌حساب"""
        self.progress_bar.setVisible(False)
        self.btn_generate.setEnabled(True)
        QMessageBox.critical(self, "خطا", error_message)

    def preview_invoice(self):
        """پیش‌نمایش صورت‌حساب"""
        if self.current_invoice_data:
            self.tabs.setCurrentIndex(1)

    def print_invoice(self):
        """چاپ صورت‌حساب"""
        if not self.current_invoice_data:
            QMessageBox.warning(self, "هشدار", "لطفاً ابتدا صورت‌حساب را تولید کنید")
            return

        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.A4)
            printer.setFullPage(True)

            print_dialog = QPrintDialog(printer, self)
            if print_dialog.exec_() == QPrintDialog.Accepted:
                document = QTextDocument()
                document.setHtml(self.current_invoice_data['html_content'])
                document.print_(printer)

                QMessageBox.information(self, "موفق", "صورت‌حساب با موفقیت چاپ شد")
                self.invoice_printed.emit(self.current_invoice_data['file_path'])

        except Exception as e:
            logger.error(f"خطا در چاپ صورت‌حساب: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در چاپ صورت‌حساب: {str(e)}")

    def export_invoice_pdf(self):
        """ذخیره صورت‌حساب به PDF"""
        if not self.current_invoice_data:
            QMessageBox.warning(self, "هشدار", "لطفاً ابتدا صورت‌حساب را تولید کنید")
            return

        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "ذخیره صورت‌حساب به PDF",
                f"invoice_{self.current_stay_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                "PDF Files (*.pdf)"
            )

            if file_path:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QPrinter.A4)

                document = QTextDocument()
                document.setHtml(self.current_invoice_data['html_content'])
                document.print_(printer)

                QMessageBox.information(self, "موفق", f"صورت‌حساب با موفقیت در {file_path} ذخیره شد")

        except Exception as e:
            logger.error(f"خطا در ذخیره PDF: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره PDF: {str(e)}")

    def set_stay_id(self, stay_id):
        """تنظیم شماره اقامت"""
        self.txt_stay_id.setText(str(stay_id))
        self.load_guest_info()

    def get_invoice_data(self):
        """دریافت داده‌های صورت‌حساب فعلی"""
        return self.current_invoice_data

    def clear_invoice(self):
        """پاک کردن صورت‌حساب فعلی"""
        self.current_stay_id = None
        self.current_invoice_data = None
        self.txt_stay_id.clear()
        self.lbl_guest_info.setText("اطلاعات مهمان بارگذاری نشده")
        self.preview_browser.clear()
        self.txt_custom_notes.clear()

        # غیرفعال کردن دکمه‌ها
        self.btn_generate.setEnabled(False)
        self.btn_preview.setEnabled(False)
        self.btn_print.setEnabled(False)
        self.btn_export.setEnabled(False)

    def send_invoice_email(self):
        """ارسال صورت‌حساب از طریق ایمیل"""
        if not self.current_invoice_data:
            QMessageBox.warning(self, "هشدار", "لطفاً ابتدا صورت‌حساب را تولید کنید")
            return

        try:
            # TODO: پیاده‌سازی ارسال ایمیل
            # این بخش نیاز به integration با سرویس ایمیل دارد
            QMessageBox.information(self, "ارسال ایمیل", "ارسال ایمیل - به زودی پیاده‌سازی می‌شود")

        except Exception as e:
            logger.error(f"خطا در ارسال ایمیل: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ارسال ایمیل: {str(e)}")

    def generate_multiple_invoices(self, stay_ids):
        """تولید صورت‌حساب برای چندین اقامت"""
        # TODO: پیاده‌سازی تولید گروهی صورت‌حساب
        QMessageBox.information(self, "تولید گروهی", "تولید گروهی صورت‌حساب - به زودی")

    def get_invoice_statistics(self):
        """دریافت آمار صورت‌حساب‌های تولید شده"""
        try:
            # محاسبه آمار از پوشه خروجی
            export_dir = config.app.export_dir / "invoices"
            if export_dir.exists():
                invoice_files = list(export_dir.glob("invoice_*.html"))
                return {
                    'total_invoices': len(invoice_files),
                    'last_generated': max([f.stat().st_mtime for f in invoice_files]) if invoice_files else 0,
                    'total_size': sum(f.stat().st_size for f in invoice_files)
                }
            return {'total_invoices': 0, 'last_generated': 0, 'total_size': 0}

        except Exception as e:
            logger.error(f"خطا در دریافت آمار صورت‌حساب‌ها: {e}")
            return {'total_invoices': 0, 'last_generated': 0, 'total_size': 0}
