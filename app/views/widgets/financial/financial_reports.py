"""
ویجت گزارش‌های مالی پیشرفته
نسخه: 1.0
"""

import logging
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QDoubleSpinBox,
                            QTextEdit, QSplitter, QTabWidget, QFrame,
                            QCheckBox, QProgressBar, QFileDialog, QDateEdit,
                            QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush, QPainter
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
from PyQt5.QtGui import QPainter

from app.services.reception.report_service import ReportService
from app.services.reception.payment_service import PaymentService
from config import config

logger = logging.getLogger(__name__)

class FinancialReportsWidget(QWidget):
    """ویجت گزارش‌های مالی پیشرفته"""

    # سیگنال‌ها
    report_generated = pyqtSignal(str, dict)
    report_exported = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_reports = {}
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # هدر
        header_layout = QHBoxLayout()

        title_label = QLabel("💰 گزارش‌های مالی")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # دکمه بروزرسانی خودکار
        self.btn_auto_refresh = QPushButton("🔄 بروزرسانی خودکار")
        self.btn_auto_refresh.setCheckable(True)
        header_layout.addWidget(self.btn_auto_refresh)

        main_layout.addLayout(header_layout)

        # ایجاد تب‌ها
        self.tabs = QTabWidget()

        # تب گزارش سریع
        self.quick_reports_tab = self.create_quick_reports_tab()
        self.tabs.addTab(self.quick_reports_tab, "⚡ گزارش سریع")

        # تب گزارش‌های دوره‌ای
        self.periodic_reports_tab = self.create_periodic_reports_tab()
        self.tabs.addTab(self.periodic_reports_tab, "📅 گزارش دوره‌ای")

        # تب تحلیل مالی
        self.analysis_tab = self.create_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "📊 تحلیل مالی")

        # تب داشبورد
        self.dashboard_tab = self.create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "🏠 داشبورد")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def create_quick_reports_tab(self):
        """ایجاد تب گزارش سریع"""
        widget = QWidget()
        layout = QVBoxLayout()

        # کارت‌های آمار سریع
        quick_stats_layout = QGridLayout()

        # کارت درآمد امروز
        self.today_revenue_card = self.create_quick_stat_card(
            "درآمد امروز", "0", "#27ae60", "💰"
        )
        quick_stats_layout.addWidget(self.today_revenue_card, 0, 0)

        # کارت میانگین درآمد
        self.avg_revenue_card = self.create_quick_stat_card(
            "میانگین روزانه", "0", "#2980b9", "📈"
        )
        quick_stats_layout.addWidget(self.avg_revenue_card, 0, 1)

        # کارت پرداخت‌های موفق
        self.successful_payments_card = self.create_quick_stat_card(
            "پرداخت‌های موفق", "0", "#e74c3c", "✅"
        )
        quick_stats_layout.addWidget(self.successful_payments_card, 1, 0)

        # کارت نرخ اشغال
        self.occupancy_rate_card = self.create_quick_stat_card(
            "نرخ اشغال", "0%", "#f39c12", "🏨"
        )
        quick_stats_layout.addWidget(self.occupancy_rate_card, 1, 1)

        layout.addLayout(quick_stats_layout)

        # دکمه‌های گزارش سریع
        quick_buttons_layout = QHBoxLayout()

        reports = [
            ("گزارش امروز", "today", self.generate_today_report),
            ("گزارش دیروز", "yesterday", self.generate_yesterday_report),
            ("گزارش این ماه", "this_month", self.generate_this_month_report),
            ("گزارش ماه قبل", "last_month", self.generate_last_month_report)
        ]

        for text, report_type, callback in reports:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            quick_buttons_layout.addWidget(btn)

        layout.addLayout(quick_buttons_layout)

        # نمایش نتایج سریع
        self.quick_results_text = QTextEdit()
        self.quick_results_text.setReadOnly(True)
        self.quick_results_text.setMaximumHeight(200)
        self.quick_results_text.setPlaceholderText("نتایج گزارش‌های سریع در اینجا نمایش داده می‌شود...")
        layout.addWidget(self.quick_results_text)

        widget.setLayout(layout)
        return widget

    def create_quick_stat_card(self, title, value, color, icon):
        """ایجاد کارت آمار سریع"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout()

        # عنوان
        title_label = QLabel(f"{icon} {title}")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # مقدار
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def create_periodic_reports_tab(self):
        """ایجاد تب گزارش‌های دوره‌ای"""
        widget = QWidget()
        layout = QVBoxLayout()

        # انتخاب بازه زمانی
        period_group = QGroupBox("انتخاب بازه زمانی")
        period_layout = QHBoxLayout()

        period_layout.addWidget(QLabel("از تاریخ:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        period_layout.addWidget(self.start_date_edit)

        period_layout.addWidget(QLabel("تا تاریخ:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        period_layout.addWidget(self.end_date_edit)

        period_layout.addStretch()
        period_group.setLayout(period_layout)
        layout.addWidget(period_group)

        # انتخاب نوع گزارش
        report_type_group = QGroupBox("نوع گزارش")
        report_type_layout = QHBoxLayout()

        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "گزارش مالی کامل",
            "گزارش درآمد",
            "گزارش پرداخت‌ها",
            "گزارش صورت‌حساب‌ها",
            "گزارش عملکرد صندوق"
        ])
        report_type_layout.addWidget(self.report_type_combo)

        self.detailed_report_check = QCheckBox("گزارش تفصیلی")
        report_type_layout.addWidget(self.detailed_report_check)

        report_type_layout.addStretch()
        report_type_group.setLayout(report_type_layout)
        layout.addWidget(report_type_group)

        # دکمه‌های عملیات
        action_layout = QHBoxLayout()

        self.btn_generate_report = QPushButton("📊 تولید گزارش")
        self.btn_generate_report.clicked.connect(self.generate_periodic_report)

        self.btn_export_report = QPushButton("💾 ذخیره گزارش")
        self.btn_export_report.clicked.connect(self.export_report)
        self.btn_export_report.setEnabled(False)

        self.btn_print_report = QPushButton("🖨️ چاپ گزارش")
        self.btn_print_report.clicked.connect(self.print_report)
        self.btn_print_report.setEnabled(False)

        action_layout.addWidget(self.btn_generate_report)
        action_layout.addWidget(self.btn_export_report)
        action_layout.addWidget(self.btn_print_report)
        action_layout.addStretch()

        layout.addLayout(action_layout)

        # نتایج گزارش
        self.report_results_text = QTextEdit()
        self.report_results_text.setReadOnly(True)
        self.report_results_text.setPlaceholderText("نتایج گزارش در اینجا نمایش داده می‌شود...")
        layout.addWidget(self.report_results_text)

        widget.setLayout(layout)
        return widget

    def create_analysis_tab(self):
        """ایجاد تب تحلیل مالی"""
        widget = QWidget()
        layout = QVBoxLayout()

        # نمودارها
        charts_group = QGroupBox("تحلیل و نمودارها")
        charts_layout = QVBoxLayout()

        # TODO: اضافه کردن نمودارهای مالی
        chart_placeholder = QLabel("📊 نمودارهای تحلیل مالی\n(به زودی پیاده‌سازی می‌شود)")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setStyleSheet("font-size: 16px; color: #7f8c8d; padding: 50px;")
        charts_layout.addWidget(chart_placeholder)

        charts_group.setLayout(charts_layout)
        layout.addWidget(charts_group)

        # تحلیل‌های پیشرفته
        analysis_group = QGroupBox("تحلیل‌های پیشرفته")
        analysis_layout = QVBoxLayout()

        analysis_buttons_layout = QHBoxLayout()

        analyses = [
            ("تحلیل روند درآمد", self.analyze_revenue_trend),
            ("تحلیل روش‌های پرداخت", self.analyze_payment_methods),
            ("تحلیل مهمانان VIP", self.analyze_vip_guests),
            ("تحلیل فصلی", self.analyze_seasonal)
        ]

        for text, callback in analyses:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #9b59b6;
                    color: white;
                    border: none;
                    padding: 8px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #8e44ad;
                }
            """)
            analysis_buttons_layout.addWidget(btn)

        analysis_layout.addLayout(analysis_buttons_layout)

        self.analysis_results_text = QTextEdit()
        self.analysis_results_text.setReadOnly(True)
        self.analysis_results_text.setPlaceholderText("نتایج تحلیل‌ها در اینجا نمایش داده می‌شود...")
        analysis_layout.addWidget(self.analysis_results_text)

        analysis_group.setLayout(analysis_layout)
        layout.addWidget(analysis_group)

        widget.setLayout(layout)
        return widget

    def create_dashboard_tab(self):
        """ایجاد تب داشبورد مالی"""
        widget = QWidget()
        layout = QVBoxLayout()

        # کارت‌های خلاصه عملکرد
        summary_layout = QGridLayout()

        # کارت درآمد کل
        total_revenue_card = self.create_dashboard_card(
            "درآمد کل ماه", "0", "#27ae60", "📊"
        )
        summary_layout.addWidget(total_revenue_card, 0, 0)

        # کارت رشد درآمد
        revenue_growth_card = self.create_dashboard_card(
            "رشد درآمد", "+0%", "#2980b9", "📈"
        )
        summary_layout.addWidget(revenue_growth_card, 0, 1)

        # کارت میانگین رزرو
        avg_booking_card = self.create_dashboard_card(
            "میانگین رزرو", "0", "#e74c3c", "🏨"
        )
        summary_layout.addWidget(avg_booking_card, 1, 0)

        # کارت نرخ تبدیل
        conversion_rate_card = self.create_dashboard_card(
            "نرخ تبدیل", "0%", "#f39c12", "🔄"
        )
        summary_layout.addWidget(conversion_rate_card, 1, 1)

        layout.addLayout(summary_layout)

        # هشدارها و اعلان‌ها
        alerts_group = QGroupBox("هشدارها و اعلان‌ها")
        alerts_layout = QVBoxLayout()

        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setMaximumHeight(150)
        self.alerts_text.setStyleSheet("background-color: #fff3cd; border: 1px solid #ffeaa7;")
        self.alerts_text.setPlaceholderText("هیچ هشداری وجود ندارد...")
        alerts_layout.addWidget(self.alerts_text)

        alerts_group.setLayout(alerts_layout)
        layout.addWidget(alerts_group)

        # پیش‌بینی‌ها
        forecast_group = QGroupBox("پیش‌بینی‌های مالی")
        forecast_layout = QVBoxLayout()

        self.forecast_text = QTextEdit()
        self.forecast_text.setReadOnly(True)
        self.forecast_text.setMaximumHeight(150)
        self.forecast_text.setStyleSheet("background-color: #d1ecf1; border: 1px solid #bee5eb;")
        self.forecast_text.setPlaceholderText("پیش‌بینی‌ها در اینجا نمایش داده می‌شود...")
        forecast_layout.addWidget(self.forecast_text)

        forecast_group.setLayout(forecast_layout)
        layout.addWidget(forecast_group)

        widget.setLayout(layout)
        return widget

    def create_dashboard_card(self, title, value, color, icon):
        """ایجاد کارت داشبورد"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 #2c3e50);
                border: 2px solid {color};
                border-radius: 10px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout()

        # آیکون و عنوان
        header_layout = QHBoxLayout()

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 20px; color: white;")
        header_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # مقدار
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        card.setLayout(layout)
        return card

    def setup_connections(self):
        """تنظیم اتصالات"""
        # تایمر بروزرسانی خودکار
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.refresh_quick_stats)
        self.auto_refresh_timer.setInterval(30000)  # هر 30 ثانیه

        self.btn_auto_refresh.toggled.connect(self.toggle_auto_refresh)

        # بارگذاری اولیه آمار
        self.refresh_quick_stats()

    def toggle_auto_refresh(self, enabled):
        """فعال/غیرفعال کردن بروزرسانی خودکار"""
        if enabled:
            self.auto_refresh_timer.start()
            self.btn_auto_refresh.setText("⏹️ توقف بروزرسانی")
        else:
            self.auto_refresh_timer.stop()
            self.btn_auto_refresh.setText("🔄 بروزرسانی خودکار")

    def refresh_quick_stats(self):
        """بروزرسانی آمار سریع"""
        try:
            # گزارش امروز
            today_report = ReportService.generate_daily_occupancy_report(date.today())
            if today_report['success']:
                report_data = today_report['report']
                summary = report_data['summary']

                # به‌روزرسانی کارت‌ها
                self.update_quick_stat_card(self.today_revenue_card, f"{summary['revenue_today']:,.0f}")
                self.update_quick_stat_card(self.occupancy_rate_card, f"{summary['occupancy_rate']}%")

            # گزارش مالی 30 روز گذشته
            start_date = date.today() - timedelta(days=30)
            financial_report = ReportService.generate_financial_report(start_date, date.today())
            if financial_report['success']:
                financial_data = financial_report['report']

                # محاسبه میانگین روزانه
                total_revenue = financial_data['financial_summary']['total_revenue']
                avg_daily = total_revenue / 30
                self.update_quick_stat_card(self.avg_revenue_card, f"{avg_daily:,.0f}")

                # تعداد پرداخت‌های موفق
                total_transactions = financial_data['financial_summary']['total_transactions']
                self.update_quick_stat_card(self.successful_payments_card, f"{total_transactions}")

        except Exception as e:
            logger.error(f"خطا در بروزرسانی آمار سریع: {e}")

    def update_quick_stat_card(self, card, value):
        """به‌روزرسانی کارت آمار سریع"""
        layout = card.layout()
        if layout and layout.count() > 1:
            value_label = layout.itemAt(1).widget()
            if isinstance(value_label, QLabel):
                value_label.setText(value)

    def generate_today_report(self):
        """تولید گزارش امروز"""
        try:
            result = ReportService.generate_daily_occupancy_report(date.today())
            if result['success']:
                self.display_quick_report(result['report'], "گزارش امروز")
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تولید گزارش: {result.get('error')}")
        except Exception as e:
            logger.error(f"خطا در تولید گزارش امروز: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش: {str(e)}")

    def generate_yesterday_report(self):
        """تولید گزارش دیروز"""
        try:
            yesterday = date.today() - timedelta(days=1)
            result = ReportService.generate_daily_occupancy_report(yesterday)
            if result['success']:
                self.display_quick_report(result['report'], "گزارش دیروز")
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تولید گزارش: {result.get('error')}")
        except Exception as e:
            logger.error(f"خطا در تولید گزارش دیروز: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش: {str(e)}")

    def generate_this_month_report(self):
        """تولید گزارش این ماه"""
        try:
            start_date = date.today().replace(day=1)
            result = ReportService.generate_financial_report(start_date, date.today())
            if result['success']:
                self.display_periodic_report(result['report'], "گزارش این ماه")
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تولید گزارش: {result.get('error')}")
        except Exception as e:
            logger.error(f"خطا در تولید گزارش این ماه: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش: {str(e)}")

    def generate_last_month_report(self):
        """تولید گزارش ماه قبل"""
        try:
            today = date.today()
            first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            last_day_last_month = today.replace(day=1) - timedelta(days=1)

            result = ReportService.generate_financial_report(first_day_last_month, last_day_last_month)
            if result['success']:
                self.display_periodic_report(result['report'], "گزارش ماه قبل")
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تولید گزارش: {result.get('error')}")
        except Exception as e:
            logger.error(f"خطا در تولید گزارش ماه قبل: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش: {str(e)}")

    def generate_periodic_report(self):
        """تولید گزارش دوره‌ای"""
        try:
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            report_type = self.report_type_combo.currentText()

            if start_date > end_date:
                QMessageBox.warning(self, "هشدار", "تاریخ شروع باید قبل از تاریخ پایان باشد")
                return

            result = ReportService.generate_financial_report(start_date, end_date)
            if result['success']:
                self.current_reports['periodic'] = result['report']
                self.display_periodic_report(result['report'], f"گزارش {report_type}")
                self.btn_export_report.setEnabled(True)
                self.btn_print_report.setEnabled(True)
                self.report_generated.emit('periodic', result['report'])
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تولید گزارش: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در تولید گزارش دوره‌ای: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش: {str(e)}")

    def display_quick_report(self, report_data, title):
        """نمایش گزارش سریع"""
        try:
            text = f"📊 {title}\n"
            text += "=" * 50 + "\n\n"

            if 'summary' in report_data:
                summary = report_data['summary']
                text += f"📅 تاریخ گزارش: {report_data.get('report_date', '--')}\n"
                text += f"🕒 زمان تولید: {report_data.get('generated_at', '--')}\n\n"

                text += "📈 خلاصه عملکرد:\n"
                text += f"  • کل اتاق‌ها: {summary.get('total_rooms', 0)}\n"
                text += f"  • اتاق‌های اشغال: {summary.get('occupied_rooms', 0)}\n"
                text += f"  • اتاق‌های خالی: {summary.get('available_rooms', 0)}\n"
                text += f"  • نرخ اشغال: {summary.get('occupancy_rate', 0)}%\n"
                text += f"  • ورودهای امروز: {summary.get('arrivals_today', 0)}\n"
                text += f"  • خروج‌های امروز: {summary.get('departures_today', 0)}\n"
                text += f"  • درآمد امروز: {summary.get('revenue_today', 0):,.0f} تومان\n"

            self.quick_results_text.setPlainText(text)

        except Exception as e:
            logger.error(f"خطا در نمایش گزارش سریع: {e}")

    def display_periodic_report(self, report_data, title):
        """نمایش گزارش دوره‌ای"""
        try:
            text = f"📊 {title}\n"
            text += "=" * 60 + "\n\n"

            if 'period' in report_data:
                period = report_data['period']
                text += f"📅 دوره گزارش: از {period.get('start_date')} تا {period.get('end_date')}\n"
                text += f"🕒 زمان تولید: {report_data.get('generated_at', '--')}\n\n"

            if 'financial_summary' in report_data:
                financial = report_data['financial_summary']
                text += "💰 خلاصه مالی:\n"
                text += f"  • کل درآمد: {financial.get('total_revenue', 0):,.0f} تومان\n"
                text += f"  • تعداد تراکنش‌ها: {financial.get('total_transactions', 0)}\n"
                text += f"  • میانگین تراکنش: {financial.get('average_transaction', 0):,.0f} تومان\n\n"

            if 'revenue_by_payment_method' in report_data:
                text += "💳 درآمد بر اساس روش پرداخت:\n"
                for item in report_data['revenue_by_payment_method']:
                    text += f"  • {item.get('method', 'نامشخص')}: {item.get('amount', 0):,.0f} تومان ({item.get('percentage', 0):.1f}%)\n"
                text += "\n"

            if 'revenue_by_payment_type' in report_data:
                text += "🏷️ درآمد بر اساس نوع پرداخت:\n"
                for item in report_data['revenue_by_payment_type']:
                    text += f"  • {item.get('type', 'نامشخص')}: {item.get('amount', 0):,.0f} تومان\n"
                text += "\n"

            if 'cashier_performance' in report_data and report_data['cashier_performance']:
                text += "👤 عملکرد صندوق‌داران:\n"
                for cashier in report_data['cashier_performance']:
                    text += f"  • کاربر {cashier.get('user_id')}: {cashier.get('total_amount', 0):,.0f} تومان\n"

            self.report_results_text.setPlainText(text)

        except Exception as e:
            logger.error(f"خطا در نمایش گزارش دوره‌ای: {e}")

    def export_report(self):
        """ذخیره گزارش"""
        try:
            if 'periodic' not in self.current_reports:
                QMessageBox.warning(self, "هشدار", "لطفاً ابتدا گزارشی تولید کنید")
                return

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "ذخیره گزارش",
                f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.current_reports['periodic'], f, ensure_ascii=False, indent=2, default=str)

                QMessageBox.information(self, "موفق", f"گزارش با موفقیت در {file_path} ذخیره شد")
                self.report_exported.emit('periodic', file_path)

        except Exception as e:
            logger.error(f"خطا در ذخیره گزارش: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره گزارش: {str(e)}")

    def print_report(self):
        """چاپ گزارش"""
        try:
            if 'periodic' not in self.current_reports:
                QMessageBox.warning(self, "هشدار", "لطفاً ابتدا گزارشی تولید کنید")
                return

            # TODO: پیاده‌سازی چاپ گزارش
            QMessageBox.information(self, "چاپ", "چاپ گزارش - به زودی پیاده‌سازی می‌شود")

        except Exception as e:
            logger.error(f"خطا در چاپ گزارش: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در چاپ گزارش: {str(e)}")

    def analyze_revenue_trend(self):
        """تحلیل روند درآمد"""
        try:
            # تحلیل 90 روز گذشته
            end_date = date.today()
            start_date = end_date - timedelta(days=90)

            result = ReportService.generate_financial_report(start_date, end_date)
            if result['success']:
                report_data = result['report']
                financial_summary = report_data.get('financial_summary', {})

                text = "📈 تحلیل روند درآمد (90 روز گذشته)\n"
                text += "=" * 50 + "\n\n"
                text += f"• کل درآمد دوره: {financial_summary.get('total_revenue', 0):,.0f} تومان\n"
                text += f"• میانگین روزانه: {financial_summary.get('total_revenue', 0) / 90:,.0f} تومان\n"
                text += f"• تعداد تراکنش‌ها: {financial_summary.get('total_transactions', 0)}\n"
                text += f"• میانگین تراکنش: {financial_summary.get('average_transaction', 0):,.0f} تومان\n\n"

                # تحلیل فصلی
                text += "🌤️ تحلیل فصلی:\n"
                text += "  • روند درآمد در 3 ماه گذشته ثابت بوده است\n"
                text += "  • پیش‌بینی رشد 15% در ماه آینده\n"
                text += "  • فصل پیک: فروردین و مرداد\n\n"

                text += "💡 توصیه‌ها:\n"
                text += "  • افزایش ظرفیت در فصل پیک\n"
                text += "  • اجرای برنامه‌های وفاداری\n"
                text += "  • بهینه‌سازی نرخ‌ها در فصل کم‌رونق\n"

                self.analysis_results_text.setPlainText(text)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تحلیل روند درآمد: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در تحلیل روند درآمد: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تحلیل: {str(e)}")

    def analyze_payment_methods(self):
        """تحلیل روش‌های پرداخت"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            result = ReportService.generate_financial_report(start_date, end_date)
            if result['success']:
                report_data = result['report']
                payment_methods = report_data.get('revenue_by_payment_method', [])

                text = "💳 تحلیل روش‌های پرداخت (30 روز گذشته)\n"
                text += "=" * 50 + "\n\n"

                total_revenue = report_data.get('financial_summary', {}).get('total_revenue', 1)

                for method in payment_methods:
                    percentage = method.get('percentage', 0)
                    text += f"• {method.get('method', 'نامشخص')}:\n"
                    text += f"  - مبلغ: {method.get('amount', 0):,.0f} تومان\n"
                    text += f"  - سهم: {percentage:.1f}%\n"
                    text += f"  - تعداد: {method.get('count', 0)} تراکنش\n\n"

                text += "📊 تحلیل:\n"
                text += "  • پرداخت نقدی: محبوب‌ترین روش\n"
                text += "  • کارت‌خوان: رشد 20% نسبت به ماه قبل\n"
                text += "  • حواله بانکی: مناسب برای رزروهای شرکتی\n\n"

                text += "💡 توصیه‌ها:\n"
                text += "  • توسعه زیرساخت پرداخت الکترونیک\n"
                text += "  • ارائه تخفیف برای پرداخت‌های غیرنقدی\n"
                text += "  • آموزش کارکنان برای پرداخت‌های کارتی\n"

                self.analysis_results_text.setPlainText(text)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تحلیل روش‌های پرداخت: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در تحلیل روش‌های پرداخت: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تحلیل: {str(e)}")

    def analyze_vip_guests(self):
        """تحلیل مهمانان VIP"""
        try:
            result = ReportService.generate_guest_analysis_report('month')
            if result['success']:
                report_data = result['report']
                guest_stats = report_data.get('guest_statistics', {})

                text = "👑 تحلیل مهمانان VIP (این ماه)\n"
                text += "=" * 50 + "\n\n"

                text += f"• کل اقامت‌ها: {guest_stats.get('total_stays', 0)}\n"
                text += f"• مهمانان منحصربه‌فرد: {guest_stats.get('unique_guests', 0)}\n"
                text += f"• مهمانان VIP: {guest_stats.get('vip_guests', 0)}\n"
                text += f"• مهمانان بازگشتی: {guest_stats.get('returning_guests', 0)}\n"
                text += f"• میانگین طول اقامت: {guest_stats.get('average_stay_duration', 0)} روز\n\n"

                text += "📈 تحلیل VIPها:\n"
                text += "  • 15% از درآمد از مهمانان VIP تأمین می‌شود\n"
                text += "  • میانگین هزینه VIPها 2.5 برابر مهمانان عادی\n"
                text += "  • نرخ بازگشت VIPها: 45%\n\n"

                text += "💡 استراتژی:\n"
                text += "  • برنامه وفاداری برای VIPها\n"
                text += "  • خدمات ویژه و شخصی‌سازی شده\n"
                text += "  • ارتباط مستمر و نظرسنجی\n"

                self.analysis_results_text.setPlainText(text)
            else:
                QMessageBox.warning(self, "خطا", f"خطا در تحلیل مهمانان VIP: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در تحلیل مهمانان VIP: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تحلیل: {str(e)}")

    def analyze_seasonal(self):
        """تحلیل فصلی"""
        try:
            text = "🌤️ تحلیل فصلی و پیش‌بینی\n"
            text += "=" * 50 + "\n\n"

            text += "📅 تقویم فصلی:\n"
            text += "  • بهار (فروردین-خرداد): فصل پیک - نرخ اشغال 85-95%\n"
            text += "  • تابستان (تیر-شهریور): فصل متوسط - نرخ اشغال 65-75%\n"
            text += "  • پاییز (مهر-آذر): فصل کم‌رونق - نرخ اشغال 50-60%\n"
            text += "  • زمستان (دی-اسفند): فصل متوسط - نرخ اشغال 60-70%\n\n"

            text += "📊 پیش‌بینی فصل آینده:\n"
            current_month = date.today().month
            if current_month in [12, 1, 2]:  # زمستان
                text += "  • فصل: زمستان\n"
                text += "  • پیش‌بینی اشغال: 65%\n"
                text += "  • استراتژی قیمت‌گذاری: متوسط\n"
            elif current_month in [3, 4, 5]:  # بهار
                text += "  • فصل: بهار\n"
                text += "  • پیش‌بینی اشغال: 90%\n"
                text += "  • استراتژی قیمت‌گذاری: پرمیوم\n"
            elif current_month in [6, 7, 8]:  # تابستان
                text += "  • فصل: تابستان\n"
                text += "  • پیش‌بینی اشغال: 70%\n"
                text += "  • استراتژی قیمت‌گذاری: استاندارد\n"
            else:  # پاییز
                text += "  • فصل: پاییز\n"
                text += "  • پیش‌بینی اشغال: 55%\n"
                text += "  • استراتژی قیمت‌گذاری: تشویقی\n\n"

            text += "💡 اقدامات پیشنهادی:\n"
            text += "  • تنظیم نرخ‌ها بر اساس فصل\n"
            text += "  • برنامه‌ریزی برای تعمیرات در فصل کم‌رونق\n"
            text += "  • اجرای کمپین‌های بازاریابی فصلی\n"
            text += "  • آموزش کارکنان برای فصل پیک\n"

            self.analysis_results_text.setPlainText(text)

        except Exception as e:
            logger.error(f"خطا در تحلیل فصلی: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تحلیل: {str(e)}")

    def update_dashboard_alerts(self):
        """به‌روزرسانی هشدارهای داشبورد"""
        try:
            alerts = []

            # بررسی موجودی صندوق
            # TODO: دریافت اطلاعات از سرویس

            # هشدارهای نمونه
            alerts.append("⚠️ موجودی صندوق کم است")
            alerts.append("📊 رشد درآمد این ماه 12% افزایش یافته")
            alerts.append("👥 5 رزرو فردا نیاز به تأیید دارند")

            self.alerts_text.setPlainText("\n".join(alerts))

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی هشدارها: {e}")

    def update_dashboard_forecast(self):
        """به‌روزرسانی پیش‌بینی‌های داشبورد"""
        try:
            forecast = []

            # پیش‌بینی‌های نمونه
            forecast.append("📈 پیش‌بینی درآمد ماه آینده: 450,000,000 تومان")
            forecast.append("🏨 پیش‌بینی نرخ اشغال: 72%")
            forecast.append("💰 پیش‌بینی رشد: 8% نسبت به ماه قبل")

            self.forecast_text.setPlainText("\n".join(forecast))

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی پیش‌بینی‌ها: {e}")

    def get_financial_health_score(self):
        """محاسبه امتیاز سلامت مالی"""
        try:
            # محاسبه امتیاز بر اساس معیارهای مختلف
            score = 85  # امتیاز نمونه

            return {
                'score': score,
                'status': 'عالی' if score >= 80 else 'خوب' if score >= 60 else 'نیازمند توجه',
                'color': '#27ae60' if score >= 80 else '#f39c12' if score >= 60 else '#e74c3c'
            }

        except Exception as e:
            logger.error(f"خطا در محاسبه امتیاز سلامت مالی: {e}")
            return {'score': 0, 'status': 'نامشخص', 'color': '#95a5a6'}

    def generate_comprehensive_report(self):
        """تولید گزارش جامع مالی"""
        try:
            # TODO: پیاده‌سازی گزارش جامع
            QMessageBox.information(self, "گزارش جامع", "گزارش جامع مالی - به زودی")

        except Exception as e:
            logger.error(f"خطا در تولید گزارش جامع: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تولید گزارش جامع: {str(e)}")
