# app/views/widgets/guest_management/guest_details_widget.py
"""
ویجت نمایش و ویرایش اطلاعات کامل مهمان
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QTextEdit, QComboBox, QDateEdit,
                            QGroupBox, QPushButton, QMessageBox, QTabWidget,
                            QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import QDate, pyqtSignal
from datetime import datetime

from app.services.reception.guest_service import GuestService
from app.services.reception.payment_service import PaymentService

logger = logging.getLogger(__name__)

class GuestDetailsWidget(QWidget):
    """ویجت نمایش و ویرایش اطلاعات مهمان"""

    # سیگنال‌ها
    data_updated = pyqtSignal()

    def __init__(self, guest_id=None, parent=None):
        super().__init__(parent)
        self.guest_id = guest_id
        self.guest_data = None
        self.init_ui()
        if guest_id:
            self.load_guest_data()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # تب‌های اطلاعات
        self.tabs = QTabWidget()

        # تب اطلاعات اصلی
        self.basic_info_tab = self.create_basic_info_tab()
        self.tabs.addTab(self.basic_info_tab, "اطلاعات اصلی")

        # تب اطلاعات اقامت
        self.stay_info_tab = self.create_stay_info_tab()
        self.tabs.addTab(self.stay_info_tab, "اطلاعات اقامت")

        # تب صورت‌حساب
        self.folio_tab = self.create_folio_tab()
        self.tabs.addTab(self.folio_tab, "صورت‌حساب")

        main_layout.addWidget(self.tabs)

        # نوار عملیات
        action_layout = self.create_action_layout()
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

    def create_basic_info_tab(self):
        """ایجاد تب اطلاعات اصلی"""
        widget = QWidget()
        layout = QVBoxLayout()

        # اطلاعات هویتی
        identity_group = self.create_identity_group()
        layout.addWidget(identity_group)

        # اطلاعات تماس
        contact_group = self.create_contact_group()
        layout.addWidget(contact_group)

        # اطلاعات شرکتی
        company_group = self.create_company_group()
        layout.addWidget(company_group)

        # ترجیحات
        preferences_group = self.create_preferences_group()
        layout.addWidget(preferences_group)

        widget.setLayout(layout)
        return widget

    def create_identity_group(self):
        """گروه اطلاعات هویتی"""
        group = QGroupBox("اطلاعات هویتی")
        layout = QFormLayout()

        self.txt_first_name = QLineEdit()
        self.txt_last_name = QLineEdit()
        self.txt_national_id = QLineEdit()
        self.txt_passport = QLineEdit()
        self.cmb_gender = QComboBox()
        self.cmb_gender.addItems(["", "مرد", "زن"])
        self.date_birth = QDateEdit()
        self.date_birth.setCalendarPopup(True)
        self.date_birth.setMaximumDate(QDate.currentDate())
        self.cmb_nationality = QComboBox()
        self.cmb_nationality.addItems(["ایرانی", "افغانستانی", "عراقی", "سایر"])

        layout.addRow("نام:", self.txt_first_name)
        layout.addRow("نام خانوادگی:", self.txt_last_name)
        layout.addRow("کدملی:", self.txt_national_id)
        layout.addRow("شماره پاسپورت:", self.txt_passport)
        layout.addRow("جنسیت:", self.cmb_gender)
        layout.addRow("تاریخ تولد:", self.date_birth)
        layout.addRow("ملیت:", self.cmb_nationality)

        group.setLayout(layout)
        return group

    def create_contact_group(self):
        """گروه اطلاعات تماس"""
        group = QGroupBox("اطلاعات تماس")
        layout = QFormLayout()

        self.txt_phone = QLineEdit()
        self.txt_email = QLineEdit()
        self.txt_address = QTextEdit()
        self.txt_address.setMaximumHeight(80)
        self.txt_emergency_contact = QLineEdit()
        self.txt_emergency_phone = QLineEdit()

        layout.addRow("تلفن همراه:", self.txt_phone)
        layout.addRow("ایمیل:", self.txt_email)
        layout.addRow("آدرس:", self.txt_address)
        layout.addRow("تماس اضطراری:", self.txt_emergency_contact)
        layout.addRow("تلفن اضطراری:", self.txt_emergency_phone)

        group.setLayout(layout)
        return group

    def create_company_group(self):
        """گروه اطلاعات شرکتی"""
        group = QGroupBox("اطلاعات شرکتی")
        layout = QFormLayout()

        self.txt_company_name = QLineEdit()
        self.txt_company_address = QTextEdit()
        self.txt_company_address.setMaximumHeight(60)
        self.txt_business_title = QLineEdit()

        layout.addRow("نام شرکت:", self.txt_company_name)
        layout.addRow("آدرس شرکت:", self.txt_company_address)
        layout.addRow("سمت:", self.txt_business_title)

        group.setLayout(layout)
        return group

    def create_preferences_group(self):
        """گروه ترجیحات و اطلاعات ویژه"""
        group = QGroupBox("ترجیحات و اطلاعات ویژه")
        layout = QFormLayout()

        self.txt_special_requests = QTextEdit()
        self.txt_special_requests.setMaximumHeight(80)
        self.chk_vip = QPushButton("مهمان ویژه")
        self.chk_vip.setCheckable(True)
        self.txt_blacklist_reason = QLineEdit()

        layout.addRow("درخواست‌های ویژه:", self.txt_special_requests)
        layout.addRow("وضعیت VIP:", self.chk_vip)
        layout.addRow("دلیل لیست سیاه:", self.txt_blacklist_reason)

        group.setLayout(layout)
        return group

    def create_stay_info_tab(self):
        """ایجاد تب اطلاعات اقامت"""
        widget = QWidget()
        layout = QVBoxLayout()

        # اطلاعات اقامت فعلی
        current_stay_group = self.create_current_stay_group()
        layout.addWidget(current_stay_group)

        # تاریخچه اقامت‌ها
        history_group = self.create_stay_history_group()
        layout.addWidget(history_group)

        widget.setLayout(layout)
        return widget

    def create_current_stay_group(self):
        """گروه اطلاعات اقامت فعلی"""
        group = QGroupBox("اطلاعات اقامت فعلی")
        layout = QFormLayout()

        self.lbl_reservation_id = QLabel("--")
        self.lbl_check_in = QLabel("--")
        self.lbl_check_out = QLabel("--")
        self.lbl_room_number = QLabel("--")
        self.lbl_stay_purpose = QLabel("--")
        self.lbl_status = QLabel("--")

        layout.addRow("شماره رزرو:", self.lbl_reservation_id)
        layout.addRow("تاریخ ورود:", self.lbl_check_in)
        layout.addRow("تاریخ خروج:", self.lbl_check_out)
        layout.addRow("شماره اتاق:", self.lbl_room_number)
        layout.addRow("هدف اقامت:", self.lbl_stay_purpose)
        layout.addRow("وضعیت:", self.lbl_status)

        group.setLayout(layout)
        return group

    def create_stay_history_group(self):
        """گروه تاریخچه اقامت‌ها"""
        group = QGroupBox("تاریخچه اقامت‌ها")
        layout = QVBoxLayout()

        self.stay_history_table = QTableWidget()
        self.stay_history_table.setColumnCount(5)
        self.stay_history_table.setHorizontalHeaderLabels([
            "تاریخ ورود", "تاریخ خروج", "اتاق", "وضعیت", "مبلغ"
        ])

        # تنظیمات جدول
        header = self.stay_history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.stay_history_table)
        group.setLayout(layout)
        return group

    def create_folio_tab(self):
        """ایجاد تب صورت‌حساب"""
        widget = QWidget()
        layout = QVBoxLayout()

        # خلاصه صورت‌حساب
        summary_group = self.create_folio_summary_group()
        layout.addWidget(summary_group)

        # تراکنش‌ها
        transactions_group = self.create_transactions_group()
        layout.addWidget(transactions_group)

        widget.setLayout(layout)
        return widget

    def create_folio_summary_group(self):
        """گروه خلاصه صورت‌حساب"""
        group = QGroupBox("خلاصه صورت‌حساب")
        layout = QFormLayout()

        self.lbl_total_charges = QLabel("0")
        self.lbl_total_payments = QLabel("0")
        self.lbl_current_balance = QLabel("0")
        self.lbl_folio_status = QLabel("--")

        layout.addRow("مجموع هزینه‌ها:", self.lbl_total_charges)
        layout.addRow("مجموع پرداخت‌ها:", self.lbl_total_payments)
        layout.addRow("مانده حساب:", self.lbl_current_balance)
        layout.addRow("وضعیت:", self.lbl_folio_status)

        group.setLayout(layout)
        return group

    def create_transactions_group(self):
        """گروه تراکنش‌های صورت‌حساب"""
        group = QGroupBox("تراکنش‌ها")
        layout = QVBoxLayout()

        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(5)
        self.transactions_table.setHorizontalHeaderLabels([
            "تاریخ", "نوع", "مبلغ", "شرح", "دسته‌بندی"
        ])

        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.transactions_table)
        group.setLayout(layout)
        return group

    def create_action_layout(self):
        """ایجاد نوار عملیات"""
        layout = QHBoxLayout()

        self.btn_save = QPushButton("ذخیره تغییرات")
        self.btn_save.clicked.connect(self.save_guest_data)

        self.btn_cancel = QPushButton("انصراف")
        self.btn_cancel.clicked.connect(self.cancel_changes)

        self.btn_refresh = QPushButton("بروزرسانی")
        self.btn_refresh.clicked.connect(self.load_guest_data)

        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_cancel)
        layout.addWidget(self.btn_refresh)
        layout.addStretch()

        return layout

    def load_guest_data(self):
        """بارگذاری اطلاعات مهمان"""
        if not self.guest_id:
            return

        try:
            result = GuestService.get_guest_details(self.guest_id)

            if result['success']:
                self.guest_data = result['guest']
                self.populate_guest_data()
                self.load_folio_data()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری اطلاعات: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری اطلاعات مهمان: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اطلاعات: {str(e)}")

    def populate_guest_data(self):
        """پر کردن فرم با داده مهمان"""
        if not self.guest_data:
            return

        # اطلاعات هویتی
        self.txt_first_name.setText(self.guest_data.get('first_name', ''))
        self.txt_last_name.setText(self.guest_data.get('last_name', ''))
        self.txt_national_id.setText(self.guest_data.get('national_id', ''))
        self.txt_passport.setText(self.guest_data.get('passport_number', ''))

        # اطلاعات اقامت
        active_stays = self.guest_data.get('active_stays', [])
        if active_stays:
            stay = active_stays[0]
            self.lbl_reservation_id.setText(str(stay.get('stay_id', '--')))
            self.lbl_check_in.setText(stay.get('planned_check_in', '--'))
            self.lbl_check_out.setText(stay.get('planned_check_out', '--'))
            self.lbl_status.setText(stay.get('status', '--'))

    def load_folio_data(self):
        """بارگذاری اطلاعات صورت‌حساب"""
        if not self.guest_data:
            return

        try:
            # پیدا کردن اقامت فعال
            active_stays = self.guest_data.get('active_stays', [])
            if not active_stays:
                return

            stay_id = active_stays[0]['stay_id']
            result = PaymentService.get_guest_folio(stay_id)

            if result['success']:
                folio = result['folio']
                self.populate_folio_data(folio)

        except Exception as e:
            logger.error(f"خطا در بارگذاری صورت‌حساب: {e}")

    def populate_folio_data(self, folio):
        """پر کردن اطلاعات صورت‌حساب"""
        self.lbl_total_charges.setText(f"{folio['total_charges']:,.0f}")
        self.lbl_total_payments.setText(f"{folio['total_payments']:,.0f}")
        self.lbl_current_balance.setText(f"{folio['current_balance']:,.0f}")
        self.lbl_folio_status.setText(folio['folio_status'])

        # پر کردن جدول تراکنش‌ها
        self.transactions_table.setRowCount(len(folio['transactions']))
        for row, transaction in enumerate(folio['transactions']):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(
                transaction['created_at'].strftime("%Y/%m/%d %H:%M")
            ))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(
                transaction['type']
            ))
            self.transactions_table.setItem(row, 2, QTableWidgetItem(
                f"{transaction['amount']:,.0f}"
            ))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(
                transaction['description']
            ))
            self.transactions_table.setItem(row, 4, QTableWidgetItem(
                transaction.get('category', '')
            ))

    def save_guest_data(self):
        """ذخیره تغییرات اطلاعات مهمان"""
        try:
            # جمع‌آوری داده‌های فرم
            guest_update = {
                'first_name': self.txt_first_name.text().strip(),
                'last_name': self.txt_last_name.text().strip(),
                'national_id': self.txt_national_id.text().strip(),
                'passport_number': self.txt_passport.text().strip(),
                'phone': self.txt_phone.text().strip(),
                'email': self.txt_email.text().strip(),
                'vip_status': self.chk_vip.isChecked()
            }

            # TODO: ارسال به سرویس برای به‌روزرسانی
            # این بخش نیاز به پیاده‌سازی متد update در GuestService دارد

            QMessageBox.information(self, "موفق", "اطلاعات مهمان با موفقیت به‌روزرسانی شد")
            self.data_updated.emit()

        except Exception as e:
            logger.error(f"خطا در ذخیره اطلاعات مهمان: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره اطلاعات: {str(e)}")

    def cancel_changes(self):
        """بازنشانی تغییرات"""
        self.load_guest_data()

    def set_guest_id(self, guest_id):
        """تنظیم ID مهمان جدید"""
        self.guest_id = guest_id
        self.load_guest_data()
