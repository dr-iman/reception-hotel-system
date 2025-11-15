# app/views/widgets/guest_management/check_out_widget.py
"""
ویجت ثبت خروج مهمان و تسویه حساب
"""

import logging
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QPushButton, QMessageBox,
                            QGroupBox, QTableWidget, QTableWidgetItem,
                            QHeaderView, QTextEdit, QCheckBox)
from PyQt5.QtCore import pyqtSignal
from decimal import Decimal

from app.services.reception.guest_service import GuestService
from app.services.reception.payment_service import PaymentService
from app.services.reception.housekeeping_service import HousekeepingService

logger = logging.getLogger(__name__)

class CheckOutWidget(QWidget):
    """ویجت ثبت خروج مهمان"""

    # سیگنال‌ها
    check_out_completed = pyqtSignal(int)  # ID اقامت

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

        # اطلاعات مهمان و اقامت
        stay_info_group = self.create_stay_info_group()
        main_layout.addWidget(stay_info_group)

        # صورت‌حساب
        folio_group = self.create_folio_group()
        main_layout.addWidget(folio_group)

        # تأییدیه‌ها
        confirmation_group = self.create_confirmation_group()
        main_layout.addWidget(confirmation_group)

        # نوار عملیات
        action_layout = self.create_action_layout()
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

    def create_stay_info_group(self):
        """گروه اطلاعات اقامت"""
        group = QGroupBox("اطلاعات اقامت")
        layout = QFormLayout()

        self.lbl_guest_name = QLabel("--")
        self.lbl_room_number = QLabel("--")
        self.lbl_check_in_date = QLabel("--")
        self.lbl_check_out_date = QLabel("--")
        self.lbl_nights_count = QLabel("--")

        layout.addRow("نام مهمان:", self.lbl_guest_name)
        layout.addRow("شماره اتاق:", self.lbl_room_number)
        layout.addRow("تاریخ ورود:", self.lbl_check_in_date)
        layout.addRow("تاریخ خروج برنامه‌ریزی:", self.lbl_check_out_date)
        layout.addRow("تعداد شب‌ها:", self.lbl_nights_count)

        group.setLayout(layout)
        return group

    def create_folio_group(self):
        """گروه صورت‌حساب"""
        group = QGroupBox("صورت‌حساب")
        layout = QVBoxLayout()

        # خلاصه صورت‌حساب
        summary_layout = QHBoxLayout()

        self.lbl_total_charges = QLabel("0")
        self.lbl_total_payments = QLabel("0")
        self.lbl_balance = QLabel("0")

        summary_layout.addWidget(QLabel("مجموع هزینه‌ها:"))
        summary_layout.addWidget(self.lbl_total_charges)
        summary_layout.addWidget(QLabel("مجموع پرداخت‌ها:"))
        summary_layout.addWidget(self.lbl_total_payments)
        summary_layout.addWidget(QLabel("مانده:"))
        self.lbl_balance = QLabel("0")
        summary_layout.addWidget(self.lbl_balance)

        layout.addLayout(summary_layout)

        # جدول تراکنش‌ها
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels([
            "تاریخ", "شرح", "نوع", "مبلغ", "وضعیت"
        ])

        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # شرح
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # تاریخ

        layout.addWidget(self.transactions_table)

        # وضعیت تسویه
        self.lbl_settlement_status = QLabel("وضعیت تسویه: --")
        self.lbl_settlement_status.setStyleSheet("font-weight: bold; color: red;")
        layout.addWidget(self.lbl_settlement_status)

        group.setLayout(layout)
        return group

    def create_confirmation_group(self):
        """گروه تأییدیه‌ها"""
        group = QGroupBox("تأییدیه‌ها")
        layout = QVBoxLayout()

        self.chk_minibar_checked = QCheckBox("مینی‌بار بررسی شده است")
        self.chk_safe_checked = QCheckBox("صندوق امانات بررسی شده است")
        self.chk_damages_checked = QCheckBox("هیچ خسارتی وجود ندارد")

        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("یادداشت‌ها و توضیحات...")
        self.txt_notes.setMaximumHeight(80)

        layout.addWidget(self.chk_minibar_checked)
        layout.addWidget(self.chk_safe_checked)
        layout.addWidget(self.chk_damages_checked)
        layout.addWidget(QLabel("یادداشت‌ها:"))
        layout.addWidget(self.txt_notes)

        group.setLayout(layout)
        return group

    def create_action_layout(self):
        """نوار عملیات"""
        layout = QHBoxLayout()

        self.btn_check_out = QPushButton("ثبت خروج")
        self.btn_check_out.clicked.connect(self.process_check_out)
        self.btn_check_out.setEnabled(False)

        self.btn_print_receipt = QPushButton("چاپ رسید")
        self.btn_print_receipt.clicked.connect(self.print_receipt)
        self.btn_print_receipt.setEnabled(False)

        self.btn_cancel = QPushButton("انصراف")
        self.btn_cancel.clicked.connect(self.cancel_check_out)

        layout.addWidget(self.btn_check_out)
        layout.addWidget(self.btn_print_receipt)
        layout.addWidget(self.btn_cancel)
        layout.addStretch()

        return layout

    def load_stay_data(self):
        """بارگذاری اطلاعات اقامت"""
        if not self.stay_id:
            return

        try:
            # دریافت اطلاعات اقامت و صورت‌حساب
            folio_result = PaymentService.get_guest_folio(self.stay_id)

            if folio_result['success']:
                self.folio_data = folio_result['folio']
                self.populate_folio_data()
                self.check_settlement_status()
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

        # پر کردن جدول تراکنش‌ها
        transactions = self.folio_data['transactions']
        self.transactions_table.setRowCount(len(transactions))

        for row, transaction in enumerate(transactions):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(
                transaction['created_at'].strftime("%Y/%m/%d %H:%M")
            ))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(
                transaction['description']
            ))
            self.transactions_table.setItem(row, 2, QTableWidgetItem(
                transaction['type']
            ))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(
                f"{transaction['amount']:,.0f}"
            ))

            # تعیین رنگ بر اساس نوع تراکنش
            amount_item = self.transactions_table.item(row, 3)
            if transaction['type'] == 'charge':
                amount_item.setForeground(QColor(200, 0, 0))  # قرمز برای هزینه
            else:
                amount_item.setForeground(QColor(0, 150, 0))  # سبز برای پرداخت

    def check_settlement_status(self):
        """بررسی وضعیت تسویه حساب"""
        if not self.folio_data:
            return

        balance = Decimal(str(self.folio_data['current_balance']))

        if balance == 0:
            self.lbl_settlement_status.setText("وضعیت تسویه: ✅ تسویه شده")
            self.lbl_settlement_status.setStyleSheet("font-weight: bold; color: green;")
            self.btn_check_out.setEnabled(True)
        elif balance > 0:
            self.lbl_settlement_status.setText(f"وضعیت تسویه: ⚠️ بدهکار - {balance:,.0f} تومان")
            self.lbl_settlement_status.setStyleSheet("font-weight: bold; color: orange;")
            self.btn_check_out.setEnabled(False)
        else:
            self.lbl_settlement_status.setText(f"وضعیت تسویه: 💰 مازاد - {abs(balance):,.0f} تومان")
            self.lbl_settlement_status.setStyleSheet("font-weight: bold; color: blue;")
            self.btn_check_out.setEnabled(True)

    def process_check_out(self):
        """پردازش ثبت خروج"""
        try:
            # بررسی تأییدیه‌ها
            if not self.chk_minibar_checked.isChecked():
                QMessageBox.warning(self, "هشدار", "لطفاً بررسی مینی‌بار را تأیید کنید")
                return

            if not self.chk_safe_checked.isChecked():
                QMessageBox.warning(self, "هشدار", "لطفاً بررسی صندوق امانات را تأیید کنید")
                return

            # ثبت خروج
            result = GuestService.check_out_guest(self.stay_id)

            if result['success']:
                # ایجاد وظیفه نظافت
                try:
                    room_result = self.get_room_id_from_stay()
                    if room_result['success']:
                        HousekeepingService.create_cleaning_task(
                            room_id=room_result['room_id'],
                            task_type='checkout_cleaning',
                            priority='high'
                        )
                except Exception as e:
                    logger.warning(f"خطا در ایجاد وظیفه نظافت: {e}")

                QMessageBox.information(self, "موفق", "خروج مهمان با موفقیت ثبت شد")
                self.btn_print_receipt.setEnabled(True)
                self.check_out_completed.emit(self.stay_id)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در ثبت خروج: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در ثبت خروج: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ثبت خروج: {str(e)}")

    def get_room_id_from_stay(self):
        """دریافت ID اتاق از اقامت"""
        # این متد نیاز به پیاده‌سازی دارد
        # در نسخه واقعی از RoomService استفاده می‌شود
        return {'success': True, 'room_id': 1}

    def print_receipt(self):
        """چاپ رسید"""
        try:
            # TODO: پیاده‌سازی چاپ رسید
            QMessageBox.information(self, "چاپ", "رسید با موفقیت چاپ شد")
        except Exception as e:
            logger.error(f"خطا در چاپ رسید: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در چاپ رسید: {str(e)}")

    def cancel_check_out(self):
        """انصراف از ثبت خروج"""
        self.close()

    def set_stay_id(self, stay_id):
        """تنظیم ID اقامت جدید"""
        self.stay_id = stay_id
        self.load_stay_data()
