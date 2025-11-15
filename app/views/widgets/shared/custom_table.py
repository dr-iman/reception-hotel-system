# app/views/widgets/shared/custom_table.py
"""
جدول سفارشی با قابلیت‌های پیشرفته
"""

import logging
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (QTableView, QWidget, QVBoxLayout, QHBoxLayout,
                            QHeaderView, QAbstractItemView, QMenu, QAction,
                            QLabel, QLineEdit, QPushButton, QComboBox)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, pyqtSignal
from PyQt5.QtGui import QFont, QBrush, QColor

logger = logging.getLogger(__name__)

class TableModel(QAbstractTableModel):
    """
    مدل جدول برای نمایش داده‌های پویا
    """

    def __init__(self, data: List[Dict] = None, headers: List[str] = None):
        super().__init__()
        self._data = data or []
        self._headers = headers or []
        self._column_keys = []

    def set_data(self, data: List[Dict], headers: List[str] = None, column_keys: List[str] = None):
        """تنظیم داده‌ها و هدرهای جدول"""
        self.beginResetModel()
        self._data = data
        if headers:
            self._headers = headers
        if column_keys:
            self._column_keys = column_keys
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = None) -> int:
        """تعداد سطرها"""
        return len(self._data)

    def columnCount(self, parent: QModelIndex = None) -> int:
        """تعداد ستون‌ها"""
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """داده هر سلول"""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._data) or col >= len(self._headers):
            return None

        item = self._data[row]
        key = self._column_keys[col] if self._column_keys else list(item.keys())[col]
        value = item.get(key, "")

        if role == Qt.DisplayRole:
            return str(value)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight | Qt.AlignVCenter
        elif role == Qt.BackgroundRole:
            # رنگ‌آمیزی سطرهای زوج و فرد
            if row % 2 == 0:
                return QBrush(QColor(248, 249, 250))  # رنگ روشن
            else:
                return QBrush(QColor(255, 255, 255))  # رنگ سفید

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """داده هدرها"""
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]
            elif orientation == Qt.Vertical:
                return str(section + 1)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.FontRole:
            font = QFont()
            font.setBold(True)
            return font

        return None

    def get_row_data(self, row: int) -> Dict:
        """دریافت داده سطر مشخص"""
        if 0 <= row < len(self._data):
            return self._data[row]
        return {}


