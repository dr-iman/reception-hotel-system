# app/views/main_window.py
import logging
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTabWidget, QStatusBar, QMenuBar, QMenu, QAction,
                            QToolBar, QLabel, QMessageBox, QSplitter, QFrame,
                            QDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont

from app.views.widgets.dashboard.main_dashboard import MainDashboard
from app.views.widgets.dashboard.room_status_widget import RoomStatusWidget
from app.views.widgets.guest_management.guest_list_widget import GuestListWidget
from app.views.widgets.guest_management.guest_details_widget import GuestDetailsWidget
from app.views.widgets.guest_management.check_in_widget import CheckInWidget
from app.views.widgets.guest_management.check_out_widget import CheckOutWidget
from app.views.widgets.room_management.room_list_widget import RoomListWidget
from app.views.widgets.room_management.room_assignment import RoomAssignmentWidget
from app.views.widgets.room_management.room_status_manager import RoomStatusManager
from config import config

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """پنجره اصلی سیستم پذیرش - نسخه به‌روز شده"""

    def __init__(self):
        super().__init__()
        self.current_user = None
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle(f"{config.app.app_name} - نسخه {config.app.version}")
        self.setGeometry(100, 100, 1400, 900)

        # ایجاد منوها
        self.create_menus()

        # ایجاد نوار ابزار
        self.create_toolbar()

        # ایجاد ویجت مرکزی
        self.central_widget = self.create_central_widget()
        self.setCentralWidget(self.central_widget)

        # ایجاد نوار وضعیت
        self.create_statusbar()

        # تایمر برای به‌روزرسانی وضعیت
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_statusbar)
        self.status_timer.start(5000)  # هر 5 ثانیه

    def create_menus(self):
        """ایجاد منوهای اصلی"""
        menubar = self.menuBar()

        # منوی فایل
        file_menu = menubar.addMenu('فایل')

        new_guest_action = QAction('مهمان جدید', self)
        new_guest_action.setShortcut('Ctrl+N')
        new_guest_action.triggered.connect(self.new_guest)
        file_menu.addAction(new_guest_action)

        file_menu.addSeparator()

        exit_action = QAction('خروج', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # منوی مدیریت
        management_menu = menubar.addMenu('مدیریت')

        guests_action = QAction('مدیریت مهمانان', self)
        guests_action.setShortcut('Ctrl+G')
        guests_action.triggered.connect(self.show_guests_management)
        management_menu.addAction(guests_action)

        rooms_action = QAction('مدیریت اتاق‌ها', self)
        rooms_action.setShortcut('Ctrl+R')
        rooms_action.triggered.connect(self.show_rooms_management)
        management_menu.addAction(rooms_action)

        # منوی اتاق‌ها
        rooms_menu = menubar.addMenu('اتاق‌ها')

        room_status_action = QAction('وضعیت اتاق‌ها', self)
        room_status_action.setShortcut('Ctrl+S')
        room_status_action.triggered.connect(self.show_room_status)
        rooms_menu.addAction(room_status_action)

        room_assign_action = QAction('تخصیص اتاق', self)
        room_assign_action.triggered.connect(self.show_room_assignment)
        rooms_menu.addAction(room_assign_action)

        # منوی گزارش‌ها
        reports_menu = menubar.addMenu('گزارش‌ها')

        daily_report_action = QAction('گزارش روزانه', self)
        daily_report_action.triggered.connect(self.show_daily_report)
        reports_menu.addAction(daily_report_action)

        financial_report_action = QAction('گزارش مالی', self)
        financial_report_action.triggered.connect(self.show_financial_report)
        reports_menu.addAction(financial_report_action)

        # منوی تنظیمات
        settings_menu = menubar.addMenu('تنظیمات')

        user_settings_action = QAction('تنظیمات کاربری', self)
        user_settings_action.triggered.connect(self.show_user_settings)
        settings_menu.addAction(user_settings_action)

        system_settings_action = QAction('تنظیمات سیستم', self)
        system_settings_action.triggered.connect(self.show_system_settings)
        settings_menu.addAction(system_settings_action)

        # منوی راهنما
        help_menu = menubar.addMenu('راهنما')

        about_action = QAction('درباره سیستم', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        """ایجاد نوار ابزار"""
        toolbar = QToolBar('نوار ابزار اصلی')
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # دکمه دشبورد
        dashboard_action = QAction('دشبورد', self)
        dashboard_action.triggered.connect(self.show_dashboard)
        toolbar.addAction(dashboard_action)

        toolbar.addSeparator()

        # دکمه مدیریت مهمانان
        guests_action = QAction('مهمانان', self)
        guests_action.triggered.connect(self.show_guests_management)
        toolbar.addAction(guests_action)

        # دکمه وضعیت اتاق‌ها
        rooms_action = QAction('اتاق‌ها', self)
        rooms_action.triggered.connect(self.show_rooms_management)
        toolbar.addAction(rooms_action)

        toolbar.addSeparator()

        # دکمه ثبت ورود
        checkin_action = QAction('ثبت ورود', self)
        checkin_action.triggered.connect(self.quick_checkin)
        toolbar.addAction(checkin_action)

        # دکمه ثبت خروج
        checkout_action = QAction('ثبت خروج', self)
        checkout_action.triggered.connect(self.quick_checkout)
        toolbar.addAction(checkout_action)

        # دکمه تخصیص اتاق
        assign_action = QAction('تخصیص اتاق', self)
        assign_action.triggered.connect(self.quick_assign_room)
        toolbar.addAction(assign_action)

    def create_central_widget(self):
        """ایجاد ویجت مرکزی"""
        central_widget = QWidget()
        main_layout = QVBoxLayout()

        # ایجاد تب‌های اصلی
        self.main_tabs = QTabWidget()
        self.main_tabs.setDocumentMode(True)
        self.main_tabs.setTabPosition(QTabWidget.North)

        # تب دشبورد
        self.dashboard_tab = self.create_dashboard_tab()
        self.main_tabs.addTab(self.dashboard_tab, "🏠 دشبورد")

        # تب مدیریت مهمانان
        self.guests_tab = self.create_guests_tab()
        self.main_tabs.addTab(self.guests_tab, "👥 مدیریت مهمانان")

        # تب مدیریت اتاق‌ها
        self.rooms_tab = self.create_rooms_tab()
        self.main_tabs.addTab(self.rooms_tab, "🏨 مدیریت اتاق‌ها")

        main_layout.addWidget(self.main_tabs)
        central_widget.setLayout(main_layout)

        return central_widget

    def create_dashboard_tab(self):
        """ایجاد تب دشبورد"""
        widget = QWidget()
        layout = QVBoxLayout()

        # دشبورد اصلی
        self.dashboard_widget = MainDashboard()
        layout.addWidget(self.dashboard_widget)

        # جداکننده
        splitter = QSplitter(Qt.Vertical)

        # وضعیت اتاق‌ها
        self.room_status_widget = RoomStatusWidget()
        splitter.addWidget(self.room_status_widget)

        # TODO: افزودن ویجت فعالیت‌های اخیر
        recent_activities_frame = QFrame()
        recent_activities_frame.setFrameStyle(QFrame.Box)
        recent_layout = QVBoxLayout()
        recent_layout.addWidget(QLabel("فعالیت‌های اخیر (به زودی)"))
        recent_activities_frame.setLayout(recent_layout)
        splitter.addWidget(recent_activities_frame)

        # تنظیم سایز اولیه
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget

    def create_guests_tab(self):
        """ایجاد تب مدیریت مهمانان"""
        widget = QWidget()
        layout = QHBoxLayout()

        # ایجاد اسپلیتر برای تقسیم صفحه
        splitter = QSplitter(Qt.Horizontal)

        # لیست مهمانان (سمت چپ)
        self.guest_list_widget = GuestListWidget()
        splitter.addWidget(self.guest_list_widget)

        # جزئیات مهمان (سمت راست)
        self.guest_details_widget = GuestDetailsWidget()
        splitter.addWidget(self.guest_details_widget)

        # تنظیم سایز اولیه
        splitter.setSizes([400, 600])

        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget

    def create_rooms_tab(self):
        """ایجاد تب مدیریت اتاق‌ها - نسخه جدید"""
        widget = QWidget()
        layout = QVBoxLayout()

        # ایجاد تب‌های داخلی برای مدیریت اتاق‌ها
        self.rooms_inner_tabs = QTabWidget()

        # تب لیست اتاق‌ها
        self.room_list_tab = self.create_room_list_tab()
        self.rooms_inner_tabs.addTab(self.room_list_tab, "📋 لیست اتاق‌ها")

        # تب مدیریت وضعیت
        self.room_status_tab = self.create_room_status_tab()
        self.rooms_inner_tabs.addTab(self.room_status_tab, "🔧 مدیریت وضعیت")

        layout.addWidget(self.rooms_inner_tabs)
        widget.setLayout(layout)
        return widget

    def create_room_list_tab(self):
        """ایجاد تب لیست اتاق‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()

        # ویجت لیست اتاق‌ها
        self.room_list_widget = RoomListWidget()
        layout.addWidget(self.room_list_widget)

        widget.setLayout(layout)
        return widget

    def create_room_status_tab(self):
        """ایجاد تب مدیریت وضعیت"""
        widget = QWidget()
        layout = QVBoxLayout()

        # ویجت مدیریت وضعیت
        self.room_status_manager = RoomStatusManager()
        layout.addWidget(self.room_status_manager)

        widget.setLayout(layout)
        return widget

    def create_statusbar(self):
        """ایجاد نوار وضعیت"""
        statusbar = QStatusBar()
        self.setStatusBar(statusbar)

        # وضعیت کاربر
        self.user_status_label = QLabel("کاربر: مهمان")
        statusbar.addWidget(self.user_status_label)

        statusbar.addPermanentWidget(QLabel("|"))

        # وضعیت سیستم
        self.system_status_label = QLabel("سیستم: فعال")
        statusbar.addPermanentWidget(self.system_status_label)

        statusbar.addPermanentWidget(QLabel("|"))

        # وضعیت دیتابیس
        self.db_status_label = QLabel("دیتابیس: متصل")
        statusbar.addPermanentWidget(self.db_status_label)

        statusbar.addPermanentWidget(QLabel("|"))

        # تعداد اتاق‌های خالی
        self.available_rooms_label = QLabel("اتاق خالی: --")
        statusbar.addPermanentWidget(self.available_rooms_label)

    def setup_connections(self):
        """تنظیم اتصالات بین ویجت‌ها"""
        # اتصال لیست مهمانان به جزئیات
        self.guest_list_widget.guest_selected.connect(
            self.guest_details_widget.set_guest_id
        )

        # اتصال درخواست ثبت ورود
        self.guest_list_widget.check_in_requested.connect(
            self.show_checkin_dialog
        )

        # اتصال درخواست ثبت خروج
        self.guest_list_widget.check_out_requested.connect(
            self.show_checkout_dialog
        )

        # اتصال تغییر وضعیت اتاق‌ها
        self.room_list_widget.status_changed.connect(
            self.on_room_status_changed
        )

        self.room_status_manager.status_updated.connect(
            self.on_room_status_changed
        )

        # اتصال انتخاب اتاق
        self.room_list_widget.room_selected.connect(
            self.on_room_selected
        )

    def update_statusbar(self):
        """به‌روزرسانی نوار وضعیت"""
        try:
            # TODO: بررسی وضعیت واقعی سیستم
            current_time = "آخرین به‌روزرسانی: اکنون"
            self.system_status_label.setText(f"سیستم: فعال - {current_time}")

            # به‌روزرسانی تعداد اتاق‌های خالی
            self.update_available_rooms_count()

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی نوار وضعیت: {e}")

    def update_available_rooms_count(self):
        """به‌روزرسانی تعداد اتاق‌های خالی"""
        try:
            from app.services.reception.room_service import RoomService
            result = RoomService.get_room_status()

            if result['success']:
                rooms = result['rooms']
                vacant_rooms = len([r for r in rooms if r['current_status'] == 'vacant'])
                total_rooms = len(rooms)
                self.available_rooms_label.setText(f"اتاق خالی: {vacant_rooms}/{total_rooms}")

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی تعداد اتاق‌های خالی: {e}")

    def show_dashboard(self):
        """نمایش تب دشبورد"""
        self.main_tabs.setCurrentIndex(0)

    def show_guests_management(self):
        """نمایش تب مدیریت مهمانان"""
        self.main_tabs.setCurrentIndex(1)

    def show_rooms_management(self):
        """نمایش تب مدیریت اتاق‌ها"""
        self.main_tabs.setCurrentIndex(2)

    def show_room_status(self):
        """نمایش وضعیت اتاق‌ها"""
        self.show_rooms_management()
        self.rooms_inner_tabs.setCurrentIndex(0)  # تب لیست اتاق‌ها

    def show_room_assignment(self):
        """نمایش دیالوگ تخصیص اتاق"""
        try:
            assignment_dialog = RoomAssignmentWidget(parent=self)
            assignment_dialog.assignment_completed.connect(self.on_assignment_completed)
            assignment_dialog.exec_()
        except Exception as e:
            logger.error(f"خطا در نمایش دیالوگ تخصیص اتاق: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تخصیص اتاق: {str(e)}")

    def new_guest(self):
        """ایجاد مهمان جدید"""
        QMessageBox.information(self, "مهمان جدید", "ایجاد مهمان جدید - به زودی")

    def show_checkin_dialog(self, guest_id):
        """نمایش دیالوگ ثبت ورود"""
        try:
            checkin_dialog = CheckInWidget(guest_id, self)
            checkin_dialog.check_in_completed.connect(self.on_checkin_completed)
            checkin_dialog.exec_()
        except Exception as e:
            logger.error(f"خطا در نمایش دیالوگ ثبت ورود: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ثبت ورود: {str(e)}")

    def show_checkout_dialog(self, guest_id):
        """نمایش دیالوگ ثبت خروج"""
        try:
            # پیدا کردن اقامت فعال مهمان
            # TODO: این بخش نیاز به پیاده‌سازی دارد
            stay_id = guest_id  # موقت

            checkout_dialog = CheckOutWidget(stay_id, self)
            checkout_dialog.check_out_completed.connect(self.on_checkout_completed)
            checkout_dialog.exec_()
        except Exception as e:
            logger.error(f"خطا در نمایش دیالوگ ثبت خروج: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ثبت خروج: {str(e)}")

    def on_checkin_completed(self, stay_id):
        """هنگام تکمیل ثبت ورود"""
        QMessageBox.information(self, "موفق", "ورود مهمان با موفقیت ثبت شد")
        self.refresh_all_data()

    def on_checkout_completed(self, stay_id):
        """هنگام تکمیل ثبت خروج"""
        QMessageBox.information(self, "موفق", "خروج مهمان با موفقیت ثبت شد")
        self.refresh_all_data()

    def on_assignment_completed(self, stay_id):
        """هنگام تکمیل تخصیص اتاق"""
        QMessageBox.information(self, "موفق", "اتاق با موفقیت تخصیص داده شد")
        self.refresh_all_data()

    def on_room_status_changed(self):
        """هنگام تغییر وضعیت اتاق"""
        logger.info("وضعیت اتاق تغییر کرد - به‌روزرسانی داده‌ها")
        self.refresh_room_data()

    def on_room_selected(self, room_id):
        """هنگام انتخاب اتاق"""
        # TODO: نمایش جزئیات اتاق در یک دیالوگ یا پنل جداگانه
        logger.info(f"اتاق {room_id} انتخاب شد")

    def refresh_all_data(self):
        """به‌روزرسانی تمام داده‌ها"""
        self.refresh_guest_data()
        self.refresh_room_data()
        self.refresh_dashboard_data()

    def refresh_guest_data(self):
        """به‌روزرسانی داده‌های مهمانان"""
        if hasattr(self, 'guest_list_widget'):
            self.guest_list_widget.load_guests()
        if hasattr(self, 'guest_details_widget'):
            self.guest_details_widget.load_guest_data()

    def refresh_room_data(self):
        """به‌روزرسانی داده‌های اتاق‌ها"""
        if hasattr(self, 'room_list_widget'):
            self.room_list_widget.load_rooms()
        if hasattr(self, 'room_status_manager'):
            self.room_status_manager.load_room_status()
        if hasattr(self, 'room_status_widget'):
            self.room_status_widget.load_room_status()
        if hasattr(self, 'dashboard_widget'):
            self.dashboard_widget.load_dashboard_data()

    def refresh_dashboard_data(self):
        """به‌روزرسانی داده‌های دشبورد"""
        if hasattr(self, 'dashboard_widget'):
            self.dashboard_widget.load_dashboard_data()

    def quick_checkin(self):
        """ثبت ورود سریع"""
        # نمایش دیالوگ ثبت ورود سریع
        try:
            from app.views.widgets.guest_management.quick_checkin_widget import QuickCheckInWidget
            checkin_dialog = QuickCheckInWidget(self)
            checkin_dialog.check_in_completed.connect(self.on_checkin_completed)
            checkin_dialog.exec_()
        except ImportError:
            QMessageBox.information(self, "ثبت ورود سریع", "ثبت ورود سریع - به زودی")

    def quick_checkout(self):
        """ثبت خروج سریع"""
        # نمایش دیالوگ ثبت خروج سریع
        try:
            from app.views.widgets.guest_management.quick_checkout_widget import QuickCheckOutWidget
            checkout_dialog = QuickCheckOutWidget(self)
            checkout_dialog.check_out_completed.connect(self.on_checkout_completed)
            checkout_dialog.exec_()
        except ImportError:
            QMessageBox.information(self, "ثبت خروج سریع", "ثبت خروج سریع - به زودی")

    def quick_assign_room(self):
        """تخصیص اتاق سریع"""
        self.show_room_assignment()

    def show_daily_report(self):
        """نمایش گزارش روزانه"""
        try:
            from app.services.reception.report_service import ReportService
            result = ReportService.generate_daily_occupancy_report()

            if result['success']:
                report_data = result['report']
                self.show_report_dialog("گزارش روزانه", report_data)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در ایجاد گزارش: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در نمایش گزارش روزانه: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ایجاد گزارش: {str(e)}")

    def show_financial_report(self):
        """نمایش گزارش مالی"""
        QMessageBox.information(self, "گزارش مالی", "گزارش مالی - به زودی")

    def show_user_settings(self):
        """نمایش تنظیمات کاربری"""
        QMessageBox.information(self, "تنظیمات کاربری", "تنظیمات کاربری - به زودی")

    def show_system_settings(self):
        """نمایش تنظیمات سیستم"""
        QMessageBox.information(self, "تنظیمات سیستم", "تنظیمات سیستم - به زودی")

    def show_report_dialog(self, title, report_data):
        """نمایش دیالوگ گزارش"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(600, 400)

        layout = QVBoxLayout()

        # نمایش گزارش
        text_edit = QTextEdit()
        text_edit.setPlainText(self.format_report_data(report_data))
        text_edit.setReadOnly(True)

        layout.addWidget(text_edit)

        # دکمه بستن
        btn_close = QPushButton("بستن")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)

        dialog.setLayout(layout)
        dialog.exec_()

    def format_report_data(self, report_data):
        """فرمت‌دهی داده‌های گزارش"""
        try:
            text = f"گزارش برای تاریخ: {report_data.get('report_date', '--')}\n"
            text += "=" * 50 + "\n\n"

            # خلاصه
            summary = report_data.get('summary', {})
            text += "خلاصه:\n"
            text += f"  - کل اتاق‌ها: {summary.get('total_rooms', 0)}\n"
            text += f"  - اتاق‌های اشغال: {summary.get('occupied_rooms', 0)}\n"
            text += f"  - اتاق‌های خالی: {summary.get('available_rooms', 0)}\n"
            text += f"  - نرخ اشغال: {summary.get('occupancy_rate', 0)}%\n"
            text += f"  - ورودهای امروز: {summary.get('arrivals_today', 0)}\n"
            text += f"  - خروج‌های امروز: {summary.get('departures_today', 0)}\n\n"

            return text

        except Exception as e:
            return f"خطا در فرمت‌دهی گزارش: {str(e)}"

    def show_about(self):
        """نمایش درباره سیستم"""
        about_text = f"""
        {config.app.app_name}
        نسخه: {config.app.version}

        طراح : ایمان جوادی نسب

        سیستم مدیریت پذیرش هتل
        طراحی شده برای مدیریت کامل فرآیندهای پذیرش

        توسعه‌یافته با Python و PyQt5

        ویژگی‌های اصلی:
        • مدیریت کامل مهمانان
        • مدیریت اتاق‌ها و وضعیت‌ها
        • سیستم پرداخت پیشرفته
        • گزارش‌گیری جامع
        • همگام‌سازی Real-time
        """

        QMessageBox.about(self, "درباره سیستم", about_text)

    def closeEvent(self, event):
        """هنگام بسته شدن برنامه"""
        reply = QMessageBox.question(
            self, 'تأیید خروج',
            'آیا از خروج از برنامه اطمینان دارید؟',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # توقف تایمرها
            self.stop_all_timers()
            event.accept()
        else:
            event.ignore()

    def stop_all_timers(self):
        """توقف تمام تایمرها"""
        self.status_timer.stop()

        # توقف تایمرهای ویجت‌ها
        widgets_to_check = [
            self.dashboard_widget,
            self.room_status_widget,
            self.guest_list_widget,
            self.room_list_widget,
            self.room_status_manager
        ]

        for widget in widgets_to_check:
            if hasattr(widget, 'auto_refresh_timer'):
                widget.auto_refresh_timer.stop()
            if hasattr(widget, 'refresh_timer'):
                widget.refresh_timer.stop()
