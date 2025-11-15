# app/views/widgets/financial/payment_processing.py
"""
ویجت پردازش پرداخت‌های مهمانان
"""

import logging
from decimal import Decimal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QDoubleSpinBox,
                            QTextEdit, QSplitter, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from app.services.reception.payment_service import PaymentService
from app.services.reception.guest_service import GuestService
from app.core.payment_processor import payment_processor
from config import config

logger = logging.getLogger(__name__)

class PaymentProcessingWidget(QWidget):
    """ویجت پردازش پرداخت‌های مهمانان"""

    # سیگنال‌ها
    payment_completed = pyqtSignal(int)  # ID پرداخت

    def __init__(self, stay_id=None, parent=None):
        super().__init__(parent)
        self.stay_id = stay_id
        self.guest_data = None
        self.folio_data = None
        self.init_ui()
        if stay_id:
            self.load_stay_data()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # ایجاد اسپلیتر برای تقسیم صفحه
        splitter = QSplitter(Qt.Horizontal)

        # پنل سمت چپ - اطلاعات مهمان و صورت‌حساب
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # پنل سمت راست - پردازش پرداخت
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # تنظیم سایز اولیه
        splitter.setSizes([500, 400])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def create_left_panel(self):
        """ایجاد پنل سمت چپ"""
        widget = QWidget()
        layout = QVBoxLayout()

        # اطلاعات مهمان
        guest_info_group = self.create_guest_info_group()
        layout.addWidget(guest_info_group)

        # صورت‌حساب
        folio_group = self.create_folio_group()
        layout.addWidget(folio_group)

        widget.setLayout(layout)
        return widget

    def create_guest_info_group(self):
        """گروه اطلاعات مهمان"""
        group = QGroupBox("اطلاعات مهمان")
        layout = QFormLayout()

        self.lbl_guest_name = QLabel("--")
        self.lbl_room_number = QLabel("--")
        self.lbl_stay_id = QLabel("--")
        self.lbl_check_in = QLabel("--")
        self.lbl_check_out = QLabel("--")

        layout.addRow("نام مهمان:", self.lbl_guest_name)
        layout.addRow("شماره اتاق:", self.lbl_room_number)
        layout.addRow("شماره اقامت:", self.lbl_stay_id)
        layout.addRow("تاریخ ورود:", self.lbl_check_in)
        layout.addRow("تاریخ خروج:", self.lbl_check_out)

        group.setLayout(layout)
        return group

    def create_folio_group(self):
        """گروه صورت‌حساب"""
        group = QGroupBox("صورت‌حساب")
        layout = QVBoxLayout()

        # خلاصه صورت‌حساب
        summary_layout = QHBoxLayout()

        self.lbl_total_charges = QLabel("0")
        self.lbl_total_charges.setStyleSheet("font-weight: bold; color: #c0392b;")

        self.lbl_total_payments = QLabel("0")
        self.lbl_total_payments.setStyleSheet("font-weight: bold; color: #27ae60;")

        self.lbl_balance = QLabel("0")
        self.lbl_balance.setStyleSheet("font-weight: bold; color: #2980b9;")

        summary_layout.addWidget(QLabel("هزینه‌ها:"))
        summary_layout.addWidget(self.lbl_total_charges)
        summary_layout.addWidget(QLabel("پرداخت‌ها:"))
        summary_layout.addWidget(self.lbl_total_payments)
        summary_layout.addWidget(QLabel("مانده:"))
        summary_layout.addWidget(self.lbl_balance)
        summary_layout.addStretch()

        layout.addLayout(summary_layout)

        # جدول تراکنش‌ها
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels([
            "تاریخ", "نوع", "مبلغ", "شرح", "وضعیت"
        ])

        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        layout.addWidget(self.transactions_table)

        group.setLayout(layout)
        return group

    def create_right_panel(self):
        """ایجاد پنل سمت راست"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فرم پرداخت
        payment_form_group = self.create_payment_form_group()
        layout.addWidget(payment_form_group)

        # پرداخت کارتی
        card_payment_group = self.create_card_payment_group()
        layout.addWidget(card_payment_group)

        # پرداخت نقدی
        cash_payment_group = self.create_cash_payment_group()
        layout.addWidget(cash_payment_group)

        # نوار عملیات
        action_layout = self.create_action_layout()
        layout.addLayout(action_layout)

        widget.setLayout(layout)
        return widget

    def create_payment_form_group(self):
        """گروه فرم پرداخت"""
        group = QGroupBox("پرداخت جدید")
        layout = QFormLayout()

        self.spn_amount = QDoubleSpinBox()
        self.spn_amount.setRange(0, 100000000)
        self.spn_amount.setSuffix(" تومان")
        self.spn_amount.setDecimals(0)
        self.spn_amount.valueChanged.connect(self.on_amount_changed)

        self.cmb_payment_type = QComboBox()
        self.cmb_payment_type.addItems(["تسویه", "پیش پرداخت", "ودیعه", "سایر"])

        self.cmb_payment_method = QComboBox()
        self.cmb_payment_method.addItems(["نقدی", "کارت‌خوان", "حواله بانکی", "آژانس"])
        self.cmb_payment_method.currentTextChanged.connect(self.on_payment_method_changed)

        self.txt_description = QLineEdit()
        self.txt_description.setPlaceholderText("شرح پرداخت...")

        layout.addRow("مبلغ:", self.spn_amount)
        layout.addRow("نوع پرداخت:", self.cmb_payment_type)
        layout.addRow("روش پرداخت:", self.cmb_payment_method)
        layout.addRow("شرح:", self.txt_description)

        group.setLayout(layout)
        return group

    def create_card_payment_group(self):
        """گروه پرداخت کارتی"""
        self.card_group = QGroupBox("پرداخت کارتی")
        layout = QFormLayout()

        self.txt_card_number = QLineEdit()
        self.txt_card_number.setPlaceholderText("شماره کارت (16 رقم)")
        self.txt_card_number.setMaxLength(16)

        self.txt_expiry_date = QLineEdit()
        self.txt_expiry_date.setPlaceholderText("MM/YY")
        self.txt_expiry_date.setMaxLength(5)

        self.txt_cvv2 = QLineEdit()
        self.txt_cvv2.setPlaceholderText("CVV2")
        self.txt_cvv2.setMaxLength(4)
        self.txt_cvv2.setEchoMode(QLineEdit.Password)

        layout.addRow("شماره کارت:", self.txt_card_number)
        layout.addRow("تاریخ انقضا:", self.txt_expiry_date)
        layout.addRow("CVV2:", self.txt_cvv2)

        self.card_group.setLayout(layout)
        self.card_group.setVisible(False)  # مخفی در ابتدا
        return self.card_group

    def create_cash_payment_group(self):
        """گروه پرداخت نقدی"""
        self.cash_group = QGroupBox("پرداخت نقدی")
        layout = QFormLayout()

        self.spn_cash_received = QDoubleSpinBox()
        self.spn_cash_received.setRange(0, 100000000)
        self.spn_cash_received.setSuffix(" تومان")
        self.spn_cash_received.setDecimals(0)
        self.spn_cash_received.valueChanged.connect(self.on_cash_received_changed)

        self.lbl_change = QLabel("0 تومان")
        self.lbl_change.setStyleSheet("font-weight: bold; color: #27ae60;")

        layout.addRow("مبلغ دریافتی:", self.spn_cash_received)
        layout.addRow("علاوه:", self.lbl_change)

        self.cash_group.setLayout(layout)
        self.cash_group.setVisible(False)  # مخفی در ابتدا
        return self.cash_group

    def create_action_layout(self):
        """نوار عملیات"""
        layout = QHBoxLayout()

        self.btn_process_payment = QPushButton("پردازش پرداخت")
        self.btn_process_payment.clicked.connect(self.process_payment)
        self.btn_process_payment.setEnabled(False)

        self.btn_cancel = QPushButton("انصراف")
        self.btn_cancel.clicked.connect(self.cancel_payment)

        self.btn_print_receipt = QPushButton("چاپ رسید")
        self.btn_print_receipt.clicked.connect(self.print_receipt)
        self.btn_print_receipt.setEnabled(False)

        layout.addWidget(self.btn_process_payment)
        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.btn_print_receipt)
        layout.addStretch()

        return layout

    def load_stay_data(self):
        """بارگذاری اطلاعات اقامت"""
        if not self.stay_id:
            return

        try:
            # دریافت اطلاعات صورت‌حساب
            folio_result = PaymentService.get_guest_folio(self.stay_id)

            if folio_result['success']:
                self.folio_data = folio_result['folio']
                self.populate_folio_data()
                self.update_payment_button()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری صورت‌حساب: {folio_result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری اطلاعات اقامت: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اطلاعات: {str(e)}")

    def populate_folio_data(self):
        """پر کردن اطلاعات صورت‌حساب"""
        if not self.folio_data:
            return

        # به‌روزرسانی خلاصه
        self.lbl_total_charges.setText(f"{self.folio_data['total_charges']:,.0f}")
        self.lbl_total_payments.setText(f"{self.folio_data['total_payments']:,.0f}")
        self.lbl_balance.setText(f"{self.folio_data['current_balance']:,.0f}")

        # تنظیم مبلغ پیشنهادی برای پرداخت
        balance = Decimal(str(self.folio_data['current_balance']))
        if balance > 0:
            self.spn_amount.setValue(float(balance))

        # پر کردن جدول تراکنش‌ها
        transactions = self.folio_data['transactions']
        self.transactions_table.setRowCount(len(transactions))

        for row, transaction in enumerate(transactions):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(
                transaction['created_at'].strftime("%Y/%m/%d %H:%M")
            ))

            type_text = "هزینه" if transaction['type'] == 'charge' else 'پرداخت'
            self.transactions_table.setItem(row, 1, QTableWidgetItem(type_text))

            amount_item = QTableWidgetItem(f"{transaction['amount']:,.0f}")
            if transaction['type'] == 'charge':
                amount_item.setForeground(QColor(200, 0, 0))  # قرمز برای هزینه
            else:
                amount_item.setForeground(QColor(0, 150, 0))  # سبز برای پرداخت
            self.transactions_table.setItem(row, 2, amount_item)

            self.transactions_table.setItem(row, 3, QTableWidgetItem(transaction['description']))
            self.transactions_table.setItem(row, 4, QTableWidgetItem("تکمیل شده"))

    def on_payment_method_changed(self, method):
        """هنگام تغییر روش پرداخت"""
        # مخفی/نمایش کردن گروه‌های مربوطه
        self.card_group.setVisible(method == "کارت‌خوان")
        self.cash_group.setVisible(method == "نقدی")

    def on_amount_changed(self, amount):
        """هنگام تغییر مبلغ"""
        self.update_payment_button()

    def on_cash_received_changed(self, received):
        """هنگام تغییر مبلغ دریافتی نقدی"""
        amount = self.spn_amount.value()
        change = received - amount
        self.lbl_change.setText(f"{change:,.0f} تومان")

        if change < 0:
            self.lbl_change.setStyleSheet("font-weight: bold; color: #c0392b;")
        else:
            self.lbl_change.setStyleSheet("font-weight: bold; color: #27ae60;")

    def update_payment_button(self):
        """به‌روزرسانی وضعیت دکمه پرداخت"""
        amount = self.spn_amount.value()
        method = self.cmb_payment_method.currentText()

        enabled = amount > 0

        if method == "نقدی":
            received = self.spn_cash_received.value()
            enabled = enabled and received >= amount
        elif method == "کارت‌خوان":
            enabled = enabled and self.validate_card_data()

        self.btn_process_payment.setEnabled(enabled)

    def validate_card_data(self):
        """اعتبارسنجی داده‌های کارت"""
        card_number = self.txt_card_number.text().strip()
        expiry = self.txt_expiry_date.text().strip()
        cvv2 = self.txt_cvv2.text().strip()

        if len(card_number) != 16 or not card_number.isdigit():
            return False

        if len(expiry) != 5 or not expiry.replace('/', '').isdigit():
            return False

        if len(cvv2) < 3 or not cvv2.isdigit():
            return False

        return True

    def process_payment(self):
        """پردازش پرداخت"""
        try:
            amount = Decimal(str(self.spn_amount.value()))
            payment_method = self.cmb_payment_method.currentText()
            payment_type = self.cmb_payment_type.currentText()
            description = self.txt_description.text().strip() or "پرداخت اقامت"

            payment_data = {
                'amount': amount,
                'payment_method': payment_method,
                'payment_type': payment_type,
                'description': description
            }

            # افزودن داده‌های خاص هر روش
            if payment_method == "کارت‌خوان":
                payment_data['card_data'] = {
                    'card_number': self.txt_card_number.text(),
                    'expiry_date': self.txt_expiry_date.text(),
                    'cvv2': self.txt_cvv2.text()
                }
            elif payment_method == "نقدی":
                payment_data['cash_received'] = Decimal(str(self.spn_cash_received.value()))

            # پردازش پرداخت
            result = PaymentService.process_payment(
                self.stay_id, amount, payment_method, payment_data
            )

            if result['success']:
                QMessageBox.information(self, "موفق", "پرداخت با موفقیت انجام شد")
                self.btn_print_receipt.setEnabled(True)
                self.payment_completed.emit(result['payment_id'])
                self.reset_form()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در پردازش پرداخت: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در پردازش پرداخت: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در پردازش پرداخت: {str(e)}")

    def reset_form(self):
        """بازنشانی فرم"""
        self.spn_amount.setValue(0)
        self.txt_description.clear()
        self.txt_card_number.clear()
        self.txt_expiry_date.clear()
        self.txt_cvv2.clear()
        self.spn_cash_received.setValue(0)
        self.cmb_payment_method.setCurrentIndex(0)

    def cancel_payment(self):
        """انصراف از پرداخت"""
        self.reset_form()

    def print_receipt(self):
        """چاپ رسید"""
        try:
            # TODO: پیاده‌سازی چاپ رسید
            QMessageBox.information(self, "چاپ", "رسید با موفقیت چاپ شد")
        except Exception as e:
            logger.error(f"خطا در چاپ رسید: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در چاپ رسید: {str(e)}")

    def set_stay_id(self, stay_id):
        """تنظیم ID اقامت جدید"""
        self.stay_id = stay_id
        self.load_stay_data()
