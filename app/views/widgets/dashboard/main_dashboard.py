# app/views/widgets/dashboard/main_dashboard.py
"""
دشبورد اصلی سیستم پذیرش
"""

import logging
from datetime import datetime, date
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QGroupBox, QFrame)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor

from app.services.reception.guest_service import GuestService
from app.services.reception.room_service import RoomService
from app.services.reception.report_service import ReportService

logger = logging.getLogger(__name__)

class MainDashboard(QWidget):
    """دشبورد اصلی سیستم پذیرش"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_dashboard_data()

        # تایمر برای به‌روزرسانی خودکار
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_dashboard_data)
        self.refresh_timer.start(60000)  # هر 1 دقیقه

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # هدر دشبورد
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # کارت‌های آمار
        stats_layout = self.create_stats_cards()
        main_layout.addLayout(stats_layout)

        # بخش‌های اطلاعات
        info_layout = self.create_info_sections()
        main_layout.addLayout(info_layout)

        self.setLayout(main_layout)

    def create_header(self):
        """ایجاد هدر دشبورد"""
        layout = QHBoxLayout()

        # عنوان و تاریخ
        title_layout = QVBoxLayout()

        self.lbl_title = QLabel("دشبورد پذیرش")
        self.lbl_title.setFont(QFont("Arial", 18, QFont.Bold))

        self.lbl_datetime = QLabel()
        self.update_datetime()

        title_layout.addWidget(self.lbl_title)
        title_layout.addWidget(self.lbl_datetime)

        layout.addLayout(title_layout)
        layout.addStretch()

        # دکمه‌های عملیاتی
        btn_layout = QHBoxLayout()

        btn_refresh = QPushButton("بروزرسانی")
        btn_refresh.clicked.connect(self.load_dashboard_data)

        btn_reports = QPushButton("گزارش‌ها")
        # btn_reports.clicked.connect(self.show_reports)

        btn_layout.addWidget(btn_refresh)
        btn_layout.addWidget(btn_reports)

        layout.addLayout(btn_layout)

        return layout

    def create_stats_cards(self):
        """ایجاد کارت‌های آمار"""
        layout = QGridLayout()

        # کارت اشغال اتاق‌ها
        self.occupancy_card = self.create_stat_card(
            "اشغال اتاق‌ها", "0", "از 0 اتاق", QColor(41, 128, 185)
        )
        layout.addWidget(self.occupancy_card, 0, 0)

        # کارت مهمانان حاضر
        self.guests_card = self.create_stat_card(
            "مهمانان حاضر", "0", "مهمان در هتل", QColor(39, 174, 96)
        )
        layout.addWidget(self.guests_card, 0, 1)

        # کارت ورودهای امروز
        self.arrivals_card = self.create_stat_card(
            "ورودهای امروز", "0", "مهمان جدید", QColor(142, 68, 173)
        )
        layout.addWidget(self.arrivals_card, 0, 2)

        # کارت خروج‌های امروز
        self.departures_card = self.create_stat_card(
            "خروج‌های امروز", "0", "مهمان خروجی", QColor(230, 126, 34)
        )
        layout.addWidget(self.departures_card, 0, 3)

        return layout

    def create_stat_card(self, title, value, description, color):
        """ایجاد یک کارت آمار"""
        card = QGroupBox(title)
        card.setMinimumHeight(120)
        layout = QVBoxLayout()

        # مقدار
        lbl_value = QLabel(value)
        lbl_value.setFont(QFont("Arial", 24, QFont.Bold))
        lbl_value.setStyleSheet(f"color: {color.name()};")
        lbl_value.setAlignment(Qt.AlignCenter)

        # توضیح
        lbl_desc = QLabel(description)
        lbl_desc.setAlignment(Qt.AlignCenter)
        lbl_desc.setStyleSheet("color: #666;")

        layout.addWidget(lbl_value)
        layout.addWidget(lbl_desc)

        card.setLayout(layout)
        return card

    def create_info_sections(self):
        """ایجاد بخش‌های اطلاعات"""
        layout = QHBoxLayout()

        # بخش مهمانان
        guests_section = self.create_guests_section()
        layout.addWidget(guests_section, 2)  # 2 واحد فضای بیشتر

        # بخش فعالیت‌ها
        activities_section = self.create_activities_section()
        layout.addWidget(activities_section, 1)

        return layout

    def create_guests_section(self):
        """بخش اطلاعات مهمانان"""
        section = QGroupBox("مهمانان امروز")
        layout = QVBoxLayout()

        # لیست مهمانان ورودی امروز
        arrivals_group = QGroupBox("ورودهای امروز")
        arrivals_layout = QVBoxLayout()

        self.lbl_arrivals_list = QLabel("در حال بارگذاری...")
        self.lbl_arrivals_list.setWordWrap(True)
        arrivals_layout.addWidget(self.lbl_arrivals_list)

        arrivals_group.setLayout(arrivals_layout)
        layout.addWidget(arrivals_group)

        # لیست مهمانان خروجی امروز
        departures_group = QGroupBox("خروج‌های امروز")
        departures_layout = QVBoxLayout()

        self.lbl_departures_list = QLabel("در حال بارگذاری...")
        self.lbl_departures_list.setWordWrap(True)
        departures_layout.addWidget(self.lbl_departures_list)

        departures_group.setLayout(departures_layout)
        layout.addWidget(departures_group)

        section.setLayout(layout)
        return section

    def create_activities_section(self):
        """بخش فعالیت‌های اخیر"""
        section = QGroupBox("فعالیت‌های اخیر")
        layout = QVBoxLayout()

        self.lbl_activities = QLabel("در حال بارگذاری...")
        self.lbl_activities.setWordWrap(True)

        layout.addWidget(self.lbl_activities)
        layout.addStretch()

        section.setLayout(layout)
        return section

    def load_dashboard_data(self):
        """بارگذاری داده‌های دشبورد"""
        try:
            # بارگذاری آمار کلی
            self.load_overall_stats()

            # بارگذاری لیست مهمانان امروز
            self.load_today_guests()

            # به‌روزرسانی تاریخ و زمان
            self.update_datetime()

        except Exception as e:
            logger.error(f"خطا در بارگذاری داده‌های دشبورد: {e}")

    def load_overall_stats(self):
        """بارگذاری آمار کلی"""
        try:
            # گزارش روزانه اشغال
            report_result = ReportService.generate_daily_occupancy_report()

            if report_result['success']:
                report_data = report_result['report']
                summary = report_data['summary']

                # به‌روزرسانی کارت‌ها
                self.update_stat_card(self.occupancy_card,
                                   f"{summary['occupancy_rate']}%",
                                   f"{summary['occupied_rooms']} از {summary['total_rooms']} اتاق")

                self.update_stat_card(self.guests_card,
                                   str(summary.get('current_guests', 0)),
                                   "مهمان در هتل")

                self.update_stat_card(self.arrivals_card,
                                   str(summary['arrivals_today']),
                                   "مهمان جدید")

                self.update_stat_card(self.departures_card,
                                   str(summary['departures_today']),
                                   "مهمان خروجی")

        except Exception as e:
            logger.error(f"خطا در بارگذاری آمار کلی: {e}")

    def load_today_guests(self):
        """بارگذاری لیست مهمانان امروز"""
        try:
            report_result = ReportService.generate_daily_occupancy_report()

            if report_result['success']:
                report_data = report_result['report']
                details = report_data.get('details', {})

                # ورودهای امروز
                arrivals = details.get('arrivals', [])
                arrivals_text = "\n".join([
                    f"• {arrival['guest_name']} - {arrival.get('room_number', 'اتاق تعیین نشده')}"
                    for arrival in arrivals[:5]  # فقط 5 مورد اول
                ]) if arrivals else "هیچ ورودی برای امروز ثبت نشده است"

                self.lbl_arrivals_list.setText(arrivals_text)

                # خروج‌های امروز
                departures = details.get('departures', [])
                departures_text = "\n".join([
                    f"• {departure['guest_name']} - {departure.get('room_number', 'اتاق تعیین نشده')}"
                    for departure in departures[:5]  # فقط 5 مورد اول
                ]) if departures else "هیچ خروجی برای امروز ثبت نشده است"

                self.lbl_departures_list.setText(departures_text)

        except Exception as e:
            logger.error(f"خطا در بارگذاری لیست مهمانان: {e}")
            self.lbl_arrivals_list.setText("خطا در بارگذاری داده‌ها")
            self.lbl_departures_list.setText("خطا در بارگذاری داده‌ها")

    def update_stat_card(self, card, value, description):
        """به‌روزرسانی یک کارت آمار"""
        layout = card.layout()
        if layout and layout.count() >= 2:
            value_label = layout.itemAt(0).widget()
            desc_label = layout.itemAt(1).widget()

            if isinstance(value_label, QLabel) and isinstance(desc_label, QLabel):
                value_label.setText(value)
                desc_label.setText(description)

    def update_datetime(self):
        """به‌روزرسانی تاریخ و زمان"""
        now = datetime.now()
        date_str = now.strftime("%Y/%m/%d")
        time_str = now.strftime("%H:%M:%S")
        day_name = self.get_persian_day_name(now.weekday())

        self.lbl_datetime.setText(f"{day_name}، {date_str} - {time_str}")

    def get_persian_day_name(self, weekday):
        """تبدیل روز هفته به فارسی"""
        days = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
        return days[weekday]
