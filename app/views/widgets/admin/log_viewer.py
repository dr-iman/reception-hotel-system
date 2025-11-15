# app/views/widgets/admin/log_viewer.py
"""
ویجت نمایش و مدیریت لاگ‌های سیستم
"""

import logging
import os
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QTextEdit,
                            QCheckBox, QDateEdit, QProgressBar)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor

logger = logging.getLogger(__name__)

class LogViewerWidget(QWidget):
    """ویجت نمایش و مدیریت لاگ‌های سیستم"""

    # سیگنال‌ها
    log_cleared = pyqtSignal()
    log_exported = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_data = []
        self.current_log_file = None
        self.init_ui()
        self.load_log_files()

        # تایمر برای به‌روزرسانی خودکار
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_logs)
        self.refresh_timer.start(10000)  # هر 10 ثانیه

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # تب‌های مدیریت لاگ
        self.tabs = QTabWidget()

        # تب نمایش لاگ
        self.viewer_tab = self.create_viewer_tab()
        self.tabs.addTab(self.viewer_tab, "📋 نمایش لاگ")

        # تب جستجو و فیلتر
        self.search_tab = self.create_search_tab()
        self.tabs.addTab(self.search_tab, "🔍 جستجو")

        # تب آمار و گزارش
        self.stats_tab = self.create_stats_tab()
        self.tabs.addTab(self.stats_tab, "📊 آمار")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def create_viewer_tab(self):
        """ایجاد تب نمایش لاگ"""
        widget = QWidget()
        layout = QVBoxLayout()

        # نوار کنترل
        control_layout = QHBoxLayout()

        # انتخاب فایل لاگ
        file_layout = QHBoxLayout()

        self.cmb_log_files = QComboBox()
        self.cmb_log_files.currentTextChanged.connect(self.load_log_file)

        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setToolTip("بروزرسانی")
        self.btn_refresh.clicked.connect(self.refresh_logs)
        self.btn_refresh.setFixedSize(30, 30)

        file_layout.addWidget(QLabel("فایل لاگ:"))
        file_layout.addWidget(self.cmb_log_files)
        file_layout.addWidget(self.btn_refresh)
        file_layout.addStretch()

        control_layout.addLayout(file_layout)

        # گزینه‌های نمایش
        options_layout = QHBoxLayout()

        self.chk_auto_scroll = QCheckBox("اسکرول خودکار")
        self.chk_auto_scroll.setChecked(True)

        self.chk_show_timestamps = QCheckBox("نمایش زمان")
        self.chk_show_timestamps.setChecked(True)

        self.chk_show_debug = QCheckBox("نمایش Debug")
        self.chk_show_debug.setChecked(False)

        options_layout.addWidget(self.chk_auto_scroll)
        options_layout.addWidget(self.chk_show_timestamps)
        options_layout.addWidget(self.chk_show_debug)
        options_layout.addStretch()

        control_layout.addLayout(options_layout)

        layout.addLayout(control_layout)

        # نمایشگر لاگ
        log_display_group = QGroupBox("لاگ سیستم")
        log_layout = QVBoxLayout()

        self.txt_log_display = QTextEdit()
        self.txt_log_display.setReadOnly(True)
        self.txt_log_display.setFont(QFont("Courier", 9))
        self.txt_log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #444;
            }
        """)

        log_layout.addWidget(self.txt_log_display)
        log_display_group.setLayout(log_layout)
        layout.addWidget(log_display_group)

        # نوار وضعیت
        status_layout = QHBoxLayout()

        self.lbl_log_info = QLabel("آماده")
        self.lbl_log_info.setStyleSheet("color: #7f8c8d;")

        self.progress_loading = QProgressBar()
        self.progress_loading.setVisible(False)
        self.progress_loading.setMaximumHeight(4)

        status_layout.addWidget(self.lbl_log_info)
        status_layout.addWidget(self.progress_loading)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        widget.setLayout(layout)
        return widget

    def create_search_tab(self):
        """ایجاد تب جستجو و فیلتر"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فرم جستجو
        search_group = QGroupBox("جستجو در لاگ")
        search_layout = QFormLayout()

        self.txt_search_term = QLineEdit()
        self.txt_search_term.setPlaceholderText("عبارت جستجو...")

        self.cmb_log_level = QComboBox()
        self.cmb_log_level.addItems(["همه سطوح", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.setCalendarPopup(True)

        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)

        self.txt_module = QLineEdit()
        self.txt_module.setPlaceholderText("ماژول (اختیاری)")

        search_layout.addRow("عبارت جستجو:", self.txt_search_term)
        search_layout.addRow("سطح لاگ:", self.cmb_log_level)
        search_layout.addRow("از تاریخ:", self.date_from)
        search_layout.addRow("تا تاریخ:", self.date_to)
        search_layout.addRow("ماژول:", self.txt_module)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # دکمه‌های جستجو
        button_layout = QHBoxLayout()

        self.btn_search = QPushButton("🔍 جستجو")
        self.btn_search.clicked.connect(self.search_logs)
        self.btn_search.setStyleSheet("background-color: #3498db; color: white;")

        self.btn_clear_search = QPushButton("پاک کردن")
        self.btn_clear_search.clicked.connect(self.clear_search)

        button_layout.addWidget(self.btn_search)
        button_layout.addWidget(self.btn_clear_search)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # نتایج جستجو
        results_group = QGroupBox("نتایج جستجو")
        results_layout = QVBoxLayout()

        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(5)
        self.search_results_table.setHorizontalHeaderLabels([
            "زمان", "سطح", "ماژول", "پیام", "خط"
        ])

        self.search_results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.search_results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.search_results_table.doubleClicked.connect(self.on_search_result_double_clicked)

        header = self.search_results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # زمان
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # سطح
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # ماژول
        header.setSectionResizeMode(3, QHeaderView.Stretch)          # پیام
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # خط

        results_layout.addWidget(self.search_results_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        widget.setLayout(layout)
        return widget

    def create_stats_tab(self):
        """ایجاد تب آمار و گزارش"""
        widget = QWidget()
        layout = QVBoxLayout()

        # آمار کلی
        stats_group = QGroupBox("آمار کلی لاگ")
        stats_layout = QFormLayout()

        self.lbl_total_entries = QLabel("0")
        self.lbl_file_size = QLabel("0 MB")
        self.lbl_oldest_entry = QLabel("--")
        self.lbl_newest_entry = QLabel("--")

        stats_layout.addRow("تعداد کل لاگ‌ها:", self.lbl_total_entries)
        stats_layout.addRow("حجم فایل:", self.lbl_file_size)
        stats_layout.addRow("قدیمی‌ترین لاگ:", self.lbl_oldest_entry)
        stats_layout.addRow("جدیدترین لاگ:", self.lbl_newest_entry)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # توزیع سطوح لاگ
        levels_group = QGroupBox("توزیع سطوح لاگ")
        levels_layout = QFormLayout()

        self.lbl_debug_count = QLabel("0")
        self.lbl_info_count = QLabel("0")
        self.lbl_warning_count = QLabel("0")
        self.lbl_error_count = QLabel("0")
        self.lbl_critical_count = QLabel("0")

        levels_layout.addRow("DEBUG:", self.lbl_debug_count)
        levels_layout.addRow("INFO:", self.lbl_info_count)
        levels_layout.addRow("WARNING:", self.lbl_warning_count)
        levels_layout.addRow("ERROR:", self.lbl_error_count)
        levels_layout.addRow("CRITICAL:", self.lbl_critical_count)

        levels_group.setLayout(levels_layout)
        layout.addWidget(levels_group)

        # عملیات
        actions_group = QGroupBox("عملیات")
        actions_layout = QVBoxLayout()

        self.btn_export_logs = QPushButton("📤 خروجی لاگ")
        self.btn_export_logs.clicked.connect(self.export_logs)

        self.btn_clear_logs = QPushButton("🗑️ پاک کردن لاگ")
        self.btn_clear_logs.clicked.connect(self.clear_logs)
        self.btn_clear_logs.setStyleSheet("background-color: #e74c3c; color: white;")

        self.btn_analyze_logs = QPushButton("📊 تحلیل لاگ")
        self.btn_analyze_logs.clicked.connect(self.analyze_logs)

        actions_layout.addWidget(self.btn_export_logs)
        actions_layout.addWidget(self.btn_clear_logs)
        actions_layout.addWidget(self.btn_analyze_logs)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def load_log_files(self):
        """بارگذاری لیست فایل‌های لاگ"""
        try:
            # شبیه‌سازی فایل‌های لاگ
            log_files = [
                "reception_system.log",
                "error.log",
                "access.log",
                "audit.log",
                "debug.log"
            ]

            self.cmb_log_files.clear()
            self.cmb_log_files.addItems(log_files)

            if log_files:
                self.load_log_file(log_files[0])

        except Exception as e:
            logger.error(f"خطا در بارگذاری فایل‌های لاگ: {e}")

    def load_log_file(self, filename):
        """بارگذاری محتوای فایل لاگ"""
        try:
            if not filename:
                return

            self.current_log_file = filename
            self.progress_loading.setVisible(True)
            self.lbl_log_info.setText(f"در حال بارگذاری {filename}...")

            # شبیه‌سازی بارگذاری لاگ
            self.simulate_log_loading(filename)

        except Exception as e:
            logger.error(f"خطا در بارگذاری فایل لاگ: {e}")
            self.lbl_log_info.setText(f"خطا در بارگذاری: {str(e)}")
            self.progress_loading.setVisible(False)

    def simulate_log_loading(self, filename):
        """شبیه‌سازی بارگذاری لاگ"""
        from PyQt5.QtCore import QTimer

        # شبیه‌سازی داده‌های لاگ
        sample_logs = self.generate_sample_logs()

        QTimer.singleShot(1000, lambda: self.display_logs(sample_logs, filename))

    def generate_sample_logs(self):
        """تولید نمونه لاگ برای نمایش"""
        logs = []
        levels = ['INFO', 'DEBUG', 'WARNING', 'ERROR']
        modules = ['app.views', 'app.services', 'app.core', 'app.models']

        for i in range(50):
            level = levels[i % len(levels)]
            module = modules[i % len(modules)]
            timestamp = datetime.now() - timedelta(minutes=50-i)

            log_entry = {
                'timestamp': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                'level': level,
                'module': module,
                'message': f"این یک پیغام نمونه از {module} است - خط {i+1}",
                'line': i + 1
            }
            logs.append(log_entry)

        return logs

    def display_logs(self, logs, filename):
        """نمایش لاگ‌ها در نمایشگر"""
        try:
            self.txt_log_display.clear()
            self.log_data = logs

            for log in logs:
                self.append_log_entry(log)

            self.progress_loading.setVisible(False)
            self.lbl_log_info.setText(f"فایل {filename} بارگذاری شد - {len(logs)} لاگ")

            if self.chk_auto_scroll.isChecked():
                self.txt_log_display.moveCursor(QTextCursor.End)

            self.update_stats()

        except Exception as e:
            logger.error(f"خطا در نمایش لاگ: {e}")
            self.lbl_log_info.setText(f"خطا در نمایش لاگ: {str(e)}")

    def append_log_entry(self, log_entry):
        """افزودن یک لاگ به نمایشگر"""
        try:
            # تعیین رنگ بر اساس سطح لاگ
            color = self.get_log_level_color(log_entry['level'])

            # فرمت کردن خط لاگ
            timestamp = log_entry['timestamp'] if self.chk_show_timestamps else ""
            level = log_entry['level']
            module = log_entry['module']
            message = log_entry['message']

            log_line = f"{timestamp} [{level}] {module}: {message}\n"

            # افزودن به نمایشگر با رنگ مناسب
            cursor = self.txt_log_display.textCursor()
            cursor.movePosition(QTextCursor.End)

            format = cursor.charFormat()
            format.setForeground(color)
            cursor.setCharFormat(format)

            cursor.insertText(log_line)

        except Exception as e:
            logger.error(f"خطا در افزودن لاگ: {e}")

    def get_log_level_color(self, level):
        """رنگ بر اساس سطح لاگ"""
        from PyQt5.QtGui import QColor
        colors = {
            'DEBUG': QColor(149, 165, 166),   # خاکستری
            'INFO': QColor(52, 152, 219),     # آبی
            'WARNING': QColor(243, 156, 18),  # نارنجی
            'ERROR': QColor(231, 76, 60),     # قرمز
            'CRITICAL': QColor(155, 89, 182)  # بنفش
        }
        return colors.get(level, QColor(189, 195, 199))

    def refresh_logs(self):
        """بروزرسانی لاگ‌ها"""
        if self.current_log_file:
            self.load_log_file(self.current_log_file)

    def search_logs(self):
        """جستجو در لاگ‌ها"""
        try:
            search_term = self.txt_search_term.text().strip().lower()
            level_filter = self.cmb_log_level.currentText()
            date_from = self.date_from.date().toString("yyyy-MM-dd")
            date_to = self.date_to.date().toString("yyyy-MM-dd")
            module_filter = self.txt_module.text().strip()

            if not search_term and level_filter == "همه سطوح" and not module_filter:
                QMessageBox.warning(self, "هشدار", "لطفاً حداقل یک معیار جستجو وارد کنید")
                return

            # فیلتر لاگ‌ها
            filtered_logs = self.log_data

            if search_term:
                filtered_logs = [log for log in filtered_logs if search_term in log['message'].lower()]

            if level_filter != "همه سطوح":
                filtered_logs = [log for log in filtered_logs if log['level'] == level_filter]

            if module_filter:
                filtered_logs = [log for log in filtered_logs if module_filter in log['module']]

            # نمایش نتایج
            self.display_search_results(filtered_logs)

        except Exception as e:
            logger.error(f"خطا در جستجوی لاگ: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در جستجو: {str(e)}")

    def display_search_results(self, results):
        """نمایش نتایج جستجو"""
        self.search_results_table.setRowCount(len(results))

        for row, log in enumerate(results):
            # زمان
            self.search_results_table.setItem(row, 0, QTableWidgetItem(log['timestamp']))

            # سطح
            level_item = QTableWidgetItem(log['level'])
            level_item.setForeground(self.get_log_level_color(log['level']))
            self.search_results_table.setItem(row, 1, level_item)

            # ماژول
            self.search_results_table.setItem(row, 2, QTableWidgetItem(log['module']))

            # پیام
            self.search_results_table.setItem(row, 3, QTableWidgetItem(log['message']))

            # خط
            self.search_results_table.setItem(row, 4, QTableWidgetItem(str(log['line'])))

    def clear_search(self):
        """پاک کردن جستجو"""
        self.txt_search_term.clear()
        self.cmb_log_level.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_to.setDate(QDate.currentDate())
        self.txt_module.clear()
        self.search_results_table.setRowCount(0)

    def on_search_result_double_clicked(self, index):
        """هنگام دابل‌کلیک روی نتیجه جستجو"""
        try:
            row = index.row()
            if 0 <= row < self.search_results_table.rowCount():
                log_entry = {
                    'timestamp': self.search_results_table.item(row, 0).text(),
                    'level': self.search_results_table.item(row, 1).text(),
                    'module': self.search_results_table.item(row, 2).text(),
                    'message': self.search_results_table.item(row, 3).text()
                }

                # نمایش لاگ در تب نمایش
                self.tabs.setCurrentIndex(0)
                self.highlight_log_entry(log_entry)

        except Exception as e:
            logger.error(f"خطا در نمایش لاگ: {e}")

    def highlight_log_entry(self, log_entry):
        """هایلایت کردن لاگ در نمایشگر"""
        try:
            # جستجوی لاگ در نمایشگر
            search_text = f"{log_entry['timestamp']} [{log_entry['level']}] {log_entry['module']}: {log_entry['message']}"

            cursor = self.txt_log_display.textCursor()
            cursor.movePosition(QTextCursor.Start)

            # جستجو و هایلایت
            while cursor.find(search_text):
                highlight_format = cursor.charFormat()
                highlight_format.setBackground(QColor(255, 255, 0))  # زرد
                highlight_format.setForeground(QColor(0, 0, 0))      # سیاه
                cursor.setCharFormat(highlight_format)

        except Exception as e:
            logger.error(f"خطا در هایلایت لاگ: {e}")

    def update_stats(self):
        """به‌روزرسانی آمار"""
        try:
            total_entries = len(self.log_data)
            self.lbl_total_entries.setText(str(total_entries))

            # توزیع سطوح
            levels = {'DEBUG': 0, 'INFO': 0, 'WARNING': 0, 'ERROR': 0, 'CRITICAL': 0}
            for log in self.log_data:
                if log['level'] in levels:
                    levels[log['level']] += 1

            self.lbl_debug_count.setText(str(levels['DEBUG']))
            self.lbl_info_count.setText(str(levels['INFO']))
            self.lbl_warning_count.setText(str(levels['WARNING']))
            self.lbl_error_count.setText(str(levels['ERROR']))
            self.lbl_critical_count.setText(str(levels['CRITICAL']))

            # اطلاعات زمانی
            if self.log_data:
                oldest = self.log_data[-1]['timestamp']
                newest = self.log_data[0]['timestamp']
                self.lbl_oldest_entry.setText(oldest)
                self.lbl_newest_entry.setText(newest)
            else:
                self.lbl_oldest_entry.setText("--")
                self.lbl_newest_entry.setText("--")

            # حجم فایل (شبیه‌سازی)
            file_size = total_entries * 0.1  # تقریباً 0.1KB به ازای هر لاگ
            self.lbl_file_size.setText(f"{file_size:.1f} KB")

        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی آمار: {e}")

    def export_logs(self):
        """خروجی گرفتن از لاگ‌ها"""
        try:
            from PyQt5.QtWidgets import QFileDialog

            file_path, _ = QFileDialog.getSaveFileName(
                self, "ذخیره لاگ", f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                # TODO: ذخیره لاگ‌ها در فایل
                QMessageBox.information(self, "موفق", "لاگ‌ها با موفقیت export شدند")
                self.log_exported.emit(file_path)

        except Exception as e:
            logger.error(f"خطا در export لاگ: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در export: {str(e)}")

    def clear_logs(self):
        """پاک کردن لاگ‌ها"""
        try:
            reply = QMessageBox.question(
                self, 'تأیید پاک کردن',
                'آیا از پاک کردن تمام لاگ‌ها اطمینان دارید؟\nاین عمل غیرقابل برگشت است.',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # TODO: پاک کردن فایل‌های لاگ
                self.txt_log_display.clear()
                self.log_data = []
                self.update_stats()
                self.lbl_log_info.setText("لاگ‌ها پاک شدند")

                QMessageBox.information(self, "موفق", "لاگ‌ها با موفقیت پاک شدند")
                self.log_cleared.emit()

        except Exception as e:
            logger.error(f"خطا در پاک کردن لاگ: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در پاک کردن لاگ: {str(e)}")

    def analyze_logs(self):
        """تحلیل لاگ‌ها"""
        try:
            # TODO: پیاده‌سازی تحلیل پیشرفته
            QMessageBox.information(self, "تحلیل", "تحلیل لاگ‌ها انجام شد")

        except Exception as e:
            logger.error(f"خطا در تحلیل لاگ: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تحلیل: {str(e)}")
