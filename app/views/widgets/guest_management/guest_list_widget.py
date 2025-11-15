# app/views/widgets/guest_management/guest_list_widget.py
"""
ویجت لیست مهمانان و جستجوی پیشرفته
"""

import logging
from datetime import datetime, date
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QLineEdit, QComboBox,
                            QLabel, QMessageBox, QHeaderView, QGroupBox,
                            QFormLayout, QDateEdit, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush

from app.services.reception.guest_service import GuestService
from config import config

logger = logging.getLogger(__name__)

class GuestListWidget(QWidget):
    """ویجت لیست مهمانان با قابلیت جستجوی پیشرفته"""

    # سیگنال‌ها
    guest_selected = pyqtSignal(int)  # ارسال ID مهمان انتخاب شده
    check_in_requested = pyqtSignal(int)  # درخواست ثبت ورود
    check_out_requested = pyqtSignal(int)  # درخواست ثبت خروج

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_guests = []
        self.selected_guest_id = None
        self.init_ui()
        self.load_guests()

        # تایمر برای به‌روزرسانی خودکار
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.load_guests)
        self.auto_refresh_timer.start(30000)  # هر 30 ثانیه

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # نوار جستجو و فیلتر
        search_group = self.create_search_group()
        main_layout.addWidget(search_group)

        # جدول مهمانان
        self.guest_table = self.create_guest_table()
        main_layout.addWidget(self.guest_table)

        # نوار عملیات
        action_group = self.create_action_group()
        main_layout.addWidget(action_group)

        self.setLayout(main_layout)

    def create_search_group(self):
        """ایجاد گروه جستجو و فیلتر"""
        group = QGroupBox("جستجو و فیلتر")
        layout = QHBoxLayout()

        # فیلد جستجو
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس نام، کدملی، تلفن...")
        self.search_input.textChanged.connect(self.on_search_changed)
        layout.addWidget(QLabel("جستجو:"))
        layout.addWidget(self.search_input)

        # نوع جستجو
        self.search_type = QComboBox()
        self.search_type.addItems(["همه", "نام", "کدملی", "تلفن", "پاسپورت"])
        layout.addWidget(QLabel("نوع جستجو:"))
        layout.addWidget(self.search_type)

        # فیلتر وضعیت
        self.status_filter = QComboBox()
        self.status_filter.addItems(["همه", "تأیید شده", "ورود", "خروج", "لغو شده"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(QLabel("وضعیت:"))
        layout.addWidget(self.status_filter)

        # دکمه بازنشانی
        btn_reset = QPushButton("بازنشانی فیلترها")
        btn_reset.clicked.connect(self.reset_filters)
        layout.addWidget(btn_reset)

        group.setLayout(layout)
        return group

    def create_guest_table(self):
        """ایجاد جدول نمایش مهمانان"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "ID", "نام کامل", "کدملی", "تلفن", "تاریخ ورود",
            "تاریخ خروج", "وضعیت", "اتاق"
        ])

        # تنظیمات جدول
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.doubleClicked.connect(self.on_guest_double_click)
        table.clicked.connect(self.on_guest_clicked)

        # تنظیم سایز ستون‌ها
        header = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # نام کامل
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # کدملی
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # تلفن

        return table

    def create_action_group(self):
        """ایجاد نوار عملیات"""
        group = QGroupBox("عملیات")
        layout = QHBoxLayout()

        # دکمه‌های عملیاتی
        self.btn_view_details = QPushButton("مشاهده جزئیات")
        self.btn_view_details.clicked.connect(self.view_guest_details)
        self.btn_view_details.setEnabled(False)

        self.btn_check_in = QPushButton("ثبت ورود")
        self.btn_check_in.clicked.connect(self.check_in_guest)
        self.btn_check_in.setEnabled(False)

        self.btn_check_out = QPushButton("ثبت خروج")
        self.btn_check_out.clicked.connect(self.check_out_guest)
        self.btn_check_out.setEnabled(False)

        self.btn_refresh = QPushButton("بروزرسانی")
        self.btn_refresh.clicked.connect(self.load_guests)

        # افزودن دکمه‌ها به layout
        layout.addWidget(self.btn_view_details)
        layout.addWidget(self.btn_check_in)
        layout.addWidget(self.btn_check_out)
        layout.addWidget(self.btn_refresh)
        layout.addStretch()

        # آمار
        self.stats_label = QLabel("تعداد مهمانان: 0")
        layout.addWidget(self.stats_label)

        group.setLayout(layout)
        return group

    def load_guests(self):
        """بارگذاری لیست مهمانان"""
        try:
            # دریافت داده از سرویس
            result = GuestService.search_guests("", "name")

            if result['success']:
                self.current_guests = result['guests']
                self.populate_table(self.current_guests)
                self.update_stats(len(self.current_guests))
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری مهمانان: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری مهمانان: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری مهمانان: {str(e)}")

    def populate_table(self, guests):
        """پر کردن جدول با داده مهمانان"""
        self.guest_table.setRowCount(len(guests))

        for row, guest in enumerate(guests):
            # ID
            self.guest_table.setItem(row, 0, QTableWidgetItem(str(guest['id'])))

            # نام کامل
            self.guest_table.setItem(row, 1, QTableWidgetItem(guest['full_name']))

            # کدملی
            national_id = guest.get('national_id', '')
            self.guest_table.setItem(row, 2, QTableWidgetItem(national_id))

            # تلفن
            phone = guest.get('phone', '')
            self.guest_table.setItem(row, 3, QTableWidgetItem(phone))

            # تاریخ ورود (نمایشی)
            self.guest_table.setItem(row, 4, QTableWidgetItem("--"))

            # تاریخ خروج (نمایشی)
            self.guest_table.setItem(row, 5, QTableWidgetItem("--"))

            # وضعیت
            status_item = QTableWidgetItem("تأیید شده")
            self.set_status_color(status_item, guest.get('vip_status', False))
            self.guest_table.setItem(row, 6, status_item)

            # اتاق
            self.guest_table.setItem(row, 7, QTableWidgetItem("--"))

        # پنهان کردن ستون ID
        self.guest_table.setColumnHidden(0, True)

    def set_status_color(self, item, is_vip):
        """تعیین رنگ وضعیت بر اساس VIP بودن"""
        if is_vip:
            item.setBackground(QBrush(QColor(255, 255, 200)))  # زرد برای VIP
            item.setForeground(QBrush(QColor(139, 0, 0)))  # قرمز تیره

    def on_search_changed(self, text):
        """هنگام تغییر متن جستجو"""
        self.apply_filters()

    def apply_filters(self):
        """اعمال فیلترهای جستجو"""
        search_text = self.search_input.text().strip()
        status_filter = self.status_filter.currentText()

        filtered_guests = self.current_guests

        # فیلتر بر اساس متن جستجو
        if search_text:
            search_type = self.search_type.currentText()
            if search_type == "همه":
                filtered_guests = [
                    g for g in filtered_guests
                    if search_text.lower() in g['full_name'].lower() or
                       search_text in g.get('national_id', '') or
                       search_text in g.get('phone', '')
                ]
            elif search_type == "نام":
                filtered_guests = [
                    g for g in filtered_guests
                    if search_text.lower() in g['full_name'].lower()
                ]
            elif search_type == "کدملی":
                filtered_guests = [
                    g for g in filtered_guests
                    if search_text in g.get('national_id', '')
                ]
            elif search_type == "تلفن":
                filtered_guests = [
                    g for g in filtered_guests
                    if search_text in g.get('phone', '')
                ]

        # فیلتر بر اساس وضعیت
        if status_filter != "همه":
            # این بخش نیاز به اطلاعات وضعیت از سرویس دارد
            pass

        self.populate_table(filtered_guests)
        self.update_stats(len(filtered_guests))

    def reset_filters(self):
        """بازنشانی تمام فیلترها"""
        self.search_input.clear()
        self.search_type.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.load_guests()

    def on_guest_clicked(self, index):
        """هنگام کلیک روی مهمان"""
        row = index.row()
        if 0 <= row < self.guest_table.rowCount():
            guest_id = int(self.guest_table.item(row, 0).text())
            self.selected_guest_id = guest_id
            self.update_action_buttons(True)

    def on_guest_double_click(self, index):
        """هنگام دابل کلیک روی مهمان"""
        row = index.row()
        if 0 <= row < self.guest_table.rowCount():
            guest_id = int(self.guest_table.item(row, 0).text())
            self.guest_selected.emit(guest_id)

    def update_action_buttons(self, enabled):
        """به‌روزرسانی وضعیت دکمه‌های عملیاتی"""
        self.btn_view_details.setEnabled(enabled)
        self.btn_check_in.setEnabled(enabled)
        self.btn_check_out.setEnabled(enabled)

    def update_stats(self, count):
        """به‌روزرسانی آمار"""
        self.stats_label.setText(f"تعداد مهمانان: {count}")

    def view_guest_details(self):
        """مشاهده جزئیات مهمان انتخاب شده"""
        if self.selected_guest_id:
            self.guest_selected.emit(self.selected_guest_id)

    def check_in_guest(self):
        """ثبت ورود مهمان انتخاب شده"""
        if self.selected_guest_id:
            self.check_in_requested.emit(self.selected_guest_id)

    def check_out_guest(self):
        """ثبت خروج مهمان انتخاب شده"""
        if self.selected_guest_id:
            self.check_out_requested.emit(self.selected_guest_id)
