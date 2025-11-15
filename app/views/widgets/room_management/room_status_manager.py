# app/views/widgets/room_management/room_status_manager.py
"""
ویجت مدیریت پیشرفته وضعیت اتاق‌ها
"""

import logging
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QPushButton, QComboBox, QGroupBox,
                            QTableWidget, QTableWidgetItem, QHeaderView,
                            QMessageBox, QDateEdit, QSpinBox)
from PyQt5.QtCore import QDate, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QBrush

from app.services.reception.room_service import RoomService
from app.services.reception.report_service import ReportService
from config import config

logger = logging.getLogger(__name__)

class RoomStatusManager(QWidget):
    """ویجت مدیریت پیشرفته وضعیت اتاق‌ها"""

    # سیگنال‌ها
    status_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rooms_data = []
        self.init_ui()
        self.load_room_status()

        # تایمر برای به‌روزرسانی خودکار
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_room_status)
        self.refresh_timer.start(60000)  # هر 1 دقیقه

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # آمار کلی
        stats_group = self.create_stats_group()
        main_layout.addWidget(stats_group)

        # فیلترها و جستجو
        filter_group = self.create_filter_group()
        main_layout.addWidget(filter_group)

        # جدول وضعیت‌ها
        table_group = self.create_table_group()
        main_layout.addWidget(table_group)

        # عملیات گروهی
        batch_operations_group = self.create_batch_operations_group()
        main_layout.addWidget(batch_operations_group)

        self.setLayout(main_layout)

    def create_stats_group(self):
        """گروه آمار کلی"""
        group = QGroupBox("آمار وضعیت اتاق‌ها")
        layout = QGridLayout()

        self.lbl_total_rooms = QLabel("0")
        self.lbl_vacant_rooms = QLabel("0")
        self.lbl_occupied_rooms = QLabel("0")
        self.lbl_cleaning_rooms = QLabel("0")
        self.lbl_maintenance_rooms = QLabel("0")
        self.lbl_occupancy_rate = QLabel("0%")

        stats = [
            ("کل اتاق‌ها", self.lbl_total_rooms, QColor(52, 152, 219)),
            ("اتاق‌های خالی", self.lbl_vacant_rooms, QColor(46, 204, 113)),
            ("اتاق‌های اشغال", self.lbl_occupied_rooms, QColor(231, 76, 60)),
            ("اتاق‌های در حال نظافت", self.lbl_cleaning_rooms, QColor(230, 126, 34)),
            ("اتاق‌های تعمیرات", self.lbl_maintenance_rooms, QColor(155, 89, 182)),
            ("نرخ اشغال", self.lbl_occupancy_rate, QColor(241, 196, 15))
        ]

        for i, (title, label, color) in enumerate(stats):
            stat_frame = self.create_stat_frame(title, label, color)
            layout.addWidget(stat_frame, i // 3, i % 3)

        group.setLayout(layout)
        return group

    def create_stat_frame(self, title, value_label, color):
        """ایجاد فریم آمار"""
        frame = QGroupBox(title)
        layout = QVBoxLayout()

        value_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color.name()};")
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(value_label)
        frame.setLayout(layout)
        return frame

    def create_filter_group(self):
        """گروه فیلترها"""
        group = QGroupBox("فیلتر و جستجو")
        layout = QHBoxLayout()

        # فیلتر تاریخ
        self.date_filter = QDateEdit()
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.dateChanged.connect(self.apply_filters)

        # فیلتر وضعیت
        self.status_filter = QComboBox()
        self.status_filter.addItems(["همه وضعیت‌ها", "خالی", "اشغال", "نظافت", "تعمیرات", "غیرقابل استفاده"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)

        # فیلتر طبقه
        self.floor_filter = QComboBox()
        self.floor_filter.addItems(["همه طبقات", "طبقه 1", "طبقه 2", "طبقه 3", "طبقه 4", "طبقه 5"])
        self.floor_filter.currentTextChanged.connect(self.apply_filters)

        layout.addWidget(QLabel("تاریخ:"))
        layout.addWidget(self.date_filter)
        layout.addWidget(QLabel("وضعیت:"))
        layout.addWidget(self.status_filter)
        layout.addWidget(QLabel("طبقه:"))
        layout.addWidget(self.floor_filter)
        layout.addStretch()

        # دکمه‌های عملیاتی
        btn_refresh = QPushButton("بروزرسانی")
        btn_refresh.clicked.connect(self.load_room_status)

        btn_export = QPushButton("خروجی گزارش")
        btn_export.clicked.connect(self.export_report)

        layout.addWidget(btn_refresh)
        layout.addWidget(btn_export)

        group.setLayout(layout)
        return group

    def create_table_group(self):
        """گروه جدول وضعیت‌ها"""
        group = QGroupBox("وضعیت اتاق‌ها")
        layout = QVBoxLayout()

        self.status_table = QTableWidget()
        self.status_table.setColumnCount(7)
        self.status_table.setHorizontalHeaderLabels([
            "شماره اتاق", "طبقه", "نوع", "وضعیت فعلی", "مهمان فعلی",
            "تاریخ تغییر", "عملیات"
        ])

        self.status_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.status_table.setSelectionMode(QTableWidget.MultiSelection)

        header = self.status_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout.addWidget(self.status_table)
        group.setLayout(layout)
        return group

    def create_batch_operations_group(self):
        """گروه عملیات گروهی"""
        group = QGroupBox("عملیات گروهی")
        layout = QHBoxLayout()

        self.cmb_batch_action = QComboBox()
        self.cmb_batch_action.addItems([
            "تغییر وضعیت به خالی",
            "تغییر وضعیت به نظافت",
            "تغییر وضعیت به تعمیرات",
            "ایجاد وظیفه نظافت"
        ])

        self.btn_apply_batch = QPushButton("اعمال بر روی انتخاب شده‌ها")
        self.btn_apply_batch.clicked.connect(self.apply_batch_operation)
        self.btn_apply_batch.setEnabled(False)

        layout.addWidget(QLabel("عملیات:"))
        layout.addWidget(self.cmb_batch_action)
        layout.addWidget(self.btn_apply_batch)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def load_room_status(self):
        """بارگذاری وضعیت اتاق‌ها"""
        try:
            result = RoomService.get_room_status()

            if result['success']:
                self.rooms_data = result['rooms']
                self.update_stats()
                self.populate_table(self.rooms_data)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری وضعیت اتاق‌ها: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری وضعیت اتاق‌ها: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری وضعیت اتاق‌ها: {str(e)}")

    def update_stats(self):
        """به‌روزرسانی آمار"""
        if not self.rooms_data:
            return

        total_rooms = len(self.rooms_data)
        vacant_rooms = len([r for r in self.rooms_data if r['current_status'] == 'vacant'])
        occupied_rooms = len([r for r in self.rooms_data if r['current_status'] == 'occupied'])
        cleaning_rooms = len([r for r in self.rooms_data if r['current_status'] == 'cleaning'])
        maintenance_rooms = len([r for r in self.rooms_data if r['current_status'] == 'maintenance'])

        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

        self.lbl_total_rooms.setText(str(total_rooms))
        self.lbl_vacant_rooms.setText(str(vacant_rooms))
        self.lbl_occupied_rooms.setText(str(occupied_rooms))
        self.lbl_cleaning_rooms.setText(str(cleaning_rooms))
        self.lbl_maintenance_rooms.setText(str(maintenance_rooms))
        self.lbl_occupancy_rate.setText(f"{occupancy_rate:.1f}%")

    def populate_table(self, rooms):
        """پر کردن جدول با داده اتاق‌ها"""
        self.status_table.setRowCount(len(rooms))

        for row, room in enumerate(rooms):
            # شماره اتاق
            self.status_table.setItem(row, 0, QTableWidgetItem(room['room_number']))

            # طبقه
            self.status_table.setItem(row, 1, QTableWidgetItem(str(room['floor'])))

            # نوع اتاق
            self.status_table.setItem(row, 2, QTableWidgetItem(room['room_type']))

            # وضعیت فعلی
            status_item = QTableWidgetItem(self.get_status_text(room['current_status']))
            self.set_status_color(status_item, room['current_status'])
            self.status_table.setItem(row, 3, status_item)

            # مهمان فعلی
            guest_name = "--"
            if room['current_guest']:
                guest_name = room['current_guest']['full_name']
            self.status_table.setItem(row, 4, QTableWidgetItem(guest_name))

            # تاریخ تغییر
            last_update = room.get('last_status_change', '--')
            self.status_table.setItem(row, 5, QTableWidgetItem(str(last_update)))

            # عملیات
            actions_item = QTableWidgetItem("مدیریت")
            actions_item.setForeground(QBrush(QColor(0, 0, 255)))
            self.status_table.setItem(row, 6, actions_item)

        # فعال کردن دکمه عملیات گروهی اگر ردیفی انتخاب شده باشد
        self.status_table.itemSelectionChanged.connect(self.on_selection_changed)

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
        }

        if status in color_map:
            item.setForeground(QBrush(color_map[status]))

    def apply_filters(self):
        """اعمال فیلترها"""
        # این متد نیاز به پیاده‌سازی دارد
        pass

    def on_selection_changed(self):
        """هنگام تغییر انتخاب‌ها"""
        selected_count = len(self.status_table.selectedItems()) // self.status_table.columnCount()
        self.btn_apply_batch.setEnabled(selected_count > 0)

    def apply_batch_operation(self):
        """اعمال عملیات گروهی"""
        selected_rows = set()
        for item in self.status_table.selectedItems():
            selected_rows.add(item.row())

        if not selected_rows:
            return

        action = self.cmb_batch_action.currentText()

        reply = QMessageBox.question(
            self, 'تأیید عملیات گروهی',
            f'آیا از اعمال "{action}" بر روی {len(selected_rows)} اتاق اطمینان دارید؟',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.process_batch_operation(list(selected_rows), action)

    def process_batch_operation(self, rows, action):
        """پردازش عملیات گروهی"""
        try:
            room_ids = []
            for row in rows:
                room_number = self.status_table.item(row, 0).text()
                room = next((r for r in self.rooms_data if r['room_number'] == room_number), None)
                if room:
                    room_ids.append(room['room_id'])

            # انجام عملیات گروهی
            if "تغییر وضعیت" in action:
                status_map = {
                    "تغییر وضعیت به خالی": "vacant",
                    "تغییر وضعیت به نظافت": "cleaning",
                    "تغییر وضعیت به تعمیرات": "maintenance"
                }

                new_status = status_map.get(action)
                if new_status:
                    for room_id in room_ids:
                        RoomService.update_room_status(
                            room_id=room_id,
                            new_status=new_status,
                            changed_by=1,  # TODO: دریافت از کاربر لاگین شده
                            reason="عملیات گروهی"
                        )

            QMessageBox.information(self, "موفق", f"عملیات بر روی {len(room_ids)} اتاق اعمال شد")
            self.load_room_status()
            self.status_updated.emit()

        except Exception as e:
            logger.error(f"خطا در عملیات گروهی: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در عملیات گروهی: {str(e)}")

    def export_report(self):
        """صدور گزارش"""
        try:
            report_date = self.date_filter.date().toPyDate()
            result = ReportService.generate_daily_occupancy_report(report_date)

            if result['success']:
                # TODO: پیاده‌سازی صدور گزارش به Excel
                QMessageBox.information(self, "موفق", "گزارش با موفقیت ایجاد شد")
            else:
                QMessageBox.warning(self, "خطا", f"خطا در ایجاد گزارش: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در صدور گزارش: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در صدور گزارش: {str(e)}")
