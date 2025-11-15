# app/views/widgets/financial/guest_folio.py
"""
ویجت نمایش و مدیریت صورت‌حساب مهمان
"""

import logging
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QDoubleSpinBox,
                            QTextEdit, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush

from app.services.reception.payment_service import PaymentService
from app.services.reception.guest_service import GuestService
from config import config

logger = logging.getLogger(__name__)

class GuestFolioWidget(QWidget):
    """ویجت نمایش و مدیریت صورت‌حساب مهمان"""

    # سیگنال‌ها
    folio_updated = pyqtSignal()

    def __init__(self, stay_id=None, parent=None):
        super().__init__(parent)
        self.stay_id = stay_id
        self.folio_data = None
        self.init_ui()
        if stay_id:
            self.load_folio_data()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # ایجاد تب‌های داخلی
        self.tabs = QTabWidget()

        # تب خلاصه
        self.summary_tab = self.create_summary_tab()
        self.tabs.addTab(self.summary_tab, "📊 خلاصه")

        # تب تراکنش‌ها
        self.transactions_tab = self.create_transactions_tab()
        self.tabs.addTab(self.transactions_tab, "💳 تراکنش‌ها")

        # تب مدیریت هزینه‌ها
        self.charges_tab = self.create_charges_tab()
        self.tabs.addTab(self.charges_tab, "➕ مدیریت هزینه‌ها")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def create_summary_tab(self):
        """ایجاد تب خلاصه"""
        widget = QWidget()
        layout = QVBoxLayout()

        # کارت‌های آمار
        stats_layout = QHBoxLayout()

        self.charges_card = self.create_stat_card("💰 هزینه‌ها", "0", QColor(231, 76, 60))
        self.payments_card = self.create_stat_card("💵 پرداخت‌ها", "0", QColor(46, 204, 113))
        self.balance_card = self.create_stat_card("⚖️ مانده", "0", QColor(52, 152, 219))
        self.status_card = self.create_stat_card("📋 وضعیت", "باز", QColor(155, 89, 182))

        stats_layout.addWidget(self.charges_card)
        stats_layout.addWidget(self.payments_card)
        stats_layout.addWidget(self.balance_card)
        stats_layout.addWidget(self.status_card)

        layout.addLayout(stats_layout)

        # اطلاعات مهمان
        guest_info_group = self.create_guest_info_group()
        layout.addWidget(guest_info_group)

        # نمودار تراکنش‌ها (ساده)
        chart_group = self.create_simple_chart_group()
        layout.addWidget(chart_group)

        widget.setLayout(layout)
        return widget

    def create_stat_card(self, title, value, color):
        """ایجاد کارت آمار"""
        card = QGroupBox(title)
        card.setMinimumHeight(100)
        layout = QVBoxLayout()

        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setStyleSheet(f"color: {color.name()};")
        value_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_guest_info_group(self):
        """گروه اطلاعات مهمان"""
        group = QGroupBox("اطلاعات مهمان")
        layout = QHBoxLayout()

        left_layout = QFormLayout()
        right_layout = QFormLayout()

        self.lbl_guest_name = QLabel("--")
        self.lbl_room_number = QLabel("--")
        self.lbl_stay_period = QLabel("--")
        self.lbl_folio_id = QLabel("--")

        left_layout.addRow("نام مهمان:", self.lbl_guest_name)
        left_layout.addRow("شماره اتاق:", self.lbl_room_number)
        right_layout.addRow("دوره اقامت:", self.lbl_stay_period)
        right_layout.addRow("شماره صورت‌حساب:", self.lbl_folio_id)

        layout.addLayout(left_layout)
        layout.addLayout(right_layout)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def create_simple_chart_group(self):
        """گروه نمودار ساده"""
        group = QGroupBox("نمایش تراکنش‌ها")
        layout = QVBoxLayout()

        # TODO: پیاده‌سازی نمودار پیشرفته
        chart_label = QLabel("📈 نمودار تراکنش‌ها (به زودی)")
        chart_label.setAlignment(Qt.AlignCenter)
        chart_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")

        layout.addWidget(chart_label)
        group.setLayout(layout)
        return group

    def create_transactions_tab(self):
        """ایجاد تب تراکنش‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فیلترها
        filter_layout = QHBoxLayout()

        self.cmb_transaction_type = QComboBox()
        self.cmb_transaction_type.addItems(["همه تراکنش‌ها", "هزینه‌ها", "پرداخت‌ها"])
        self.cmb_transaction_type.currentTextChanged.connect(self.filter_transactions)

        filter_layout.addWidget(QLabel("نوع تراکنش:"))
        filter_layout.addWidget(self.cmb_transaction_type)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # جدول تراکنش‌ها
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(6)
        self.transactions_table.setHorizontalHeaderLabels([
            "تاریخ", "نوع", "مبلغ", "شرح", "دسته‌بندی", "وضعیت"
        ])

        self.transactions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.transactions_table.setEditTriggers(QTableWidget.NoEditTriggers)

        header = self.transactions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        layout.addWidget(self.transactions_table)

        widget.setLayout(layout)
        return widget

    def create_charges_tab(self):
        """ایجاد تب مدیریت هزینه‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فرم افزودن هزینه
        add_charge_group = self.create_add_charge_group()
        layout.addWidget(add_charge_group)

        # لیست هزینه‌های اخیر
        recent_charges_group = self.create_recent_charges_group()
        layout.addWidget(recent_charges_group)

        widget.setLayout(layout)
        return widget

    def create_add_charge_group(self):
        """گروه افزودن هزینه"""
        group = QGroupBox("افزودن هزینه جدید")
        layout = QFormLayout()

        self.spn_charge_amount = QDoubleSpinBox()
        self.spn_charge_amount.setRange(0, 10000000)
        self.spn_charge_amount.setSuffix(" تومان")
        self.spn_charge_amount.setDecimals(0)

        self.cmb_charge_category = QComboBox()
        self.cmb_charge_category.addItems([
            "اتاق", "رستوران", "مینی‌بار", "تلفن", "لاندری",
            "خدمات ویژه", "سایر"
        ])

        self.txt_charge_description = QLineEdit()
        self.txt_charge_description.setPlaceholderText("شرح هزینه...")

        self.btn_add_charge = QPushButton("افزودن هزینه")
        self.btn_add_charge.clicked.connect(self.add_charge)

        layout.addRow("مبلغ:", self.spn_charge_amount)
        layout.addRow("دسته‌بندی:", self.cmb_charge_category)
        layout.addRow("شرح:", self.txt_charge_description)
        layout.addRow(self.btn_add_charge)

        group.setLayout(layout)
        return group

    def create_recent_charges_group(self):
        """گroup هزینه‌های اخیر"""
        group = QGroupBox("هزینه‌های اخیر")
        layout = QVBoxLayout()

        self.recent_charges_table = QTableWidget()
        self.recent_charges_table.setColumnCount(4)
        self.recent_charges_table.setHorizontalHeaderLabels([
            "تاریخ", "مبلغ", "دسته‌بندی", "شرح"
        ])

        header = self.recent_charges_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        layout.addWidget(self.recent_charges_table)

        group.setLayout(layout)
        return group

    def load_folio_data(self):
        """بارگذاری اطلاعات صورت‌حساب"""
        if not self.stay_id:
            return

        try:
            result = PaymentService.get_guest_folio(self.stay_id)

            if result['success']:
                self.folio_data = result['folio']
                self.populate_summary()
                self.populate_transactions()
                self.load_guest_info()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در بارگذاری صورت‌حساب: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در بارگذاری صورت‌حساب: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری صورت‌حساب: {str(e)}")

    def populate_summary(self):
        """پر کردن اطلاعات خلاصه"""
        if not self.folio_data:
            return

        # به‌روزرسانی کارت‌ها
        self.update_stat_card(self.charges_card, f"{self.folio_data['total_charges']:,.0f}")
        self.update_stat_card(self.payments_card, f"{self.folio_data['total_payments']:,.0f}")
        self.update_stat_card(self.balance_card, f"{self.folio_data['current_balance']:,.0f}")

        # وضعیت صورت‌حساب
        status_text = "تسویه شده" if self.folio_data['current_balance'] <= 0 else "باز"
        status_color = QColor(46, 204, 113) if status_text == "تسویه شده" else QColor(230, 126, 34)
        self.update_stat_card(self.status_card, status_text, status_color)

    def update_stat_card(self, card, value, color=None):
        """به‌روزرسانی کارت آمار"""
        layout = card.layout()
        if layout and layout.count() > 0:
            label = layout.itemAt(0).widget()
            if isinstance(label, QLabel):
                label.setText(value)
                if color:
                    label.setStyleSheet(f"color: {color.name()}; font-size: 16px; font-weight: bold;")

    def populate_transactions(self):
        """پر کردن جدول تراکنش‌ها"""
        if not self.folio_data:
            return

        transactions = self.folio_data['transactions']
        self.transactions_table.setRowCount(len(transactions))

        for row, transaction in enumerate(transactions):
            # تاریخ
            self.transactions_table.setItem(row, 0, QTableWidgetItem(
                transaction['created_at'].strftime("%Y/%m/%d %H:%M")
            ))

            # نوع
            type_text = "💸 هزینه" if transaction['type'] == 'charge' else '💳 پرداخت'
            self.transactions_table.setItem(row, 1, QTableWidgetItem(type_text))

            # مبلغ
            amount_item = QTableWidgetItem(f"{transaction['amount']:,.0f}")
            if transaction['type'] == 'charge':
                amount_item.setForeground(QBrush(QColor(231, 76, 60)))  # قرمز
            else:
                amount_item.setForeground(QBrush(QColor(46, 204, 113)))  # سبز
            self.transactions_table.setItem(row, 2, amount_item)

            # شرح
            self.transactions_table.setItem(row, 3, QTableWidgetItem(transaction['description']))

            # دسته‌بندی
            category = transaction.get('category', 'عمومی')
            self.transactions_table.setItem(row, 4, QTableWidgetItem(category))

            # وضعیت
            status_item = QTableWidgetItem("✅ تکمیل شده")
            status_item.setForeground(QBrush(QColor(46, 204, 113)))
            self.transactions_table.setItem(row, 5, status_item)

    def load_guest_info(self):
        """بارگذاری اطلاعات مهمان"""
        if not self.stay_id:
            return

        try:
            # TODO: دریافت اطلاعات مهمان از سرویس
            # این بخش نیاز به پیاده‌سازی دارد
            self.lbl_guest_name.setText("مهمان نمونه")
            self.lbl_room_number.setText("۱۰۱")
            self.lbl_stay_period("۱۴۰۲/۱۰/۱۵ - ۱۴۰۲/۱۰/۱۸")
            self.lbl_folio_id.setText(str(self.folio_data['folio_id']))

        except Exception as e:
            logger.error(f"خطا در بارگذاری اطلاعات مهمان: {e}")

    def filter_transactions(self):
        """فیلتر تراکنش‌ها"""
        # این متد نیاز به پیاده‌سازی دارد
        pass

    def add_charge(self):
        """افزودن هزینه جدید"""
        try:
            amount = Decimal(str(self.spn_charge_amount.value()))
            category = self.cmb_charge_category.currentText()
            description = self.txt_charge_description.text().strip()

            if amount <= 0:
                QMessageBox.warning(self, "هشدار", "مبلغ باید بزرگتر از صفر باشد")
                return

            if not description:
                QMessageBox.warning(self, "هشدار", "لطفاً شرح هزینه را وارد کنید")
                return

            # افزودن هزینه
            result = PaymentService.add_folio_charge(
                self.stay_id, amount, description, category
            )

            if result['success']:
                QMessageBox.information(self, "موفق", "هزینه با موفقیت افزوده شد")
                self.reset_charge_form()
                self.load_folio_data()
                self.folio_updated.emit()
            else:
                QMessageBox.warning(self, "خطا", f"خطا در افزودن هزینه: {result.get('error')}")

        except Exception as e:
            logger.error(f"خطا در افزودن هزینه: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در افزودن هزینه: {str(e)}")

    def reset_charge_form(self):
        """بازنشانی فرم افزودن هزینه"""
        self.spn_charge_amount.setValue(0)
        self.txt_charge_description.clear()

    def set_stay_id(self, stay_id):
        """تنظیم ID اقامت جدید"""
        self.stay_id = stay_id
        self.load_folio_data()
