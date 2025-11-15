# app/views/widgets/shared/message_box.py
"""
پیام‌باکس‌های سفارشی
"""

from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap

class CustomMessageBox(QDialog):
    """
    پیام‌باکس سفارشی با طراحی بهتر
    """

    def __init__(self, parent=None, title: str = "", message: str = "",
                 message_type: str = "info"):
        super().__init__(parent)
        self.title = title
        self.message = message
        self.message_type = message_type

        self.setup_ui()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        self.setWindowTitle(self.title)
        self.setModal(True)
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # آیکون و متن
        content_layout = QHBoxLayout()

        # آیکون
        icon_label = QLabel()
        icon_size = 48

        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "success": "✅",
            "question": "❓"
        }

        icon_text = icons.get(self.message_type, "ℹ️")
        icon_label.setText(icon_text)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: {icon_size}px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        icon_label.setFixedSize(icon_size + 10, icon_size + 10)

        # متن پیام
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            QLabel {
                font-size: 11px;
                line-height: 1.4;
            }
        """)

        content_layout.addWidget(icon_label)
        content_layout.addWidget(message_label)
        layout.addLayout(content_layout)

        # دکمه‌ها
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        if self.message_type == "question":
            self.yes_btn = QPushButton("بله")
            self.no_btn = QPushButton("خیر")

            self.yes_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)

            self.no_btn.setStyleSheet("""
                QPushButton {
                    background-color: #6c757d;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #5a6268;
                }
            """)

            self.yes_btn.clicked.connect(self.accept)
            self.no_btn.clicked.connect(self.reject)

            button_layout.addWidget(self.yes_btn)
            button_layout.addWidget(self.no_btn)
        else:
            self.ok_btn = QPushButton("تأیید")
            self.ok_btn.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 60px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
            """)
            self.ok_btn.clicked.connect(self.accept)
            button_layout.addWidget(self.ok_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    @classmethod
    def show_info(cls, parent, title: str, message: str):
        """نمایش پیام اطلاعات"""
        dialog = cls(parent, title, message, "info")
        return dialog.exec_()

    @classmethod
    def show_warning(cls, parent, title: str, message: str):
        """نمایش پیام هشدار"""
        dialog = cls(parent, title, message, "warning")
        return dialog.exec_()

    @classmethod
    def show_error(cls, parent, title: str, message: str):
        """نمایش پیام خطا"""
        dialog = cls(parent, title, message, "error")
        return dialog.exec_()

    @classmethod
    def show_success(cls, parent, title: str, message: str):
        """نمایش پیام موفقیت"""
        dialog = cls(parent, title, message, "success")
        return dialog.exec_()

    @classmethod
    def show_question(cls, parent, title: str, message: str):
        """نمایش سؤال"""
        dialog = cls(parent, title, message, "question")
        return dialog.exec_()
