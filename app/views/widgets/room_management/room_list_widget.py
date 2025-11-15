# app/views/widgets/room_management/room_list_widget.py
"""
ویجت لیست اتاق‌ها و مدیریت وضعیت
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                            QTableWidgetItem, QPushButton, QComboBox, QLabel,
                            QMessageBox, QHeaderView, QGroupBox, QLineEdit,
                            QSplitter, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QBrush, QFont

from app.services.reception.room_service import RoomService
from app.services.reception.housekeeping_service import HousekeepingService
from config import config

logger = logging.getLogger(__name__)

class RoomListWidget(QWidget):
    """ویجت لیست و مدیریت اتاق‌ها"""

    # سیگنال‌ها
    room_selected = pyqtSignal(int)  # ارسال ID اتاق انتخاب شده
    status_changed = pyqtSignal()    # تغییر وضعیت اتاق

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rooms_data = []
        self.selected_room_id = None
        self.init_ui()
        self.load_rooms()

        # تایمر برای به‌روزرسانی خودکار
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.load_rooms)
        self.auto_refresh_timer.start(30000)  # هر 30 ثانیه

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # نوار جستجو و فیلتر
        filter_group = self.create_filter_group()
        main_layout.addWidget(filter_group)

        # ایجاد اسپلیتر برای تقسیم صفحه
        splitter = QSplitter(Qt.Horizontal)

        # جدول اتاق‌ها (سمت چپ)
        self.rooms_table = self.create_rooms_table()
        splitter.addWidget(self.rooms_table)

        # پنل مدیریت (سمت راست)
        self.management_panel = self.create_management_panel()
        splitter.addWidget(self.management_panel)

        # تنظیم سایز اولیه
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def create_filter_group(self):
        """ایجاد گروه فیلترها"""
        group = QGroupBox("فیلتر و جستجو")
        layout = QHBoxLayout()

        # فیلد جستجو
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو بر اساس شماره اتاق...")
        self.search_input.textChanged.connect(self.apply_filters)
        layout.addWidget(QLabel("جستجو:"))
        layout.addWidget(self.search_input)

        # فیلتر طبقه
        self.floor_filter = QComboBox()
        self.floor_filter.addItems(["همه طبقات", "طبقه 1", "طبقه 2", "طبقه 3", "طبقه 4", "طبقه 5"])
        self.floor_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(QLabel("طبقه:"))
        layout.addWidget(self.floor_filter)

        # فیلتر وضعیت
        self.status_filter = QComboBox()
        self.status_filter.addItems(["همه وضعیت‌ها", "خالی", "اشغال", "نظافت", "تعمیرات", "غیرقابل استفاده"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(QLabel("وضعیت:"))
        layout.addWidget(self.status_filter)

        # فیلتر نوع اتاق
        self.type_filter = QComboBox()
        self.type_filter.addItems(["همه انواع", "استاندارد", "دلوکس", "سوئیت"])
        self.type_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(QLabel("نوع اتاق:"))
        layout.addWidget(self.type_filter)

        # دکمه بازنشانی
        btn_reset = QPushButton("بازنشانی فیلترها")
        btn_reset.clicked.connect(self.reset_filters)
        layout.addWidget(btn_reset)

        group.setLayout(layout)
        return group

    def create_rooms_table(self):
        """ایجاد جدول اتاق‌ها"""
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "ID", "شماره اتاق", "طبقه", "نوع", "وضعیت", "مهمان فعلی",
            "تخت", "آخرین بروزرسانی"
        ])

        # تنظیمات جدول
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.doubleClicked.connect(self.on_room_double_click)
        table.clicked.connect(self.on_room_clicked)

        # تنظیم سایز ستون‌ها
        header = table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # شماره اتاق
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # وضعیت
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # مهمان فعلی

        return table

    def create_management_panel(self):
        """ایجاد پنل مدیریت"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Box)
        layout = QVBoxLayout()

        # اطلاعات اتاق انتخاب شده
        self.room_info_group = self.create_room_info_group()
        layout.addWidget(self.room_info_group)

        # تغییر وضعیت
        self.status_change_group = self.create_status_change_group()
        layout.addWidget(self.status_change_group)

        # عملیات سریع
        self.quick_actions_group = self.create_quick_actions_group()
        layout.addWidget(self.quick_actions_group)

        layout.addStretch()
        panel.setLayout(layout)
        return panel

    def create_room_info_group(self):
        """گروه اطلاعات اتاق"""
        group = QGroupBox("اطلاعات اتاق")
        layout = QVBoxLayout()

        self.lbl_room_number = QLabel("--")
        self.lbl_room_number.setFont(QFont("Arial", 16, QFont.Bold))

        self.lbl_room_type = QLabel("--")
        self.lbl_room_floor = QLabel("--")
        self.lbl_current_status = QLabel("--")
        self.lbl_current_guest = QLabel("--")
        self.lbl_bed_type = QLabel("--")

        info_layout = QHBoxLayout()
        left_info = QVBoxLayout()
        right_info = QVBoxLayout()

        left_info.addWidget(QLabel("شماره اتاق:"))
        left_info.addWidget(QLabel("نوع:"))
        left_info.addWidget(QLabel("طبقه:"))
        left_info.addWidget(QLabel("وضعیت:"))

        right_info.addWidget(self.lbl_room_number)
        right_info.addWidget(self.lbl_room_type)
        right_info.addWidget(self.lbl_room_floor)
        right_info.addWidget(self.lbl_current_status)

        info_layout.addLayout(left_info)
        info_layout.addLayout(right_info)

        layout.addLayout(info_layout)
        layout.addWidget(QLabel("مهمان فعلی:"))
        layout.addWidget(self.lbl_current_guest)
        layout.addWidget(QLabel("نوع تخت:"))
        layout.addWidget(self.lbl_bed_type)

        group.setLayout(layout)
        return group

    def create_status_change_group(self):
        """گروه تغییر وضعیت"""
        group = QGroupBox("تغییر وضعیت")
        layout = QVBoxLayout()

        self.cmb_new_status = QComboBox()
        self.cmb_new_status.addItems(["خالی", "اشغال", "نظافت", "تعمیرات", "غیرقابل استفاده", "بازرسی"])

        self.txt_status_reason = QLineEdit()
        self.txt_status_reason.setPlaceholderText("دلیل تغییر وضعیت...")

        self.btn_change_status = QPushButton("اعمال تغییر وضعیت")
        self.btn_change_status.clicked.connect(self.change_room_status)
        self.btn_change_status.setEnabled(False)

        layout.addWidget(QLabel("وضعیت جدید:"))
        layout.addWidget(self.cmb_new_status)
        layout.addWidget(QLabel("دلیل تغییر:"))
        layout.addWidget(self.txt_status_reason)
        layout.addWidget(self.btn_change_status)

        group.setLayout(layout)
        return group

    def create_quick_actions_group(self):
        """گروه عملیات سریع"""
        group = QGroupBox("عملیات سریع")
        layout = QVBoxLayout()

        self.btn_create_cleaning = QPushButton("ایجاد وظیفه نظافت")
        self.btn_create_cleaning.clicked.connect(self.create_cleaning_task)
        self.btn_create_cleaning.setEnabled(False)

        self.btn_assign_room = QPushButton("تخصیص اتاق")
        self.btn_assign_room.clicked.connect(self.assign_room)
        self.btn_assign_room.setEnabled(False)

        self.btn_room_details = QPushButton("مشاهده جزئیات کامل")
        self.btn_room_details.clicked.connect(self.show_room_details)
        self.btn_room_details.setEnabled(False)

        layout.addWidget(self.btn_create_cleaning)
        layout.addWidget(self.btn_assign_room)
        layout.addWidget(self.btn_room_details)

        group.setLayout(layout)
        return group

    def load_rooms(self):
        """بارگذاری لیست اتاق‌ها"""
        try:
            result = RoomService.get_room_status()

            if result['success']:
                self.rooms_data = result['rooms']
                self.populate_table(self.rooms_data)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری اتاق‌ها: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری اتاق‌ها: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری اتاق‌ها: {str(e)}")

    def populate_table(self, rooms):
        """پر کردن جدول با داده اتاق‌ها"""
        self.rooms_table.setRowCount(len(rooms))

        for row, room in enumerate(rooms):
            # ID
            self.rooms_table.setItem(row, 0, QTableWidgetItem(str(room['room_id'])))

            # شماره اتاق
            self.rooms_table.setItem(row, 1, QTableWidgetItem(room['room_number']))

            # طبقه
            self.rooms_table.setItem(row, 2, QTableWidgetItem(str(room['floor'])))

            # نوع اتاق
            self.rooms_table.setItem(row, 3, QTableWidgetItem(room['room_type']))

            # وضعیت
            status_item = QTableWidgetItem(self.get_status_text(room['current_status']))
            self.set_status_color(status_item, room['current_status'])
            self.rooms_table.setItem(row, 4, status_item)

            # مهمان فعلی
            guest_name = "--"
            if room['current_guest']:
                guest_name = room['current_guest']['full_name']
            self.rooms_table.setItem(row, 5, QTableWidgetItem(guest_name))

            # نوع تخت
            bed_type = room.get('bed_type', '--')
            self.rooms_table.setItem(row, 6, QTableWidgetItem(bed_type))

            # آخرین بروزرسانی
            last_update = room.get('last_status_change', '--')
            self.rooms_table.setItem(row, 7, QTableWidgetItem(str(last_update)))

        # پنهان کردن ستون ID
        self.rooms_table.setColumnHidden(0, True)

    def get_status_text(self, status):
        """متن وضعیت به فارسی"""
        status_map = {
            'vacant': 'خالی',
            'occupied': 'اشغال',
            'cleaning': 'نظافت',
            'maintenance': 'تعمیرات',
            'out_of_order': 'غیرقابل استفاده',
            'inspection': 'بازرسی'
        }
        return status_map.get(status, status)

    def set_status_color(self, item, status):
        """تعیین رنگ وضعیت"""
        color_map = {
            'vacant': QColor(0, 128, 0),      # سبز
            'occupied': QColor(220, 0, 0),    # قرمز
            'cleaning': QColor(255, 165, 0),  # نارنجی
            'maintenance': QColor(128, 0, 128), # بنفش
            'out_of_order': QColor(128, 128, 128), # خاکستری
            'inspection': QColor(0, 0, 255)   # آبی
        }

        if status in color_map:
            item.setForeground(QBrush(color_map[status]))
            item.setFont(QFont("Arial", 9, QFont.Bold))

    def on_room_clicked(self, index):
        """هنگام کلیک روی اتاق"""
        row = index.row()
        if 0 <= row < self.rooms_table.rowCount():
            room_id = int(self.rooms_table.item(row, 0).text())
            self.selected_room_id = room_id
            self.update_room_info(room_id)
            self.update_action_buttons(True)

    def on_room_double_click(self, index):
        """هنگام دابل کلیک روی اتاق"""
        row = index.row()
        if 0 <= row < self.rooms_table.rowCount():
            room_id = int(self.rooms_table.item(row, 0).text())
            self.room_selected.emit(room_id)

    def update_room_info(self, room_id):
        """به‌روزرسانی اطلاعات اتاق انتخاب شده"""
        room = next((r for r in self.rooms_data if r['room_id'] == room_id), None)
        if not room:
            return

        self.lbl_room_number.setText(room['room_number'])
        self.lbl_room_type.setText(room['room_type'])
        self.lbl_room_floor.setText(str(room['floor']))
        self.lbl_current_status.setText(self.get_status_text(room['current_status']))
        self.lbl_bed_type.setText(room.get('bed_type', '--'))

        # مهمان فعلی
        if room['current_guest']:
            guest = room['current_guest']
            self.lbl_current_guest.setText(f"{guest['full_name']} (اقامت: {guest.get('stay_id', '--')})")
        else:
            self.lbl_current_guest.setText("--")

    def update_action_buttons(self, enabled):
        """به‌روزرسانی وضعیت دکمه‌های عملیاتی"""
        self.btn_change_status.setEnabled(enabled)
        self.btn_create_cleaning.setEnabled(enabled)
        self.btn_assign_room.setEnabled(enabled)
        self.btn_room_details.setEnabled(enabled)

    def apply_filters(self):
        """اعمال فیلترهای جستجو"""
        search_text = self.search_input.text().strip().lower()
        floor_filter = self.floor_filter.currentText()
        status_filter = self.status_filter.currentText()
        type_filter = self.type_filter.currentText()

        filtered_rooms = self.rooms_data

        # فیلتر جستجو
        if search_text:
            filtered_rooms = [
                r for r in filtered_rooms
                if search_text in r['room_number'].lower()
            ]

        # فیلتر طبقه
        if floor_filter != "همه طبقات":
            floor_num = int(floor_filter.split()[1])
            filtered_rooms = [r for r in filtered_rooms if r['floor'] == floor_num]

        # فیلتر وضعیت
        if status_filter != "همه وضعیت‌ها":
            status_map = {
                "خالی": "vacant",
                "اشغال": "occupied",
                "نظافت": "cleaning",
                "تعمیرات": "maintenance",
                "غیرقابل استفاده": "out_of_order"
            }
            target_status = status_map.get(status_filter)
            if target_status:
                filtered_rooms = [r for r in filtered_rooms if r['current_status'] == target_status]

        # فیلتر نوع اتاق
        if type_filter != "همه انواع":
            filtered_rooms = [r for r in filtered_rooms if r['room_type'] == type_filter]

        self.populate_table(filtered_rooms)

    def reset_filters(self):
        """بازنشانی تمام فیلترها"""
        self.search_input.clear()
        self.floor_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.type_filter.setCurrentIndex(0)
        self.load_rooms()

    def change_room_status(self):
        """تغییر وضعیت اتاق"""
        if not self.selected_room_id:
            return

        new_status = self.cmb_new_status.currentText()
        reason = self.txt_status_reason.text().strip()

        if not reason:
            QMessageBox.warning(self, "هشدار", "لطفاً دلیل تغییر وضعیت را وارد کنید")
            return

        try:
            # تبدیل وضعیت فارسی به انگلیسی
            status_map = {
                "خالی": "vacant",
                "اشغال": "occupied",
                "نظافت": "cleaning",
                "تعمیرات": "maintenance",
                "غیرقابل استفاده": "out_of_order",
                "بازرسی": "inspection"
            }

            status_english = status_map.get(new_status)
            if not status_english:
                QMessageBox.warning(self, "خطا", "وضعیت انتخاب شده نامعتبر است")
                return

            # تغییر وضعیت
            result = RoomService.update_room_status(
                room_id=self.selected_room_id,
                new_status=status_english,
                changed_by=1,  # TODO: دریافت از کاربر لاگین شده
                reason=reason
            )

            if result['success']:
                QMessageBox.information(self, "موفق", "وضعیت اتاق با موفقیت تغییر یافت")
                self.txt_status_reason.clear()
                self.load_rooms()
                self.status_changed.emit()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تغییر وضعیت: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در تغییر وضعیت اتاق: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تغییر وضعیت: {str(e)}")

    def create_cleaning_task(self):
        """ایجاد وظیفه نظافت"""
        if not self.selected_room_id:
            return

        try:
            result = HousekeepingService.create_cleaning_task(
                room_id=self.selected_room_id,
                task_type='daily_cleaning',
                priority='medium'
            )

            if result['success']:
                QMessageBox.information(self, "موفق", "وظیفه نظافت با موفقیت ایجاد شد")
            else:
                QMessageBox.warning(self, "خطا", f"خطا در ایجاد وظیفه نظافت: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در ایجاد وظیفه نظافت: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ایجاد وظیفه نظافت: {str(e)}")

    def assign_room(self):
        """تخصیص اتاق"""
        if not self.selected_room_id:
            return

        # TODO: پیاده‌سازی دیالوگ تخصیص اتاق
        QMessageBox.information(self, "تخصیص اتاق", f"تخصیص اتاق {self.selected_room_id} - به زودی")

    def show_room_details(self):
        """نمایش جزئیات کامل اتاق"""
        if self.selected_room_id:
            self.room_selected.emit(self.selected_room_id)
