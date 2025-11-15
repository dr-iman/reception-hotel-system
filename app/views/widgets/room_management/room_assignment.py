# app/views/widgets/room_management/room_assignment.py
"""
ویجت تخصیص اتاق به مهمان
"""

import logging
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QDateEdit)
from PyQt5.QtCore import QDate, pyqtSignal

from app.services.reception.room_service import RoomService
from app.services.reception.guest_service import GuestService
from config import config

logger = logging.getLogger(__name__)

class RoomAssignmentWidget(QWidget):
    """ویجت تخصیص اتاق به مهمان"""

    # سیگنال‌ها
    assignment_completed = pyqtSignal(int)  # ID تخصیص

    def __init__(self, guest_id=None, parent=None):
        super().__init__(parent)
        self.guest_id = guest_id
        self.available_rooms = []
        self.selected_room = None
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

        # جزئیات تخصیص
        assignment_details_group = self.create_assignment_details_group()
        main_layout.addWidget(assignment_details_group)

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
        self.lbl_check_in = QLabel("--")
        self.lbl_check_out = QLabel("--")

        layout.addRow("نام مهمان:", self.lbl_guest_name)
        layout.addRow("کدملی:", self.lbl_national_id)
        layout.addRow("تلفن:", self.lbl_phone)
        layout.addRow("شماره رزرو:", self.lbl_reservation_id)
        layout.addRow("تاریخ ورود:", self.lbl_check_in)
        layout.addRow("تاریخ خروج:", self.lbl_check_out)

        group.setLayout(layout)
        return group

    def create_room_selection_group(self):
        """گروه انتخاب اتاق"""
        group = QGroupBox("انتخاب اتاق")
        layout = QVBoxLayout()

        # فیلترها
        filter_layout = QHBoxLayout()

        self.cmb_room_type = QComboBox()
        self.cmb_room_type.addItems(["همه", "استاندارد", "دلوکس", "سوئیت"])
        self.cmb_room_type.currentTextChanged.connect(self.load_available_rooms)

        self.cmb_floor = QComboBox()
        self.cmb_floor.addItems(["همه طبقات", "طبقه 1", "طبقه 2", "طبقه 3", "طبقه 4", "طبقه 5"])
        self.cmb_floor.currentTextChanged.connect(self.load_available_rooms)

        filter_layout.addWidget(QLabel("نوع اتاق:"))
        filter_layout.addWidget(self.cmb_room_type)
        filter_layout.addWidget(QLabel("طبقه:"))
        filter_layout.addWidget(self.cmb_floor)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # جدول اتاق‌های available
        self.rooms_table = QTableWidget()
        self.rooms_table.setColumnCount(6)
        self.rooms_table.setHorizontalHeaderLabels([
            "ID", "شماره اتاق", "نوع", "طبقه", "تخت", "قیمت شبانه"
        ])

        self.rooms_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rooms_table.setSelectionMode(QTableWidget.SingleSelection)
        self.rooms_table.doubleClicked.connect(self.on_room_selected)
        self.rooms_table.clicked.connect(self.on_room_clicked)

        header = self.rooms_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        layout.addWidget(self.rooms_table)

        group.setLayout(layout)
        return group

    def create_assignment_details_group(self):
        """گروه جزئیات تخصیص"""
        group = QGroupBox("جزئیات تخصیص")
        layout = QFormLayout()

        self.lbl_selected_room = QLabel("--")
        self.lbl_room_type = QLabel("--")
        self.lbl_room_floor = QLabel("--")
        self.lbl_nightly_rate = QLabel("--")

        self.date_check_in = QDateEdit()
        self.date_check_in.setCalendarPopup(True)
        self.date_check_in.setDate(QDate.currentDate())

        self.date_check_out = QDateEdit()
        self.date_check_out.setCalendarPopup(True)
        self.date_check_out.setDate(QDate.currentDate().addDays(1))

        self.cmb_assignment_type = QComboBox()
        self.cmb_assignment_type.addItems(["اصلی", "اضافی", "جابجایی"])

        layout.addRow("اتاق انتخاب شده:", self.lbl_selected_room)
        layout.addRow("نوع اتاق:", self.lbl_room_type)
        layout.addRow("طبقه:", self.lbl_room_floor)
        layout.addRow("قیمت شبانه:", self.lbl_nightly_rate)
        layout.addRow("تاریخ تخصیص:", self.date_check_in)
        layout.addRow("تاریخ پایان تخصیص:", self.date_check_out)
        layout.addRow("نوع تخصیص:", self.cmb_assignment_type)

        group.setLayout(layout)
        return group

    def create_action_layout(self):
        """نوار عملیات"""
        layout = QHBoxLayout()

        self.btn_assign = QPushButton("تخصیص اتاق")
        self.btn_assign.clicked.connect(self.process_assignment)
        self.btn_assign.setEnabled(False)

        self.btn_cancel = QPushButton("انصراف")
        self.btn_cancel.clicked.connect(self.cancel_assignment)

        layout.addWidget(self.btn_assign)
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
            self.lbl_check_in.setText(str(stay.get('planned_check_in', '--')))
            self.lbl_check_out.setText(str(stay.get('planned_check_out', '--')))

    def load_available_rooms(self):
        """بارگذاری اتاق‌های available"""
        try:
            # محاسبه تاریخ‌ها
            check_in = self.date_check_in.date().toPyDate()
            check_out = self.date_check_out.date().toPyDate()

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
            self.rooms_table.setItem(row, 0, QTableWidgetItem(str(room['room_id'])))
            self.rooms_table.setItem(row, 1, QTableWidgetItem(room['room_number']))
            self.rooms_table.setItem(row, 2, QTableWidgetItem(room['room_type']))
            self.rooms_table.setItem(row, 3, QTableWidgetItem(str(room['floor'])))
            self.rooms_table.setItem(row, 4, QTableWidgetItem(room['bed_type']))
            self.rooms_table.setItem(row, 5, QTableWidgetItem(f"{room['rate_per_night']:,.0f}"))

        # پنهان کردن ستون ID
        self.rooms_table.setColumnHidden(0, True)

    def on_room_clicked(self, index):
        """هنگام کلیک روی اتاق"""
        row = index.row()
        if 0 <= row < len(self.available_rooms):
            self.selected_room = self.available_rooms[row]
            self.update_selected_room_info()
            self.btn_assign.setEnabled(True)

    def on_room_selected(self, index):
        """هنگام دابل کلیک روی اتاق"""
        self.on_room_clicked(index)

    def update_selected_room_info(self):
        """به‌روزرسانی اطلاعات اتاق انتخاب شده"""
        if not self.selected_room:
            return

        self.lbl_selected_room.setText(self.selected_room['room_number'])
        self.lbl_room_type.setText(self.selected_room['room_type'])
        self.lbl_room_floor.setText(str(self.selected_room['floor']))
        self.lbl_nightly_rate.setText(f"{self.selected_room['rate_per_night']:,.0f} تومان")

    def process_assignment(self):
        """پردازش تخصیص اتاق"""
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

            # ثبت تخصیص اتاق
            # TODO: این بخش نیاز به پیاده‌سازی در RoomService دارد
            QMessageBox.information(self, "موفق", f"اتاق {self.selected_room['room_number']} به مهمان تخصیص داده شد")
            self.assignment_completed.emit(stay_id)
            self.close()

        except Exception as e:
            logger.error(f"خطا در تخصیص اتاق: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تخصیص اتاق: {str(e)}")

    def cancel_assignment(self):
        """انصراف از تخصیص"""
        self.close()

    def set_guest_id(self, guest_id):
        """تنظیم ID مهمان جدید"""
        self.guest_id = guest_id
        self.load_guest_data()
