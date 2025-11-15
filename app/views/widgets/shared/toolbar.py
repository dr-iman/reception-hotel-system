# app/views/widgets/shared/toolbar.py
"""
نوار ابزار سفارشی
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel,
                            QComboBox, QLineEdit, QToolButton, QMenu)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon

class ToolBarWidget(QWidget):
    """
    نوار ابزار سفارشی با دکمه‌ها و ابزارها
    """

    # سیگنال‌ها
    button_clicked = pyqtSignal(str)  # نام دکمه

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buttons = {}
        self.setup_ui()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(6)
        self.setLayout(layout)

        self.layout = layout

        # استایل
        self.setStyleSheet("""
            ToolBarWidget {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }
        """)

    def add_button(self, name: str, text: str, icon: QIcon = None,
                   tooltip: str = None, style: str = "default"):
        """افزودن دکمه"""
        button = QPushButton(text)
        if icon:
            button.setIcon(icon)
        if tooltip:
            button.setToolTip(tooltip)

        # استایل‌های مختلف
        styles = {
            "default": """
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #ced4da;
                    padding: 6px 12px;
                    border-radius: 4px;
                    color: #495057;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #adb5bd;
                }
            """,
            "primary": """
                QPushButton {
                    background-color: #007bff;
                    border: 1px solid #007bff;
                    padding: 6px 12px;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                    border-color: #0056b3;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #28a745;
                    border: 1px solid #28a745;
                    padding: 6px 12px;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                    border-color: #218838;
                }
            """
        }

        button.setStyleSheet(styles.get(style, styles["default"]))
        button.clicked.connect(lambda: self.button_clicked.emit(name))

        self.layout.addWidget(button)
        self.buttons[name] = button
        return button

    def add_separator(self):
        """افزودن جداکننده"""
        separator = QLabel("|")
        separator.setStyleSheet("color: #dee2e6; margin: 0 8px;")
        self.layout.addWidget(separator)

    def add_widget(self, widget: QWidget):
        """افزودن ویجت دلخواه"""
        self.layout.addWidget(widget)

    def add_stretch(self):
        """افزودن stretch"""
        self.layout.addStretch()

    def add_dropdown(self, name: str, items: list, default_text: str = "انتخاب کنید"):
        """افزودن dropdown"""
        combo = QComboBox()
        combo.addItem(default_text)
        combo.addItems(items)
        combo.currentTextChanged.connect(lambda text: self.button_clicked.emit(f"{name}:{text}"))
        self.layout.addWidget(combo)
        return combo

    def add_search_box(self, placeholder: str = "جستجو..."):
        """افزودن جعبه جستجو"""
        search_box = QLineEdit()
        search_box.setPlaceholderText(placeholder)
        search_box.setMinimumWidth(200)
        search_box.textChanged.connect(lambda text: self.button_clicked.emit(f"search:{text}"))
        self.layout.addWidget(search_box)
        return search_box

    def set_button_enabled(self, name: str, enabled: bool):
        """فعال/غیرفعال کردن دکمه"""
        if name in self.buttons:
            self.buttons[name].setEnabled(enabled)

    def set_button_visible(self, name: str, visible: bool):
        """نمایش/پنهان کردن دکمه"""
        if name in self.buttons:
            self.buttons[name].setVisible(visible)
