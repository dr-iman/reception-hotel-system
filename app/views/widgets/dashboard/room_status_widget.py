# app/views/widgets/dashboard/room_status_widget.py
"""
ویجت نمایش وضعیت لحظه‌ای اتاق‌ها
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QGroupBox, QScrollArea,
                            QFrame, QComboBox)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QColor, QPalette

from app.services.reception.room_service import RoomService

logger = logging.getLogger(__name__)

class RoomStatusWidget(QWidget):
    """ویجت نمایش وضعیت اتاق‌ها"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rooms_data = []
        self.init_ui()
        self.load_room_status()

        # تایمر برای به‌روزرسانی خودکار
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_room_status)
        self.refresh_timer.start(30000)  # هر 30 ثانیه

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # هدر و فیلترها
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # نمایش اتاق‌ها
        self.rooms_container = self.create_rooms_container()
        main_layout.addWidget(self.rooms_container)

        self.setLayout(main_layout)

    def create_header(self):
        """ایجاد هدر و فیلترها"""
        layout = QHBoxLayout()

        # عنوان
        title_label = QLabel("وضعیت اتاق‌ها")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title_label)

        layout.addStretch()

        # فیلتر طبقه
        self.floor_filter = QComboBox()
        self.floor_filter.addItems(["همه طبقات", "طبقه 1", "طبقه 2", "طبقه 3", "طبقه 4", "طبقه 5"])
        self.floor_filter.currentTextChanged.connect(self.apply_filters)

        layout.addWidget(QLabel("طبقه:"))
        layout.addWidget(self.floor_filter)

        # فیلتر وضعیت
        self.status_filter = QComboBox()
        self.status_filter.addItems(["همه وضعیت‌ها", "خالی", "اشغال", "نظافت", "تعمیرات"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)

        layout.addWidget(QLabel("وضعیت:"))
        layout.addWidget(self.status_filter)

        # دکمه بروزرسانی
        btn_refresh = QPushButton("بروزرسانی")
        btn_refresh.clicked.connect(self.load_room_status)
        layout.addWidget(btn_refresh)

        return layout

    def create_rooms_container(self):
        """ایجاد کانتینر نمایش اتاق‌ها"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.rooms_widget = QWidget()
        self.rooms_layout = QGridLayout()
        self.rooms_widget.setLayout(self.rooms_layout)

        scroll_area.setWidget(self.rooms_widget)
        return scroll_area

    def load_room_status(self):
        """بارگذاری وضعیت اتاق‌ها"""
        try:
            result = RoomService.get_room_status()

            if result['success']:
                self.rooms_data = result['rooms']
                self.display_rooms(self.rooms_data)
            else:
                logger.error(f"خطا در بارگذاری وضعیت اتاق‌ها: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری وضعیت اتاق‌ها: {e}")

    def display_rooms(self, rooms):
        """نمایش اتاق‌ها در گرید"""
        # پاک کردن layout فعلی
        for i in reversed(range(self.rooms_layout.count())):
            self.rooms_layout.itemAt(i).widget().setParent(None)

        # نمایش اتاق‌ها
        row, col = 0, 0
        max_cols = 6  # حداکثر تعداد ستون

        for room in rooms:
            room_widget = self.create_room_widget(room)
            self.rooms_layout.addWidget(room_widget, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

    def create_room_widget(self, room_data):
        """ایجاد ویجت نمایش یک اتاق"""
        room_frame = QFrame()
        room_frame.setFrameStyle(QFrame.Box)
        room_frame.setLineWidth(1)
        room_frame.setMinimumSize(120, 100)

        layout = QVBoxLayout()

        # شماره اتاق
        room_number = QLabel(room_data['room_number'])
        room_number.setAlignment(Qt.AlignCenter)
        room_number.setStyleSheet("font-size: 16px; font-weight: bold;")

        # نوع اتاق
        room_type = QLabel(room_data['room_type'])
        room_type.setAlignment(Qt.AlignCenter)
        room_type.setStyleSheet("font-size: 12px; color: #666;")

        # وضعیت
        status = QLabel(self.get_status_text(room_data['current_status']))
        status.setAlignment(Qt.AlignCenter)
        status.setStyleSheet(self.get_status_style(room_data['current_status']))

        # مهمان فعلی (اگر وجود دارد)
        guest_info = ""
        if room_data['current_guest']:
            guest = room_data['current_guest']
            guest_name = guest['full_name'].split()[0]  # فقط نام کوچک
            guest_info = f"👤 {guest_name}"

        guest_label = QLabel(guest_info)
        guest_label.setAlignment(Qt.AlignCenter)
        guest_label.setStyleSheet("font-size: 10px; color: #333;")

        layout.addWidget(room_number)
        layout.addWidget(room_type)
        layout.addWidget(status)
        layout.addWidget(guest_label)

        room_frame.setLayout(layout)

        # تنظیم رنگ背景 بر اساس وضعیت
        room_frame.setStyleSheet(self.get_room_background_style(room_data['current_status']))

        return room_frame

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

    def get_status_style(self, status):
        """استایل متن وضعیت"""
        color_map = {
            'vacant': 'color: green; font-weight: bold;',
            'occupied': 'color: red; font-weight: bold;',
            'cleaning': 'color: orange; font-weight: bold;',
            'maintenance': 'color: purple; font-weight: bold;',
            'out_of_order': 'color: gray; font-weight: bold;',
            'inspection': 'color: blue; font-weight: bold;'
        }
        return color_map.get(status, '')

    def get_room_background_style(self, status):
        """استایل background اتاق"""
        color_map = {
            'vacant': 'background-color: #e8f5e8;',  # سبز بسیار روشن
            'occupied': 'background-color: #ffe8e8;',  # قرمز بسیار روشن
            'cleaning': 'background-color: #fff4e8;',  # نارنجی بسیار روشن
            'maintenance': 'background-color: #f0e8ff;',  # بنفش بسیار روشن
            'out_of_order': 'background-color: #f0f0f0;',  # خاکستری
            'inspection': 'background-color: #e8f4ff;'  # آبی بسیار روشن
        }
        return color_map.get(status, '') + 'border: 1px solid #ccc; border-radius: 5px; padding: 5px;'

    def apply_filters(self):
        """اعمال فیلترهای انتخاب شده"""
        floor_filter = self.floor_filter.currentText()
        status_filter = self.status_filter.currentText()

        filtered_rooms = self.rooms_data

        # فیلتر طبقه
        if floor_filter != "همه طبقات":
            floor_num = int(floor_filter.split()[1])  # استخراج شماره طبقه
            filtered_rooms = [r for r in filtered_rooms if r['floor'] == floor_num]

        # فیلتر وضعیت
        if status_filter != "همه وضعیت‌ها":
            status_map = {
                "خالی": "vacant",
                "اشغال": "occupied",
                "نظافت": "cleaning",
                "تعمیرات": "maintenance"
            }
            target_status = status_map.get(status_filter)
            if target_status:
                filtered_rooms = [r for r in filtered_rooms if r['current_status'] == target_status]

        self.display_rooms(filtered_rooms)
