# app/views/widgets/shared/loading_widget.py
"""
ویجت نمایش بارگذاری
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QMovie

class LoadingWidget(QWidget):
    """
    ویجت نمایش وضعیت بارگذاری
    """

    def __init__(self, parent=None, message: str = "در حال بارگذاری..."):
        super().__init__(parent)
        self.message = message
        self.setup_ui()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        # انیمیشن بارگذاری (می‌توانید از یک GIF استفاده کنید)
        self.loading_label = QLabel()
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setText("⏳")  # می‌توانید با یک GIF جایگزین کنید
        self.loading_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                color: #007bff;
            }
        """)
        layout.addWidget(self.loading_label)

        # متن بارگذاری
        self.message_label = QLabel(self.message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 11px;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.message_label)

        # نوار پیشرفت (اختیاری)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # indeterminate
        layout.addWidget(self.progress_bar)

    def set_message(self, message: str):
        """تنظیم پیام بارگذاری"""
        self.message_label.setText(message)

    def show_progress(self, show: bool = True):
        """نمایش نوار پیشرفت"""
        self.progress_bar.setVisible(show)

    def set_progress(self, value: int, maximum: int = 100):
        """تنظیم مقدار پیشرفت"""
        if maximum > 0:
            self.progress_bar.setRange(0, maximum)
            self.progress_bar.setValue(value)
