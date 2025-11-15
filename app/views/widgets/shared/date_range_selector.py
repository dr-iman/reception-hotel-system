# app/views/widgets/shared/date_range_selector.py
"""
انتخابگر بازه تاریخ
"""

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLabel, QDateEdit,
                            QComboBox, QPushButton)
from PyQt5.QtCore import QDate, pyqtSignal

class DateRangeSelector(QWidget):
    """
    ویجت انتخاب بازه تاریخ با پیش‌تعریف‌ها
    """

    date_range_changed = pyqtSignal(QDate, QDate)  # تاریخ شروع, تاریخ پایان

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_presets()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # لیست پیش‌تعریف‌ها
        layout.addWidget(QLabel("بازه:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(120)
        self.preset_combo.currentIndexChanged.connect(self.on_preset_changed)
        layout.addWidget(self.preset_combo)

        # تاریخ شروع
        layout.addWidget(QLabel("از:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.dateChanged.connect(self.on_date_changed)
        layout.addWidget(self.start_date)

        # تاریخ پایان
        layout.addWidget(QLabel("تا:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.on_date_changed)
        layout.addWidget(self.end_date)

        # دکمه اعمال
        self.apply_btn = QPushButton("اعمال")
        self.apply_btn.clicked.connect(self.apply_dates)
        layout.addWidget(self.apply_btn)

        layout.addStretch()

    def setup_presets(self):
        """تنظیم پیش‌تعریف‌ها"""
        presets = [
            ("امروز", 0),
            ("دیروز", 1),
            ("۷ روز گذشته", 7),
            ("۳۰ روز گذشته", 30),
            ("این ماه", "current_month"),
            ("ماه قبل", "last_month"),
            ("امسال", "current_year"),
            ("همه تاریخ", "all")
        ]

        for name, value in presets:
            self.preset_combo.addItem(name, value)

    def on_preset_changed(self, index):
        """هنگام تغییر پیش‌تعریف"""
        preset_value = self.preset_combo.currentData()
        today = QDate.currentDate()

        if preset_value == 0:  # امروز
            self.start_date.setDate(today)
            self.end_date.setDate(today)
        elif preset_value == 1:  # دیروز
            yesterday = today.addDays(-1)
            self.start_date.setDate(yesterday)
            self.end_date.setDate(yesterday)
        elif preset_value == 7:  # ۷ روز گذشته
            self.start_date.setDate(today.addDays(-7))
            self.end_date.setDate(today)
        elif preset_value == 30:  # ۳۰ روز گذشته
            self.start_date.setDate(today.addDays(-30))
            self.end_date.setDate(today)
        elif preset_value == "current_month":  # این ماه
            first_day = QDate(today.year(), today.month(), 1)
            self.start_date.setDate(first_day)
            self.end_date.setDate(today)
        elif preset_value == "last_month":  # ماه قبل
            first_day_last_month = today.addMonths(-1)
            first_day_last_month = QDate(first_day_last_month.year(), first_day_last_month.month(), 1)
            last_day_last_month = QDate(today.year(), today.month(), 1).addDays(-1)
            self.start_date.setDate(first_day_last_month)
            self.end_date.setDate(last_day_last_month)
        elif preset_value == "current_year":  # امسال
            first_day = QDate(today.year(), 1, 1)
            self.start_date.setDate(first_day)
            self.end_date.setDate(today)
        elif preset_value == "all":  # همه تاریخ
            self.start_date.setDate(QDate(2000, 1, 1))
            self.end_date.setDate(today)

        self.apply_dates()

    def on_date_changed(self):
        """هنگام تغییر تاریخ"""
        # وقتی تاریخ دستی تغییر می‌کند، پیش‌تعریف را به "سفارشی" تغییر می‌دهیم
        self.preset_combo.setCurrentIndex(-1)

    def apply_dates(self):
        """اعمال تاریخ‌ها"""
        start_date = self.start_date.date().toPyDate()
        end_date = self.end_date.date().toPyDate()
        self.date_range_changed.emit(self.start_date.date(), self.end_date.date())

    def get_date_range(self) -> tuple:
        """دریافت بازه تاریخ"""
        return (
            self.start_date.date().toPyDate(),
            self.end_date.date().toPyDate()
        )

    def set_date_range(self, start_date, end_date):
        """تنظیم بازه تاریخ"""
        self.start_date.setDate(QDate.fromString(start_date.toString("yyyy-MM-dd"), "yyyy-MM-dd"))
        self.end_date.setDate(QDate.fromString(end_date.toString("yyyy-MM-dd"), "yyyy-MM-dd"))
        self.apply_dates()
