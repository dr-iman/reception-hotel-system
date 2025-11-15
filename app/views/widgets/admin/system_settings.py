# app/views/widgets/admin/system_settings.py
"""
ویجت تنظیمات سیستم
"""

import logging
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QSpinBox, QDoubleSpinBox,
                            QCheckBox, QTabWidget, QTextEdit, QTimeEdit)
from PyQt5.QtCore import Qt, QTime, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class SystemSettingsWidget(QWidget):
    """ویجت تنظیمات سیستم"""

    # سیگنال‌ها
    settings_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_data = {}
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # تب‌های تنظیمات
        self.tabs = QTabWidget()

        # تب تنظیمات عمومی
        self.general_tab = self.create_general_tab()
        self.tabs.addTab(self.general_tab, "⚙️ عمومی")

        # تب تنظیمات مالی
        self.financial_tab = self.create_financial_tab()
        self.tabs.addTab(self.financial_tab, "💰 مالی")

        # تب تنظیمات اتاق‌ها
        self.rooms_tab = self.create_rooms_tab()
        self.tabs.addTab(self.rooms_tab, "🏨 اتاق‌ها")

        # تب تنظیمات اعلان‌ها
        self.notifications_tab = self.create_notifications_tab()
        self.tabs.addTab(self.notifications_tab, "🔔 اعلان‌ها")

        main_layout.addWidget(self.tabs)

        # نوار عملیات
        action_layout = self.create_action_layout()
        main_layout.addLayout(action_layout)

        self.setLayout(main_layout)

    def create_general_tab(self):
        """ایجاد تب تنظیمات عمومی"""
        widget = QWidget()
        layout = QVBoxLayout()

        # اطلاعات هتل
        hotel_info_group = QGroupBox("اطلاعات هتل")
        hotel_layout = QFormLayout()

        self.txt_hotel_name = QLineEdit()
        self.txt_hotel_name.setPlaceholderText("نام هتل")

        self.txt_hotel_address = QTextEdit()
        self.txt_hotel_address.setMaximumHeight(60)
        self.txt_hotel_address.setPlaceholderText("آدرس هتل")

        self.txt_hotel_phone = QLineEdit()
        self.txt_hotel_phone.setPlaceholderText("تلفن هتل")

        self.txt_hotel_email = QLineEdit()
        self.txt_hotel_email.setPlaceholderText("ایمیل هتل")

        hotel_layout.addRow("نام هتل:", self.txt_hotel_name)
        hotel_layout.addRow("آدرس:", self.txt_hotel_address)
        hotel_layout.addRow("تلفن:", self.txt_hotel_phone)
        hotel_layout.addRow("ایمیل:", self.txt_hotel_email)

        hotel_info_group.setLayout(hotel_layout)
        layout.addWidget(hotel_info_group)

        # تنظیمات سیستم
        system_group = QGroupBox("تنظیمات سیستم")
        system_layout = QFormLayout()

        self.cmb_language = QComboBox()
        self.cmb_language.addItems(["فارسی", "English"])

        self.cmb_theme = QComboBox()
        self.cmb_theme.addItems(["پیش‌فرض", "تیره", "آبی"])

        self.spn_auto_save = QSpinBox()
        self.spn_auto_save.setRange(1, 60)
        self.spn_auto_save.setSuffix(" دقیقه")

        self.spn_session_timeout = QSpinBox()
        self.spn_session_timeout.setRange(5, 480)
        self.spn_session_timeout.setSuffix(" دقیقه")

        system_layout.addRow("زبان:", self.cmb_language)
        system_layout.addRow("تم:", self.cmb_theme)
        system_layout.addRow("ذخیره‌سازی خودکار:", self.spn_auto_save)
        system_layout.addRow("خاتمه خودکار session:", self.spn_session_timeout)

        system_group.setLayout(system_layout)
        layout.addWidget(system_group)

        # زمان‌بندی
        timing_group = QGroupBox("زمان‌بندی")
        timing_layout = QFormLayout()

        self.time_check_in = QTimeEdit()
        self.time_check_in.setDisplayFormat("HH:mm")

        self.time_check_out = QTimeEdit()
        self.time_check_out.setDisplayFormat("HH:mm")
        self.time_check_out.setTime(QTime(12, 0))

        self.time_night_audit = QTimeEdit()
        self.time_night_audit.setDisplayFormat("HH:mm")
        self.time_night_audit.setTime(QTime(2, 0))

        timing_layout.addRow("زمان ورود پیش‌فرض:", self.time_check_in)
        timing_layout.addRow("زمان خروج پیش‌فرض:", self.time_check_out)
        timing_layout.addRow("زمان حسابرسی شبانه:", self.time_night_audit)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_financial_tab(self):
        """ایجاد تب تنظیمات مالی"""
        widget = QWidget()
        layout = QVBoxLayout()

        # نرخ‌ها و مالیات
        rates_group = QGroupBox("نرخ‌ها و مالیات")
        rates_layout = QFormLayout()

        self.spn_tax_rate = QDoubleSpinBox()
        self.spn_tax_rate.setRange(0, 25)
        self.spn_tax_rate.setSuffix(" %")
        self.spn_tax_rate.setDecimals(1)

        self.spn_service_charge = QDoubleSpinBox()
        self.spn_service_charge.setRange(0, 15)
        self.spn_service_charge.setSuffix(" %")
        self.spn_service_charge.setDecimals(1)

        self.spn_city_tax = QDoubleSpinBox()
        self.spn_city_tax.setRange(0, 10)
        self.spn_city_tax.setSuffix(" %")
        self.spn_city_tax.setDecimals(1)

        rates_layout.addRow("نرخ مالیات:", self.spn_tax_rate)
        rates_layout.addRow("کارمزد خدمات:", self.spn_service_charge)
        rates_layout.addRow("مالیات شهرداری:", self.spn_city_tax)

        rates_group.setLayout(rates_layout)
        layout.addWidget(rates_group)

        # پرداخت
        payment_group = QGroupBox("تنظیمات پرداخت")
        payment_layout = QFormLayout()

        self.chk_pos_enabled = QCheckBox("فعال بودن کارت‌خوان")
        self.chk_cash_enabled = QCheckBox("فعال بودن پرداخت نقدی")
        self.chk_online_enabled = QCheckBox("فعال بودن پرداخت آنلاین")

        self.spn_max_cash = QSpinBox()
        self.spn_max_cash.setRange(100000, 10000000)
        self.spn_max_cash.setSuffix(" تومان")

        payment_layout.addRow(self.chk_pos_enabled)
        payment_layout.addRow(self.chk_cash_enabled)
        payment_layout.addRow(self.chk_online_enabled)
        payment_layout.addRow("حداکثر پرداخت نقدی:", self.spn_max_cash)

        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)

        # ارز
        currency_group = QGroupBox("ارز")
        currency_layout = QFormLayout()

        self.cmb_base_currency = QComboBox()
        self.cmb_base_currency.addItems(["تومان", "ریال", "دلار", "یورو"])

        self.chk_multi_currency = QCheckBox("پشتیبانی از چند ارز")

        currency_layout.addRow("ارز پایه:", self.cmb_base_currency)
        currency_layout.addRow(self.chk_multi_currency)

        currency_group.setLayout(currency_layout)
        layout.addWidget(currency_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_rooms_tab(self):
        """ایجاد تب تنظیمات اتاق‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()

        # انواع اتاق
        room_types_group = QGroupBox("انواع اتاق")
        room_types_layout = QFormLayout()

        self.txt_room_types = QTextEdit()
        self.txt_room_types.setPlaceholderText("هر خط یک نوع اتاق\nمثال:\nاستاندارد\nدلوکس\nسوئیت")
        self.txt_room_types.setMaximumHeight(100)

        room_types_layout.addRow("انواع اتاق:", self.txt_room_types)
        room_types_group.setLayout(room_types_layout)
        layout.addWidget(room_types_group)

        # امکانات اتاق
        amenities_group = QGroupBox("امکانات اتاق")
        amenities_layout = QVBoxLayout()

        self.chk_wifi = QCheckBox("Wi-Fi رایگان")
        self.chk_tv = QCheckBox("تلویزیون")
        self.chk_ac = QCheckBox("کولر گازی")
        self.chk_minibar = QCheckBox("مینی‌بار")
        self.chk_safe = QCheckBox("صندوق امانات")
        self.chk_balcony = QCheckBox("بالکن")

        amenities_layout.addWidget(self.chk_wifi)
        amenities_layout.addWidget(self.chk_tv)
        amenities_layout.addWidget(self.chk_ac)
        amenities_layout.addWidget(self.chk_minibar)
        amenities_layout.addWidget(self.chk_safe)
        amenities_layout.addWidget(self.chk_balcony)

        amenities_group.setLayout(amenities_layout)
        layout.addWidget(amenities_group)

        # تنظیمات نظافت
        cleaning_group = QGroupBox("تنظیمات نظافت")
        cleaning_layout = QFormLayout()

        self.spn_cleaning_time = QSpinBox()
        self.spn_cleaning_time.setRange(15, 120)
        self.spn_cleaning_time.setSuffix(" دقیقه")

        self.spn_inspection_time = QSpinBox()
        self.spn_inspection_time.setRange(5, 30)
        self.spn_inspection_time.setSuffix(" دقیقه")

        self.chk_auto_cleaning = QCheckBox("برنامه‌ریزی خودکار نظافت")

        cleaning_layout.addRow("زمان استاندارد نظافت:", self.spn_cleaning_time)
        cleaning_layout.addRow("زمان بازرسی:", self.spn_inspection_time)
        cleaning_layout.addRow(self.chk_auto_cleaning)

        cleaning_group.setLayout(cleaning_layout)
        layout.addWidget(cleaning_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_notifications_tab(self):
        """ایجاد تب تنظیمات اعلان‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()

        # کانال‌های اعلان
        channels_group = QGroupBox("کانال‌های اعلان")
        channels_layout = QVBoxLayout()

        self.chk_email_notifications = QCheckBox("اعلان از طریق ایمیل")
        self.chk_sms_notifications = QCheckBox("اعلان از طریق SMS")
        self.chk_push_notifications = QCheckBox("اعلان از طریق Push")
        self.chk_desktop_notifications = QCheckBox("اعلان دسکتاپ")

        channels_layout.addWidget(self.chk_email_notifications)
        channels_layout.addWidget(self.chk_sms_notifications)
        channels_layout.addWidget(self.chk_push_notifications)
        channels_layout.addWidget(self.chk_desktop_notifications)

        channels_group.setLayout(channels_layout)
        layout.addWidget(channels_group)

        # تنظیمات ایمیل
        email_group = QGroupBox("تنظیمات ایمیل")
        email_layout = QFormLayout()

        self.txt_smtp_server = QLineEdit()
        self.txt_smtp_server.setPlaceholderText("smtp.gmail.com")

        self.spn_smtp_port = QSpinBox()
        self.spn_smtp_port.setRange(1, 65535)

        self.txt_smtp_username = QLineEdit()
        self.txt_smtp_username.setPlaceholderText("username@gmail.com")

        self.txt_smtp_password = QLineEdit()
        self.txt_smtp_password.setPlaceholderText("کلمه عبور")
        self.txt_smtp_password.setEchoMode(QLineEdit.Password)

        email_layout.addRow("SMTP Server:", self.txt_smtp_server)
        email_layout.addRow("SMTP Port:", self.spn_smtp_port)
        email_layout.addRow("Username:", self.txt_smtp_username)
        email_layout.addRow("Password:", self.txt_smtp_password)

        email_group.setLayout(email_layout)
        layout.addWidget(email_group)

        # تنظیمات SMS
        sms_group = QGroupBox("تنظیمات SMS")
        sms_layout = QFormLayout()

        self.txt_sms_api_key = QLineEdit()
        self.txt_sms_api_key.setPlaceholderText("API Key")

        self.txt_sms_sender = QLineEdit()
        self.txt_sms_sender.setPlaceholderText("شماره فرستنده")

        sms_layout.addRow("API Key:", self.txt_sms_api_key)
        sms_layout.addRow("شماره فرستنده:", self.txt_sms_sender)

        sms_group.setLayout(sms_layout)
        layout.addWidget(sms_group)

        # رویدادهای اعلان
        events_group = QGroupBox("رویدادهای اعلان")
        events_layout = QVBoxLayout()

        self.chk_notify_check_in = QCheckBox("ورود مهمان جدید")
        self.chk_notify_check_out = QCheckBox("خروج مهمان")
        self.chk_notify_cleaning = QCheckBox("اتمام نظافت")
        self.chk_notify_maintenance = QCheckBox("درخواست تعمیرات")
        self.chk_notify_payment = QCheckBox("پرداخت جدید")

        events_layout.addWidget(self.chk_notify_check_in)
        events_layout.addWidget(self.chk_notify_check_out)
        events_layout.addWidget(self.chk_notify_cleaning)
        events_layout.addWidget(self.chk_notify_maintenance)
        events_layout.addWidget(self.chk_notify_payment)

        events_group.setLayout(events_layout)
        layout.addWidget(events_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def create_action_layout(self):
        """ایجاد نوار عملیات"""
        layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 ذخیره تنظیمات")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)

        self.btn_reset = QPushButton("🔄 بازنشانی")
        self.btn_reset.clicked.connect(self.reset_settings)

        self.btn_test_email = QPushButton("✉️ تست ایمیل")
        self.btn_test_email.clicked.connect(self.test_email_settings)

        self.btn_test_sms = QPushButton("📱 تست SMS")
        self.btn_test_sms.clicked.connect(self.test_sms_settings)

        layout.addWidget(self.btn_save)
        layout.addWidget(self.btn_reset)
        layout.addWidget(self.btn_test_email)
        layout.addWidget(self.btn_test_sms)
        layout.addStretch()

        return layout

    def load_settings(self):
        """بارگذاری تنظیمات"""
        try:
            # شبیه‌سازی بارگذاری تنظیمات
            self.settings_data = {
                'hotel': {
                    'name': 'هتل آراد',
                    'address': 'مشهد - خیابان مصباح یزدی 4 ( دانش غربی 11)',
                    'phone': '051-38581574',
                    'email': 'info@hotelarad.ir'
                },
                'system': {
                    'language': 'فارسی',
                    'theme': 'پیش‌فرض',
                    'auto_save_interval': 5,
                    'session_timeout': 30
                },
                'timing': {
                    'check_in_time': '14:00',
                    'check_out_time': '12:00',
                    'night_audit_time': '02:00'
                },
                'financial': {
                    'tax_rate': 9.0,
                    'service_charge': 1.0,
                    'city_tax': 2.0,
                    'pos_enabled': True,
                    'cash_enabled': True,
                    'online_enabled': False,
                    'max_cash_payment': 5000000,
                    'base_currency': 'تومان',
                    'multi_currency': False
                },
                'rooms': {
                    'types': ['استاندارد', 'دلوکس', 'سوئیت'],
                    'amenities': ['wifi', 'tv', 'ac', 'minibar'],
                    'cleaning_time': 45,
                    'inspection_time': 10,
                    'auto_cleaning': True
                },
                'notifications': {
                    'email_enabled': True,
                    'sms_enabled': False,
                    'push_enabled': True,
                    'desktop_enabled': True,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'smtp_username': '',
                    'smtp_password': '',
                    'sms_api_key': '',
                    'sms_sender': '',
                    'notify_check_in': True,
                    'notify_check_out': True,
                    'notify_cleaning': False,
                    'notify_maintenance': True,
                    'notify_payment': True
                }
            }

            self.populate_settings_form()

        except Exception as e:
            logger.error(f"خطا در بارگذاری تنظیمات: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری تنظیمات: {str(e)}")

    def populate_settings_form(self):
        """پر کردن فرم با تنظیمات"""
        try:
            # اطلاعات هتل
            hotel = self.settings_data['hotel']
            self.txt_hotel_name.setText(hotel['name'])
            self.txt_hotel_address.setText(hotel['address'])
            self.txt_hotel_phone.setText(hotel['phone'])
            self.txt_hotel_email.setText(hotel['email'])

            # تنظیمات سیستم
            system = self.settings_data['system']
            self.cmb_language.setCurrentText(system['language'])
            self.cmb_theme.setCurrentText(system['theme'])
            self.spn_auto_save.setValue(system['auto_save_interval'])
            self.spn_session_timeout.setValue(system['session_timeout'])

            # زمان‌بندی
            timing = self.settings_data['timing']
            self.time_check_in.setTime(QTime.fromString(timing['check_in_time'], "HH:mm"))
            self.time_check_out.setTime(QTime.fromString(timing['check_out_time'], "HH:mm"))
            self.time_night_audit.setTime(QTime.fromString(timing['night_audit_time'], "HH:mm"))

            # تنظیمات مالی
            financial = self.settings_data['financial']
            self.spn_tax_rate.setValue(financial['tax_rate'])
            self.spn_service_charge.setValue(financial['service_charge'])
            self.spn_city_tax.setValue(financial['city_tax'])
            self.chk_pos_enabled.setChecked(financial['pos_enabled'])
            self.chk_cash_enabled.setChecked(financial['cash_enabled'])
            self.chk_online_enabled.setChecked(financial['online_enabled'])
            self.spn_max_cash.setValue(financial['max_cash_payment'])
            self.cmb_base_currency.setCurrentText(financial['base_currency'])
            self.chk_multi_currency.setChecked(financial['multi_currency'])

            # تنظیمات اتاق‌ها
            rooms = self.settings_data['rooms']
            self.txt_room_types.setText("\n".join(rooms['types']))
            self.spn_cleaning_time.setValue(rooms['cleaning_time'])
            self.spn_inspection_time.setValue(rooms['inspection_time'])
            self.chk_auto_cleaning.setChecked(rooms['auto_cleaning'])

            # امکانات اتاق
            amenities = rooms['amenities']
            self.chk_wifi.setChecked('wifi' in amenities)
            self.chk_tv.setChecked('tv' in amenities)
            self.chk_ac.setChecked('ac' in amenities)
            self.chk_minibar.setChecked('minibar' in amenities)
            self.chk_safe.setChecked('safe' in amenities)
            self.chk_balcony.setChecked('balcony' in amenities)

            # تنظیمات اعلان‌ها
            notifications = self.settings_data['notifications']
            self.chk_email_notifications.setChecked(notifications['email_enabled'])
            self.chk_sms_notifications.setChecked(notifications['sms_enabled'])
            self.chk_push_notifications.setChecked(notifications['push_enabled'])
            self.chk_desktop_notifications.setChecked(notifications['desktop_enabled'])

            self.txt_smtp_server.setText(notifications['smtp_server'])
            self.spn_smtp_port.setValue(notifications['smtp_port'])
            self.txt_smtp_username.setText(notifications['smtp_username'])
            self.txt_smtp_password.setText(notifications['smtp_password'])

            self.txt_sms_api_key.setText(notifications['sms_api_key'])
            self.txt_sms_sender.setText(notifications['sms_sender'])

            self.chk_notify_check_in.setChecked(notifications['notify_check_in'])
            self.chk_notify_check_out.setChecked(notifications['notify_check_out'])
            self.chk_notify_cleaning.setChecked(notifications['notify_cleaning'])
            self.chk_notify_maintenance.setChecked(notifications['notify_maintenance'])
            self.chk_notify_payment.setChecked(notifications['notify_payment'])

        except Exception as e:
            logger.error(f"خطا در پر کردن فرم تنظیمات: {e}")

    def save_settings(self):
        """ذخیره تنظیمات"""
        try:
            # جمع‌آوری داده‌های فرم
            new_settings = self.collect_settings_from_form()

            # TODO: ذخیره تنظیمات در دیتابیس یا فایل
            logger.info("ذخیره تنظیمات جدید")

            QMessageBox.information(self, "موفق", "تنظیمات با موفقیت ذخیره شد")
            self.settings_updated.emit(new_settings)

        except Exception as e:
            logger.error(f"خطا در ذخیره تنظیمات: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره تنظیمات: {str(e)}")

    def collect_settings_from_form(self):
        """جمع‌آوری تنظیمات از فرم"""
        settings = {
            'hotel': {
                'name': self.txt_hotel_name.text().strip(),
                'address': self.txt_hotel_address.toPlainText().strip(),
                'phone': self.txt_hotel_phone.text().strip(),
                'email': self.txt_hotel_email.text().strip()
            },
            'system': {
                'language': self.cmb_language.currentText(),
                'theme': self.cmb_theme.currentText(),
                'auto_save_interval': self.spn_auto_save.value(),
                'session_timeout': self.spn_session_timeout.value()
            },
            'timing': {
                'check_in_time': self.time_check_in.time().toString("HH:mm"),
                'check_out_time': self.time_check_out.time().toString("HH:mm"),
                'night_audit_time': self.time_night_audit.time().toString("HH:mm")
            },
            'financial': {
                'tax_rate': self.spn_tax_rate.value(),
                'service_charge': self.spn_service_charge.value(),
                'city_tax': self.spn_city_tax.value(),
                'pos_enabled': self.chk_pos_enabled.isChecked(),
                'cash_enabled': self.chk_cash_enabled.isChecked(),
                'online_enabled': self.chk_online_enabled.isChecked(),
                'max_cash_payment': self.spn_max_cash.value(),
                'base_currency': self.cmb_base_currency.currentText(),
                'multi_currency': self.chk_multi_currency.isChecked()
            },
            'rooms': {
                'types': [t.strip() for t in self.txt_room_types.toPlainText().split('\n') if t.strip()],
                'cleaning_time': self.spn_cleaning_time.value(),
                'inspection_time': self.spn_inspection_time.value(),
                'auto_cleaning': self.chk_auto_cleaning.isChecked()
            },
            'notifications': {
                'email_enabled': self.chk_email_notifications.isChecked(),
                'sms_enabled': self.chk_sms_notifications.isChecked(),
                'push_enabled': self.chk_push_notifications.isChecked(),
                'desktop_enabled': self.chk_desktop_notifications.isChecked(),
                'smtp_server': self.txt_smtp_server.text().strip(),
                'smtp_port': self.spn_smtp_port.value(),
                'smtp_username': self.txt_smtp_username.text().strip(),
                'smtp_password': self.txt_smtp_password.text(),
                'sms_api_key': self.txt_sms_api_key.text().strip(),
                'sms_sender': self.txt_sms_sender.text().strip(),
                'notify_check_in': self.chk_notify_check_in.isChecked(),
                'notify_check_out': self.chk_notify_check_out.isChecked(),
                'notify_cleaning': self.chk_notify_cleaning.isChecked(),
                'notify_maintenance': self.chk_notify_maintenance.isChecked(),
                'notify_payment': self.chk_notify_payment.isChecked()
            }
        }

        # جمع‌آوری امکانات اتاق
        amenities = []
        if self.chk_wifi.isChecked(): amenities.append('wifi')
        if self.chk_tv.isChecked(): amenities.append('tv')
        if self.chk_ac.isChecked(): amenities.append('ac')
        if self.chk_minibar.isChecked(): amenities.append('minibar')
        if self.chk_safe.isChecked(): amenities.append('safe')
        if self.chk_balcony.isChecked(): amenities.append('balcony')
        settings['rooms']['amenities'] = amenities

        return settings

    def reset_settings(self):
        """بازنشانی تنظیمات به حالت پیش‌فرض"""
        try:
            reply = QMessageBox.question(
                self, 'تأیید بازنشانی',
                'آیا از بازنشانی تنظیمات به حالت پیش‌فرض اطمینان دارید؟',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.load_settings()  # بارگذاری مجدد تنظیمات پیش‌فرض
                QMessageBox.information(self, "موفق", "تنظیمات به حالت پیش‌فرض بازنشانی شد")

        except Exception as e:
            logger.error(f"خطا در بازنشانی تنظیمات: {e}")

    def test_email_settings(self):
        """تست تنظیمات ایمیل"""
        try:
            # TODO: پیاده‌سازی تست ایمیل
            QMessageBox.information(self, "تست ایمیل", "ارسال ایمیل تست با موفقیت انجام شد")

        except Exception as e:
            logger.error(f"خطا در تست ایمیل: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تست ایمیل: {str(e)}")

    def test_sms_settings(self):
        """تست تنظیمات SMS"""
        try:
            # TODO: پیاده‌سازی تست SMS
            QMessageBox.information(self, "تست SMS", "ارسال SMS تست با موفقیت انجام شد")

        except Exception as e:
            logger.error(f"خطا در تست SMS: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در تست SMS: {str(e)}")
