# app/views/widgets/shared/search_bar.py
"""
ویجت جستجوی پیشرفته
"""

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton,
                            QComboBox, QLabel, QCheckBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIcon

class SearchWidget(QWidget):
    """
    ویجت جستجوی پیشرفته با فیلترهای مختلف
    """

    search_triggered = pyqtSignal(str, str, bool)  # متن جستجو, فیلد, دقیق

    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_fields = []
        self.setup_ui()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # فیلد جستجو
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو...")
        self.search_input.setMinimumWidth(200)
        self.search_input.returnPressed.connect(self.on_search)
        layout.addWidget(self.search_input)

        # فیلد انتخاب
        self.field_combo = QComboBox()
        self.field_combo.setMinimumWidth(120)
        layout.addWidget(self.field_combo)

        # چک‌باکس جستجوی دقیق
        self.exact_match_check = QCheckBox("جستجوی دقیق")
        layout.addWidget(self.exact_match_check)

        # دکمه جستجو
        self.search_btn = QPushButton("جستجو")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.search_btn.clicked.connect(self.on_search)
        layout.addWidget(self.search_btn)

        # دکمه پاک کردن
        self.clear_btn = QPushButton("پاک کردن")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self.clear_btn.clicked.connect(self.on_clear)
        layout.addWidget(self.clear_btn)

    def set_search_fields(self, fields: list):
        """تنظیم فیلدهای جستجو"""
        self.search_fields = fields
        self.field_combo.clear()
        self.field_combo.addItem("همه فیلدها", "all")
        for field in fields:
            self.field_combo.addItem(field['name'], field['key'])

    def on_search(self):
        """هنگام جستجو"""
        search_text = self.search_input.text().strip()
        field_key = self.field_combo.currentData()
        exact_match = self.exact_match_check.isChecked()

        self.search_triggered.emit(search_text, field_key, exact_match)

    def on_clear(self):
        """پاک کردن جستجو"""
        self.search_input.clear()
        self.field_combo.setCurrentIndex(0)
        self.exact_match_check.setChecked(False)
        self.search_triggered.emit("", "all", False)

    def get_search_params(self) -> dict:
        """دریافت پارامترهای جستجو"""
        return {
            'text': self.search_input.text().strip(),
            'field': self.field_combo.currentData(),
            'exact_match': self.exact_match_check.isChecked()
        }