class CustomTableWidget(QWidget):
    """
    ویجت جدول سفارشی با قابلیت‌های پیشرفته
    """

    # سیگنال‌ها
    row_selected = pyqtSignal(dict)  # انتخاب سطر
    row_double_clicked = pyqtSignal(dict)  # دابل کلیک روی سطر
    context_menu_requested = pyqtSignal(dict, QModelIndex)  # منوی راست کلیک

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = TableModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """راه‌اندازی رابط کاربری"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # نوار ابزار جدول
        self.toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(5, 5, 5, 5)

        # جستجو
        toolbar_layout.addWidget(QLabel("جستجو:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("جستجو در جدول...")
        self.search_input.setMaximumWidth(200)
        toolbar_layout.addWidget(self.search_input)

        # فیلتر ستون
        toolbar_layout.addWidget(QLabel("فیلتر ستون:"))
        self.column_filter = QComboBox()
        self.column_filter.setMaximumWidth(150)
        toolbar_layout.addWidget(self.column_filter)

        toolbar_layout.addStretch()

        # دکمه‌ها
        self.refresh_btn = QPushButton("بروزرسانی")
        self.export_btn = QPushButton("خروجی")

        toolbar_layout.addWidget(self.refresh_btn)
        toolbar_layout.addWidget(self.export_btn)

        self.toolbar.setLayout(toolbar_layout)
        layout.addWidget(self.toolbar)

        # جدول
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)

        # تنظیمات ظاهری
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setVisible(False)

        # فونت
        font = QFont()
        font.setPointSize(9)
        self.table_view.setFont(font)

        layout.addWidget(self.table_view)

        # نوار وضعیت
        self.status_bar = QLabel("تعداد رکوردها: 0")
        self.status_bar.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 5px;
                border-top: 1px solid #dee2e6;
                color: #6c757d;
            }
        """)
        layout.addWidget(self.status_bar)

    def setup_connections(self):
        """تنظیم اتصالات"""
        self.search_input.textChanged.connect(self.on_search_text_changed)
        self.column_filter.currentTextChanged.connect(self.on_column_filter_changed)
        self.refresh_btn.clicked.connect(self.refresh_data)
        self.export_btn.clicked.connect(self.export_data)

        self.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.table_view.doubleClicked.connect(self.on_double_click)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)

    def set_data(self, data: List[Dict], headers: List[str], column_keys: List[str] = None):
        """تنظیم داده‌های جدول"""
        self.model.set_data(data, headers, column_keys)
        self.update_column_filter(headers)
        self.update_status()

        # تنظیم عرض ستون‌ها
        self.table_view.resizeColumnsToContents()

    def update_column_filter(self, headers: List[str]):
        """به‌روزرسانی فیلتر ستون‌ها"""
        self.column_filter.clear()
        self.column_filter.addItem("همه ستون‌ها")
        self.column_filter.addItems(headers)

    def update_status(self):
        """به‌روزرسانی نوار وضعیت"""
        count = self.model.rowCount()
        self.status_bar.setText(f"تعداد رکوردها: {count}")

    def on_search_text_changed(self, text: str):
        """هنگام تغییر متن جستجو"""
        self.proxy_model.setFilterFixedString(text)

    def on_column_filter_changed(self, column: str):
        """هنگام تغییر فیلتر ستون"""
        if column == "همه ستون‌ها":
            self.proxy_model.setFilterKeyColumn(-1)  # همه ستون‌ها
        else:
            column_index = self.column_filter.currentIndex() - 1
            if column_index >= 0:
                self.proxy_model.setFilterKeyColumn(column_index)

    def on_selection_changed(self):
        """هنگام تغییر انتخاب"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if selected_indexes:
            proxy_index = selected_indexes[0]
            source_index = self.proxy_model.mapToSource(proxy_index)
            row_data = self.model.get_row_data(source_index.row())
            self.row_selected.emit(row_data)

    def on_double_click(self, index: QModelIndex):
        """هنگام دابل کلیک"""
        source_index = self.proxy_model.mapToSource(index)
        row_data = self.model.get_row_data(source_index.row())
        self.row_double_clicked.emit(row_data)

    def show_context_menu(self, position):
        """نمایش منوی راست کلیک"""
        index = self.table_view.indexAt(position)
        if index.isValid():
            source_index = self.proxy_model.mapToSource(index)
            row_data = self.model.get_row_data(source_index.row())

            menu = QMenu(self)

            # آیتم‌های منو
            view_action = QAction("مشاهده جزئیات", self)
            edit_action = QAction("ویرایش", self)
            delete_action = QAction("حذف", self)

            menu.addAction(view_action)
            menu.addAction(edit_action)
            menu.addAction(delete_action)

            # اجرای منو
            action = menu.exec_(self.table_view.viewport().mapToGlobal(position))

            if action == view_action:
                self.context_menu_requested.emit(row_data, source_index)
            elif action == edit_action:
                self.context_menu_requested.emit(row_data, source_index)
            elif action == delete_action:
                self.context_menu_requested.emit(row_data, source_index)

    def refresh_data(self):
        """بروزرسانی داده‌ها"""
        # باید در کلاس فرزند پیاده‌سازی شود
        logger.info("بروزرسانی داده‌های جدول")

    def export_data(self):
        """خروجی گرفتن از داده‌ها"""
        # باید در کلاس فرزند پیاده‌سازی شود
        logger.info("خروجی گرفتن از داده‌های جدول")

    def get_selected_row(self) -> Optional[Dict]:
        """دریافت سطر انتخاب شده"""
        selected_indexes = self.table_view.selectionModel().selectedRows()
        if selected_indexes:
            proxy_index = selected_indexes[0]
            source_index = self.proxy_model.mapToSource(proxy_index)
            return self.model.get_row_data(source_index.row())
        return None

    def clear_selection(self):
        """پاک کردن انتخاب"""
        self.table_view.clearSelection()

    def set_column_widths(self, widths: List[int]):
        """تنظیم عرض ستون‌ها"""
        for i, width in enumerate(widths):
            if i < self.model.columnCount():
                self.table_view.setColumnWidth(i, width)
