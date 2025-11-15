# app/views/widgets/shared/base_widget.py
"""
ویجت پایه و دیالوگ پایه برای تمام کامپوننت‌ها
"""

import logging
from PyQt5.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

logger = logging.getLogger(__name__)

class BaseWidget(QWidget):
    """
    ویجت پایه با قابلیت‌های مشترک برای تمام ویجت‌ها
    """

    # سیگنال‌های مشترک
    data_loaded = pyqtSignal(bool)  # موفقیت بارگذاری داده
    error_occurred = pyqtSignal(str, str)  # خطا با عنوان و پیام

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
        self.auto_refresh_timer = None

    def setup_ui(self):
        """راه‌اندازی رابط کاربری پایه"""
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(8)
        self.setLayout(self.main_layout)

        # هدر ویجت
        self.header_frame = QFrame()
        self.header_frame.setFrameStyle(QFrame.StyledPanel)
        self.header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
        """)

        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(5, 5, 5, 5)

        self.title_label = QLabel()
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #2c3e50;")

        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()

        # دکمه‌های action در هدر
        self.action_buttons_layout = QHBoxLayout()
        self.header_layout.addLayout(self.action_buttons_layout)

        self.header_frame.setLayout(self.header_layout)
        self.main_layout.addWidget(self.header_frame)

        # محتوای اصلی
        self.content_frame = QFrame()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_frame.setLayout(self.content_layout)
        self.main_layout.addWidget(self.content_frame)

        # وضعیت بارگذاری
        self.loading_widget = QLabel("در حال بارگذاری...")
        self.loading_widget.setAlignment(Qt.AlignCenter)
        self.loading_widget.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-style: italic;
                padding: 20px;
            }
        """)
        self.loading_widget.hide()

        self.content_layout.addWidget(self.loading_widget)

    def setup_connections(self):
        """تنظیم اتصالات پایه"""
        self.data_loaded.connect(self.on_data_loaded)
        self.error_occurred.connect(self.on_error_occurred)

    def set_title(self, title: str):
        """تنظیم عنوان ویجت"""
        self.title_label.setText(title)

    def add_action_button(self, text: str, callback, icon=None, tooltip: str = None):
        """افزودن دکمه action به هدر"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
        if tooltip:
            button.setToolTip(tooltip)

        button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)

        button.clicked.connect(callback)
        self.action_buttons_layout.addWidget(button)
        return button

    def show_loading(self, message: str = "در حال بارگذاری..."):
        """نمایش وضعیت بارگذاری"""
        self.loading_widget.setText(message)
        self.loading_widget.show()
        self.content_frame.hide()

    def hide_loading(self):
        """پنهان کردن وضعیت بارگذاری"""
        self.loading_widget.hide()
        self.content_frame.show()

    def start_auto_refresh(self, interval_ms: int = 30000):
        """شروع به‌روزرسانی خودکار"""
        if self.auto_refresh_timer is None:
            self.auto_refresh_timer = QTimer()
            self.auto_refresh_timer.timeout.connect(self.refresh_data)

        self.auto_refresh_timer.start(interval_ms)

    def stop_auto_refresh(self):
        """توقف به‌روزرسانی خودکار"""
        if self.auto_refresh_timer:
            self.auto_refresh_timer.stop()

    def refresh_data(self):
        """بارگذاری مجدد داده‌ها - باید در کلاس فرزند پیاده‌سازی شود"""
        logger.warning("refresh_data باید در کلاس فرزند پیاده‌سازی شود")

    def on_data_loaded(self, success: bool):
        """هنگام بارگذاری داده"""
        self.hide_loading()
        if not success:
            self.show_error("خطا در بارگذاری داده‌ها")

    def on_error_occurred(self, title: str, message: str):
        """هنگام وقوع خطا"""
        self.hide_loading()
        self.show_error(message, title)

    def show_error(self, message: str, title: str = "خطا"):
        """نمایش خطا"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(self, title, message)

    def show_success(self, message: str, title: str = "موفق"):
        """نمایش پیام موفقیت"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)

    def clear_layout(self, layout):
        """پاک کردن تمام ویجت‌های یک layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_style_sheet(self, widget_type: str = "default") -> str:
        """دریافت استایل شیت بر اساس نوع ویجت"""
        styles = {
            "default": """
                QWidget {
                    font-family: "Tahoma";
                    font-size: 9pt;
                }
            """,
            "panel": """
                QFrame {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 6px;
                    padding: 8px;
                }
            """,
            "button_primary": """
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """,
            "button_success": """
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """
        }
        return styles.get(widget_type, styles["default"])


class BaseDialog(QDialog):
    """
    دیالوگ پایه با قابلیت‌های مشترک
    """

    def __init__(self, parent=None, title: str = ""):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle(title)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(10)
        self.setLayout(self.main_layout)

        # محتوای اصلی
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_widget.setLayout(self.content_layout)
        self.main_layout.addWidget(self.content_widget)

        # دکمه‌های پایین
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()

        self.ok_button = QPushButton("تأیید")
        self.cancel_button = QPushButton("انصراف")

        self.ok_button.setStyleSheet(self.get_style_sheet("button_primary"))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.main_layout.addLayout(self.button_layout)

    def set_content_widget(self, widget: QWidget):
        """تنظیم ویجت محتوای اصلی"""
        self.content_layout.addWidget(widget)

    def get_style_sheet(self, style_type: str) -> str:
        """دریافت استایل شیت"""
        return BaseWidget().get_style_sheet(style_type)
