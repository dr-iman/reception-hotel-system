# app/views/widgets/guest_management/check_in_widget.py
"""
ویجت ثبت ورود مهمان و تخصیص اتاق
"""

import logging
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import pyqtSignal

from app.services.reception.guest_service import GuestService
from app.services.reception.room_service import RoomService

logger = logging.getLogger(__name__)

class CheckInWidget(QWidget):
    """ویجت ثبت ورود مهمان"""

    # سیگنال‌ها
    check_in_completed = pyqtSignal(int)  # ID اقامت

    def __init__(self, guest_id=None, parent=None):
        super().__init__(parent)
        self.guest_id = guest_id
        self.guest_data = None
        self.available_rooms = []
        self.init_ui()
        if guest_id:
            self.load_guest_data()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # اطلاعات مهمان
        guest_info_group = self.create_guest_info_group()
        main_layout.addWidget(guest_info_group)

        # انتخاب اتاق
        room_selection_group = self.create_room_selection_group()
        main_layout.addWidget(room_selection_group)

        # نوار عملیات
        action_layout = self.create_action_layout()
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

    def create_guest_info_group(self):
        """گروه اطلاعات مهمان"""
        group = QGroupBox("اطلاعات مهمان")
        layout = QFormLayout()

        self.lbl_guest_name = QLabel("--")
        self.lbl_national_id = QLabel("--")
        self.lbl_phone = QLabel("--")
        self.lbl_reservation_id = QLabel("--")
        self.lbl_check_in_date = QLabel("--")
        self.lbl_check_out_date = QLabel("--")

        layout.addRow("نام مهمان:", self.lbl_guest_name)
        layout.addRow("کدملی:", self.lbl_national_id)
        layout.addRow("تلفن:", self.lbl_phone)
        layout.addRow("شماره رزرو:", self.lbl_reservation_id)
        layout.addRow("تاریخ ورود:", self.lbl_check_in_date)
        layout.addRow("تاریخ خروج:", self.lbl_check_out_date)

        group.setLayout(layout)
        return group

    def create_room_selection_group(self):
        """گروه انتخاب اتاق"""
        group = QGroupBox("انتخاب اتاق")
        layout = QVBoxLayout()

        # فیلترهای جستجوی اتاق
        filter_layout = QHBoxLayout()

        self.cmb_room_type = QComboBox()
        self.cmb_room_type.addItems(["همه", "استاندارد", "دلوکس", "سوئیت"])
        self.cmb_room_type.currentTextChanged.connect(self.load_available_rooms)

        filter_layout.addWidget(QLabel("نوع اتاق:"))
        filter_layout.addWidget(self.cmb_room_type)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # جدول اتاق‌های available
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(5)
        self.rooms_table.setHorizontalHeaderLabels([
            "شماره اتاق", "نوع", "طبقه", "تخت", "قیمت شبانه"
        ])

        self.rooms_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rooms_table.setSelectionMode(QTableWidget.SingleSelection)
        self.rooms_table.doubleClicked.connect(self.on_room_selected)

        header = self.rooms_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.rooms_table)

        group.setLayout(layout)
        return group

    def create_action_layout(self):
        """نوار عملیات"""
        layout = QHBoxLayout()

        self.btn_check_in = QPushButton("ثبت ورود")
        self.btn_check_in.clicked.connect(self.process_check_in)
        self.btn_check_in.setEnabled(False)

        self.btn_cancel = QPushButton("انصراف")
        self.btn_cancel.clicked.connect(self.cancel_check_in)

        layout.addWidget(self.btn_check_in)
        layout.addWidget(self.btn_cancel)
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
                self.populate_guest_info()
                self.load_available_rooms()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری اطلاعات مهمان: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری اطلاعات مهمان: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اطلاعات: {str(e)}")

    def populate_guest_info(self):
        """پر کردن اطلاعات مهمان"""
        if not self.guest_data:
            return

        self.lbl_guest_name.setText(self.guest_data['full_name'])
        self.lbl_national_id.setText(self.guest_data.get('national_id', '--'))
        self.lbl_phone.setText(self.guest_data.get('phone', '--'))

        # اطلاعات اقامت
        active_stays = self.guest_data.get('active_stays', [])
        if active_stays:
            stay = active_stays[0]
            self.lbl_reservation_id.setText(str(stay.get('stay_id', '--')))
            self.lbl_check_in_date.setText(str(stay.get('planned_check_in', '--')))
            self.lbl_check_out_date.setText(str(stay.get('planned_check_out', '--')))

    def load_available_rooms(self):
        """بارگذاری اتاق‌های available"""
        try:
            # محاسبه تاریخ‌های اقامت
            check_in = datetime.now().date()
            check_out = datetime.now().date()

            # اگر اطلاعات اقامت موجود باشد
            if self.guest_data and self.guest_data.get('active_stays'):
                stay = self.guest_data['active_stays'][0]
                check_in = stay.get('planned_check_in', datetime.now()).date()
                check_out = stay.get('planned_check_out', datetime.now()).date()

            room_type = None
            if self.cmb_room_type.currentText() != "همه":
                room_type = self.cmb_room_type.currentText()

            result = RoomService.get_available_rooms(check_in, check_out, room_type)

            if result['success']:
                self.available_rooms = result['available_rooms']
                self.populate_rooms_table()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری اتاق‌ها: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری اتاق‌ها: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اتاق‌ها: {str(e)}")

    def populate_rooms_table(self):
        """پر کردن جدول اتاق‌ها"""
        self.rooms_table.setRowCount(len(self.available_rooms))

        for row, room in enumerate(self.available_rooms):
            self.rooms_table.setItem(row, 0, QTableWidgetItem(room['room_number']))
            self.rooms_table.setItem(row, 1, QTableWidgetItem(room['room_type']))
            self.rooms_table.setItem(row, 2, QTableWidgetItem(str(room['floor'])))
            self.rooms_table.setItem(row, 3, QTableWidgetItem(room['bed_type']))
            self.rooms_table.setItem(row, 4, QTableWidgetItem(f"{room['rate_per_night']:,.0f}"))

    def on_room_selected(self, index):
        """هنگام انتخاب اتاق"""
        row = index.row()
        if 0 <= row < len(self.available_rooms):
            self.selected_room = self.available_rooms[row]
            self.btn_check_in.setEnabled(True)

    def process_check_in(self):
        """پردازش ثبت ورود"""
        if not self.selected_room or not self.guest_id:
            return

        try:
            # پیدا کردن اقامت فعال
            active_stays = self.guest_data.get('active_stays', [])
            if not active_stays:
                QMessageBox.warning(self, "خطا", "هیچ اقامت فعالی برای این مهمان یافت نشد")
                return

            stay_id = active_stays[0]['stay_id']
            room_id = self.selected_room['room_id']

            # ثبت ورود
            result = GuestService.check_in_guest(stay_id, room_id)

            if result['success']:
                QMessageBox.information(self, "موفق", "ورود مهمان با موفقیت ثبت شد")
                self.check_in_completed.emit(stay_id)
                self.close()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در ثبت ورود: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در ثبت ورود: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ثبت ورود: {str(e)}")

    def cancel_check_in(self):
        """انصراف از ثبت ورود"""
        self.close()

    def set_guest_id(self, guest_id):
        """تنظیم ID مهمان جدید"""
        self.guest_id = guest_id
        self.load_guest_data()
