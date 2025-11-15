# app/views/widgets/dashboard/today_activities.py
"""
ویجت نمایش فعالیت‌های امروز سیستم پذیرش
"""

import logging
from datetime import datetime, date
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                            QLabel, QPushButton, QGroupBox, QListWidgetItem,
                            QFrame, QProgressBar)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon

from app.services.reception.guest_service import GuestService
from app.services.reception.room_service import RoomService
from app.services.reception.housekeeping_service import HousekeepingService

logger = logging.getLogger(__name__)

class TodayActivitiesWidget(QWidget):
    """ویجت نمایش فعالیت‌های امروز"""

    # سیگنال‌ها
    activity_selected = pyqtSignal(dict)  # اطلاعات فعالیت انتخاب شده
    refresh_requested = pyqtSignal()      # درخواست بروزرسانی

    def __init__(self, parent=None):
        super().__init__(parent)
        self.activities_data = []
        self.init_ui()
        self.load_activities()

        # تایمر برای به‌روزرسانی خودکار
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_activities)
        self.refresh_timer.start(60000)  # هر 1 دقیقه

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # هدر و آمار
        header_layout = self.create_header()
        main_layout.addLayout(header_layout)

        # لیست فعالیت‌ها
        activities_group = self.create_activities_list()
        main_layout.addWidget(activities_group)

        # نوار وضعیت
        status_layout = self.create_status_bar()
        main_layout.addLayout(status_layout)

        self.setLayout(main_layout)

    def create_header(self):
        """ایجاد هدر ویجت"""
        layout = QHBoxLayout()

        # عنوان
        title_label = QLabel("فعالیت‌های امروز")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        layout.addWidget(title_label)
        layout.addStretch()

        # دکمه بروزرسانی
        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("بروزرسانی فعالیت‌ها")
        btn_refresh.clicked.connect(self.load_activities)
        btn_refresh.setFixedSize(30, 30)

        layout.addWidget(btn_refresh)

        return layout

    def create_activities_list(self):
        """ایجاد لیست فعالیت‌ها"""
        group = QGroupBox()
        group.setStyleSheet("QGroupBox { border: 1px solid #bdc3c7; border-radius: 5px; }")
        layout = QVBoxLayout()

        # فیلترهای سریع
        filter_layout = QHBoxLayout()

        self.btn_all = QPushButton("همه")
        self.btn_all.setCheckable(True)
        self.btn_all.setChecked(True)
        self.btn_all.clicked.connect(self.filter_activities)

        self.btn_arrivals = QPushButton("ورودها")
        self.btn_arrivals.setCheckable(True)
        self.btn_arrivals.clicked.connect(self.filter_activities)

        self.btn_departures = QPushButton("خروج‌ها")
        self.btn_departures.setCheckable(True)
        self.btn_departures.clicked.connect(self.filter_activities)

        self.btn_cleaning = QPushButton("نظافت")
        self.btn_cleaning.setCheckable(True)
        self.btn_cleaning.clicked.connect(self.filter_activities)

        filter_layout.addWidget(self.btn_all)
        filter_layout.addWidget(self.btn_arrivals)
        filter_layout.addWidget(self.btn_departures)
        filter_layout.addWidget(self.btn_cleaning)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # لیست فعالیت‌ها
        self.activities_list = QListWidget()
        self.activities_list.itemClicked.connect(self.on_activity_selected)
        self.activities_list.setAlternatingRowColors(True)
        self.activities_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: #f8f9fa;
            }
            QListWidget::item {
                border-bottom: 1px solid #e9ecef;
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)

        layout.addWidget(self.activities_list)

        group.setLayout(layout)
        return group

    def create_status_bar(self):
        """ایجاد نوار وضعیت"""
        layout = QHBoxLayout()

        # پیشرفت روز
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("پیشرفت روز: %p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 4px;
            }
        """)

        # تعداد فعالیت‌ها
        self.lbl_activity_count = QLabel("0 فعالیت")
        self.lbl_activity_count.setStyleSheet("color: #7f8c8d; font-size: 12px;")

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.lbl_activity_count)

        return layout

    def load_activities(self):
        """بارگذاری فعالیت‌های امروز"""
        try:
            # شبیه‌سازی داده‌های فعالیت‌ها
            self.activities_data = self.get_todays_activities()
            self.display_activities(self.activities_data)
            self.update_progress()
            self.refresh_requested.emit()

        except Exception as e:
            logger.error(f"خطا در بارگذاری فعالیت‌ها: {e}")

    def get_todays_activities(self):
        """دریافت فعالیت‌های امروز از سرویس‌ها"""
        activities = []

        try:
            # فعالیت‌های مهمانان
            guest_activities = self.get_guest_activities()
            activities.extend(guest_activities)

            # فعالیت‌های نظافت
            cleaning_activities = self.get_cleaning_activities()
            activities.extend(cleaning_activities)

            # فعالیت‌های تعمیرات
            maintenance_activities = self.get_maintenance_activities()
            activities.extend(maintenance_activities)

            # مرتب‌سازی بر اساس زمان
            activities.sort(key=lambda x: x.get('timestamp', datetime.now()), reverse=True)

        except Exception as e:
            logger.error(f"خطا در دریافت فعالیت‌ها: {e}")

        return activities

    def get_guest_activities(self):
        """دریافت فعالیت‌های مهمانان"""
        activities = []

        try:
            # شبیه‌سازی داده‌های مهمانان
            sample_guests = [
                {
                    'type': 'arrival',
                    'title': 'ورود مهمان جدید',
                    'description': 'آقای احمدی - اتاق ۲۰۱',
                    'timestamp': datetime.now().replace(hour=10, minute=30),
                    'priority': 'high',
                    'status': 'completed'
                },
                {
                    'type': 'departure',
                    'title': 'خروج مهمان',
                    'description': 'خانم رضایی - اتاق ۱۰۵',
                    'timestamp': datetime.now().replace(hour=12, minute=15),
                    'priority': 'medium',
                    'status': 'pending'
                },
                {
                    'type': 'check_in',
                    'title': 'ثبت ورود',
                    'description': 'آقای محمدی - اتاق ۳۰۲',
                    'timestamp': datetime.now().replace(hour=9, minute=0),
                    'priority': 'high',
                    'status': 'completed'
                }
            ]

            activities.extend(sample_guests)

        except Exception as e:
            logger.error(f"خطا در دریافت فعالیت‌های مهمانان: {e}")

        return activities

    def get_cleaning_activities(self):
        """دریافت فعالیت‌های نظافت"""
        activities = []

        try:
            # شبیه‌سازی داده‌های نظافت
            sample_cleaning = [
                {
                    'type': 'cleaning',
                    'title': 'اتاق آماده شد',
                    'description': 'اتاق ۲۰۱ - نظافت تکمیل شد',
                    'timestamp': datetime.now().replace(hour=11, minute=0),
                    'priority': 'medium',
                    'status': 'completed'
                },
                {
                    'type': 'cleaning',
                    'title': 'در حال نظافت',
                    'description': 'اتاق ۱۰۵ - پس از خروج مهمان',
                    'timestamp': datetime.now().replace(hour=12, minute=30),
                    'priority': 'high',
                    'status': 'in_progress'
                }
            ]

            activities.extend(sample_cleaning)

        except Exception as e:
            logger.error(f"خطا در دریافت فعالیت‌های نظافت: {e}")

        return activities

    def get_maintenance_activities(self):
        """دریافت فعالیت‌های تعمیرات"""
        activities = []

        try:
            # شبیه‌سازی داده‌های تعمیرات
            sample_maintenance = [
                {
                    'type': 'maintenance',
                    'title': 'تعمیرات تکمیل شد',
                    'description': 'اتاق ۴۰۵ - تعمیر کولر',
                    'timestamp': datetime.now().replace(hour=8, minute=45),
                    'priority': 'low',
                    'status': 'completed'
                }
            ]

            activities.extend(sample_maintenance)

        except Exception as e:
            logger.error(f"خطا در دریافت فعالیت‌های تعمیرات: {e}")

        return activities

    def display_activities(self, activities):
        """نمایش فعالیت‌ها در لیست"""
        self.activities_list.clear()

        for activity in activities:
            item = QListWidgetItem()
            widget = self.create_activity_item(activity)
            item.setSizeHint(widget.sizeHint())

            self.activities_list.addItem(item)
            self.activities_list.setItemWidget(item, widget)

        # به‌روزرسانی تعداد
        self.lbl_activity_count.setText(f"{len(activities)} فعالیت")

    def create_activity_item(self, activity):
        """ایجاد ویجت برای یک فعالیت"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)

        # سطر اول: عنوان و زمان
        top_layout = QHBoxLayout()

        # آیکون و عنوان
        icon_label = QLabel(self.get_activity_icon(activity['type']))
        icon_label.setFont(QFont("Arial", 12))

        title_label = QLabel(activity['title'])
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.get_priority_color(activity['priority'])};")

        top_layout.addWidget(icon_label)
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        # زمان
        time_str = activity['timestamp'].strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        top_layout.addWidget(time_label)

        layout.addLayout(top_layout)

        # سطر دوم: توضیحات و وضعیت
        bottom_layout = QHBoxLayout()

        desc_label = QLabel(activity['description'])
        desc_label.setStyleSheet("color: #2c3e50; font-size: 9px;")
        bottom_layout.addWidget(desc_label)
        bottom_layout.addStretch()

        # وضعیت
        status_label = QLabel(self.get_status_text(activity['status']))
        status_label.setStyleSheet(self.get_status_style(activity['status']))
        status_label.setFont(QFont("Arial", 8))
        bottom_layout.addWidget(status_label)

        layout.addLayout(bottom_layout)

        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget:hover {
                background-color: #f1f8ff;
            }
        """)

        return widget

    def get_activity_icon(self, activity_type):
        """دریافت آیکون مناسب برای نوع فعالیت"""
        icons = {
            'arrival': '👋',
            'departure': '🚪',
            'check_in': '🔑',
            'check_out': '🧾',
            'cleaning': '🧹',
            'maintenance': '🔧',
            'payment': '💳'
        }
        return icons.get(activity_type, '📝')

    def get_priority_color(self, priority):
        """دریافت رنگ بر اساس اولویت"""
        colors = {
            'high': '#e74c3c',
            'medium': '#f39c12',
            'low': '#27ae60'
        }
        return colors.get(priority, '#7f8c8d')

    def get_status_text(self, status):
        """متن وضعیت به فارسی"""
        status_map = {
            'completed': 'تکمیل شده',
            'pending': 'در انتظار',
            'in_progress': 'در حال انجام',
            'cancelled': 'لغو شده'
        }
        return status_map.get(status, status)

    def get_status_style(self, status):
        """استایل وضعیت"""
        styles = {
            'completed': 'color: #27ae60; background-color: #d5f4e6; padding: 2px 6px; border-radius: 3px;',
            'pending': 'color: #f39c12; background-color: #fef5e7; padding: 2px 6px; border-radius: 3px;',
            'in_progress': 'color: #3498db; background-color: #ebf5fb; padding: 2px 6px; border-radius: 3px;',
            'cancelled': 'color: #e74c3c; background-color: #fdedec; padding: 2px 6px; border-radius: 3px;'
        }
        return styles.get(status, '')

    def filter_activities(self):
        """فیلتر فعالیت‌ها بر اساس نوع"""
        sender = self.sender()

        # Reset all buttons
        self.btn_all.setChecked(False)
        self.btn_arrivals.setChecked(False)
        self.btn_departures.setChecked(False)
        self.btn_cleaning.setChecked(False)

        # Set the clicked button as checked
        sender.setChecked(True)

        # Filter activities
        if sender == self.btn_all:
            filtered_activities = self.activities_data
        elif sender == self.btn_arrivals:
            filtered_activities = [a for a in self.activities_data if a['type'] in ['arrival', 'check_in']]
        elif sender == self.btn_departures:
            filtered_activities = [a for a in self.activities_data if a['type'] in ['departure', 'check_out']]
        elif sender == self.btn_cleaning:
            filtered_activities = [a for a in self.activities_data if a['type'] in ['cleaning', 'maintenance']]
        else:
            filtered_activities = self.activities_data

        self.display_activities(filtered_activities)

    def update_progress(self):
        """به‌روزرسانی پیشرفت روز"""
        try:
            now = datetime.now()
            hour = now.hour
            minute = now.minute

            # محاسبه درصد پیشرفت روز (از 6 صبح تا 10 شب)
            total_minutes = (22 - 6) * 60  # 16 ساعت
            current_minutes = (hour - 6) * 60 + minute
            progress = min(max(0, (current_minutes / total_minutes) * 100), 100)

            self.progress_bar.setValue(int(progress))

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی پیشرفت: {e}")

    def on_activity_selected(self, item):
        """هنگام انتخاب یک فعالیت"""
        try:
            index = self.activities_list.row(item)
            if 0 <= index < len(self.activities_data):
                activity = self.activities_data[index]
                self.activity_selected.emit(activity)

        except Exception as e:
            logger.error(f"خطا در انتخاب فعالیت: {e}")

    def add_custom_activity(self, activity_data):
        """افزودن فعالیت جدید"""
        try:
            activity_data['timestamp'] = datetime.now()
            self.activities_data.insert(0, activity_data)
            self.display_activities(self.activities_data)

        except Exception as e:
            logger.error(f"خطا در افزودن فعالیت: {e}")

    def clear_completed_activities(self):
        """پاک کردن فعالیت‌های تکمیل شده"""
        try:
            self.activities_data = [a for a in self.activities_data if a['status'] != 'completed']
            self.display_activities(self.activities_data)

        except Exception as e:
            logger.error(f"خطا در پاک کردن فعالیت‌ها: {e}")
