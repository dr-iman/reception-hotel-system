# app/views/widgets/admin/user_management.py
"""
ویجت مدیریت کاربران سیستم
"""

import logging
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QComboBox, QPushButton,
                            QMessageBox, QGroupBox, QTableWidget,
                            QTableWidgetItem, QHeaderView, QCheckBox,
                            QTabWidget, QTextEdit, QDateEdit)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QColor

logger = logging.getLogger(__name__)

class UserManagementWidget(QWidget):
    """ویجت مدیریت کاربران سیستم"""

    # سیگنال‌ها
    user_created = pyqtSignal(dict)
    user_updated = pyqtSignal(dict)
    user_deleted = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user_id = None
        self.users_data = []
        self.init_ui()
        self.load_users()

    def init_ui(self):
        """راه‌اندازی رابط کاربری"""
        main_layout = QVBoxLayout()

        # تب‌های مدیریت کاربران
        self.tabs = QTabWidget()

        # تب لیست کاربران
        self.users_list_tab = self.create_users_list_tab()
        self.tabs.addTab(self.users_list_tab, "👥 لیست کاربران")

        # تب ایجاد کاربر جدید
        self.create_user_tab = self.create_user_form_tab()
        self.tabs.addTab(self.create_user_tab, "➕ کاربر جدید")

        # تب تنظیمات دسترسی
        self.permissions_tab = self.create_permissions_tab()
        self.tabs.addTab(self.permissions_tab, "🔐 دسترسی‌ها")

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def create_users_list_tab(self):
        """ایجاد تب لیست کاربران"""
        widget = QWidget()
        layout = QVBoxLayout()

        # نوار جستجو و فیلتر
        search_layout = QHBoxLayout()

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("جستجوی کاربر...")
        self.txt_search.textChanged.connect(self.filter_users)

        self.cmb_role_filter = QComboBox()
        self.cmb_role_filter.addItems(["همه نقش‌ها", "مدیر", "پذیرش", "نظافت", "مهمان"])
        self.cmb_role_filter.currentTextChanged.connect(self.filter_users)

        self.cmb_status_filter = QComboBox()
        self.cmb_status_filter.addItems(["همه وضعیت‌ها", "فعال", "غیرفعال", "مسدود"])
        self.cmb_status_filter.currentTextChanged.connect(self.filter_users)

        search_layout.addWidget(QLabel("وضعیت:"))
        search_layout.addWidget(self.cmb_status_filter)
        search_layout.addWidget(QLabel("نقش:"))
        search_layout.addWidget(self.cmb_role_filter)
        search_layout.addWidget(self.txt_search)
        search_layout.addStretch()

        layout.addLayout(search_layout)

        # جدول کاربران
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(7)
        self.users_table.setHorizontalHeaderLabels([
            "ID", "نام کاربری", "نام کامل", "نقش", "وضعیت", "آخرین ورود", "عملیات"
        ])

        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)

        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # نام کاربری
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # نام کامل
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # نقش
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # وضعیت
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # آخرین ورود
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # عملیات

        layout.addWidget(self.users_table)

        widget.setLayout(layout)
        return widget

    def create_user_form_tab(self):
        """ایجاد تب فرم کاربر"""
        widget = QWidget()
        layout = QVBoxLayout()

        # فرم اطلاعات کاربر
        user_form_group = QGroupBox("اطلاعات کاربر")
        form_layout = QFormLayout()

        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("نام کاربری")

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("کلمه عبور")
        self.txt_password.setEchoMode(QLineEdit.Password)

        self.txt_confirm_password = QLineEdit()
        self.txt_confirm_password.setPlaceholderText("تکرار کلمه عبور")
        self.txt_confirm_password.setEchoMode(QLineEdit.Password)

        self.txt_full_name = QLineEdit()
        self.txt_full_name.setPlaceholderText("نام و نام خانوادگی")

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("ایمیل")

        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("تلفن همراه")

        self.cmb_role = QComboBox()
        self.cmb_role.addItems(["پذیرش", "نظافت", "تعمیرات", "مالی", "مدیر"])

        self.chk_active = QCheckBox("کاربر فعال")

        form_layout.addRow("نام کاربری:", self.txt_username)
        form_layout.addRow("کلمه عبور:", self.txt_password)
        form_layout.addRow("تکرار کلمه عبور:", self.txt_confirm_password)
        form_layout.addRow("نام کامل:", self.txt_full_name)
        form_layout.addRow("ایمیل:", self.txt_email)
        form_layout.addRow("تلفن:", self.txt_phone)
        form_layout.addRow("نقش:", self.cmb_role)
        form_layout.addRow(self.chk_active)

        user_form_group.setLayout(form_layout)
        layout.addWidget(user_form_group)

        # دکمه‌های عملیات
        button_layout = QHBoxLayout()

        self.btn_create_user = QPushButton("ایجاد کاربر")
        self.btn_create_user.clicked.connect(self.create_user)
        self.btn_create_user.setStyleSheet("background-color: #27ae60; color: white;")

        self.btn_clear_form = QPushButton("پاک کردن فرم")
        self.btn_clear_form.clicked.connect(self.clear_form)

        button_layout.addWidget(self.btn_create_user)
        button_layout.addWidget(self.btn_clear_form)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def create_permissions_tab(self):
        """ایجاد تب مدیریت دسترسی‌ها"""
        widget = QWidget()
        layout = QVBoxLayout()

        # انتخاب کاربر
        user_selection_layout = QHBoxLayout()

        self.cmb_user_select = QComboBox()
        self.cmb_user_select.currentTextChanged.connect(self.load_user_permissions)

        user_selection_layout.addWidget(QLabel("انتخاب کاربر:"))
        user_selection_layout.addWidget(self.cmb_user_select)
        user_selection_layout.addStretch()

        layout.addLayout(user_selection_layout)

        # دسترسی‌های ماژول‌ها
        permissions_group = QGroupBox("دسترسی‌های ماژول‌ها")
        permissions_layout = QVBoxLayout()

        # پذیرش
        reception_group = QGroupBox("ماژول پذیرش")
        reception_layout = QVBoxLayout()

        self.chk_reception_view = QCheckBox("مشاهده پذیرش")
        self.chk_reception_edit = QCheckBox("ویرایش پذیرش")
        self.chk_reception_delete = QCheckBox("حذف از پذیرش")

        reception_layout.addWidget(self.chk_reception_view)
        reception_layout.addWidget(self.chk_reception_edit)
        reception_layout.addWidget(self.chk_reception_delete)
        reception_group.setLayout(reception_layout)

        # مهمانان
        guests_group = QGroupBox("ماژول مهمانان")
        guests_layout = QVBoxLayout()

        self.chk_guests_view = QCheckBox("مشاهده مهمانان")
        self.chk_guests_edit = QCheckBox("ویرایش مهمانان")
        self.chk_guests_delete = QCheckBox("حذف مهمانان")

        guests_layout.addWidget(self.chk_guests_view)
        guests_layout.addWidget(self.chk_guests_edit)
        guests_layout.addWidget(self.chk_guests_delete)
        guests_group.setLayout(guests_layout)

        # اتاق‌ها
        rooms_group = QGroupBox("ماژول اتاق‌ها")
        rooms_layout = QVBoxLayout()

        self.chk_rooms_view = QCheckBox("مشاهده اتاق‌ها")
        self.chk_rooms_edit = QCheckBox("ویرایش اتاق‌ها")
        self.chk_rooms_assign = QCheckBox("تخصیص اتاق")

        rooms_layout.addWidget(self.chk_rooms_view)
        rooms_layout.addWidget(self.chk_rooms_edit)
        rooms_layout.addWidget(self.chk_rooms_assign)
        rooms_group.setLayout(rooms_layout)

        permissions_layout.addWidget(reception_group)
        permissions_layout.addWidget(guests_group)
        permissions_layout.addWidget(rooms_group)
        permissions_group.setLayout(permissions_layout)

        layout.addWidget(permissions_group)

        # دکمه ذخیره دسترسی‌ها
        self.btn_save_permissions = QPushButton("ذخیره دسترسی‌ها")
        self.btn_save_permissions.clicked.connect(self.save_permissions)
        self.btn_save_permissions.setEnabled(False)

        layout.addWidget(self.btn_save_permissions)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def load_users(self):
        """بارگذاری لیست کاربران"""
        try:
            # شبیه‌سازی داده‌های کاربران
            self.users_data = [
                {
                    'id': 1,
                    'username': 'admin',
                    'full_name': 'مدیر سیستم',
                    'role': 'مدیر',
                    'status': 'فعال',
                    'last_login': '۱۴۰۲/۱۰/۱۵ ۱۰:۳۰',
                    'email': 'admin@hotel.com',
                    'phone': '09123456789'
                },
                {
                    'id': 2,
                    'username': 'reception1',
                    'full_name': 'کاربر پذیرش',
                    'role': 'پذیرش',
                    'status': 'فعال',
                    'last_login': '۱۴۰۲/۱۰/۱۵ ۰۹:۱۵',
                    'email': 'reception@hotel.com',
                    'phone': '09123456780'
                }
            ]

            self.populate_users_table()
            self.populate_user_combo()

        except Exception as e:
            logger.error(f"خطا در بارگذاری کاربران: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در بارگذاری کاربران: {str(e)}")

    def populate_users_table(self):
        """پر کردن جدول کاربران"""
        self.users_table.setRowCount(len(self.users_data))

        for row, user in enumerate(self.users_data):
            # ID
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))

            # نام کاربری
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))

            # نام کامل
            self.users_table.setItem(row, 2, QTableWidgetItem(user['full_name']))

            # نقش
            role_item = QTableWidgetItem(user['role'])
            role_item.setForeground(self.get_role_color(user['role']))
            self.users_table.setItem(row, 3, role_item)

            # وضعیت
            status_item = QTableWidgetItem(user['status'])
            status_item.setForeground(self.get_status_color(user['status']))
            self.users_table.setItem(row, 4, status_item)

            # آخرین ورود
            self.users_table.setItem(row, 5, QTableWidgetItem(user['last_login']))

            # عملیات
            operations_widget = self.create_operations_widget(user['id'])
            self.users_table.setCellWidget(row, 6, operations_widget)

    def create_operations_widget(self, user_id):
        """ایجاد ویجت عملیات برای هر کاربر"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        btn_edit = QPushButton("ویرایش")
        btn_edit.setFixedSize(60, 25)
        btn_edit.setStyleSheet("background-color: #3498db; color: white;")
        btn_edit.clicked.connect(lambda: self.edit_user(user_id))

        btn_delete = QPushButton("حذف")
        btn_delete.setFixedSize(60, 25)
        btn_delete.setStyleSheet("background-color: #e74c3c; color: white;")
        btn_delete.clicked.connect(lambda: self.delete_user(user_id))

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        layout.addStretch()

        widget.setLayout(layout)
        return widget

    def get_role_color(self, role):
        """رنگ بر اساس نقش"""
        colors = {
            'مدیر': QColor(231, 76, 60),
            'پذیرش': QColor(52, 152, 219),
            'نظافت': QColor(155, 89, 182),
            'تعمیرات': QColor(230, 126, 34),
            'مالی': QColor(39, 174, 96)
        }
        return colors.get(role, QColor(149, 165, 166))

    def get_status_color(self, status):
        """رنگ بر اساس وضعیت"""
        colors = {
            'فعال': QColor(39, 174, 96),
            'غیرفعال': QColor(149, 165, 166),
            'مسدود': QColor(231, 76, 60)
        }
        return colors.get(status, QColor(149, 165, 166))

    def populate_user_combo(self):
        """پر کردن کامبوباکس کاربران"""
        self.cmb_user_select.clear()
        for user in self.users_data:
            self.cmb_user_select.addItem(f"{user['full_name']} ({user['username']})", user['id'])

    def filter_users(self):
        """فیلتر کاربران بر اساس جستجو"""
        search_text = self.txt_search.text().lower()
        role_filter = self.cmb_role_filter.currentText()
        status_filter = self.cmb_status_filter.currentText()

        filtered_users = self.users_data

        if search_text:
            filtered_users = [u for u in filtered_users if
                            search_text in u['username'].lower() or
                            search_text in u['full_name'].lower()]

        if role_filter != "همه نقش‌ها":
            filtered_users = [u for u in filtered_users if u['role'] == role_filter]

        if status_filter != "همه وضعیت‌ها":
            filtered_users = [u for u in filtered_users if u['status'] == status_filter]

        # به‌روزرسانی جدول
        self.users_table.setRowCount(len(filtered_users))
        for row, user in enumerate(filtered_users):
            self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.users_table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.users_table.setItem(row, 2, QTableWidgetItem(user['full_name']))

            role_item = QTableWidgetItem(user['role'])
            role_item.setForeground(self.get_role_color(user['role']))
            self.users_table.setItem(row, 3, role_item)

            status_item = QTableWidgetItem(user['status'])
            status_item.setForeground(self.get_status_color(user['status']))
            self.users_table.setItem(row, 4, status_item)

            self.users_table.setItem(row, 5, QTableWidgetItem(user['last_login']))

    def create_user(self):
        """ایجاد کاربر جدید"""
        try:
            # اعتبارسنجی فرم
            if not self.validate_user_form():
                return

            # ایجاد کاربر
            user_data = {
                'username': self.txt_username.text().strip(),
                'password': self.txt_password.text(),
                'full_name': self.txt_full_name.text().strip(),
                'email': self.txt_email.text().strip(),
                'phone': self.txt_phone.text().strip(),
                'role': self.cmb_role.currentText(),
                'active': self.chk_active.isChecked()
            }

            # TODO: ارسال به سرویس کاربران
            logger.info(f"ایجاد کاربر جدید: {user_data['username']}")

            QMessageBox.information(self, "موفق", "کاربر جدید با موفقیت ایجاد شد")
            self.clear_form()
            self.load_users()  # بارگذاری مجدد لیست
            self.user_created.emit(user_data)

        except Exception as e:
            logger.error(f"خطا در ایجاد کاربر: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ایجاد کاربر: {str(e)}")

    def validate_user_form(self):
        """اعتبارسنجی فرم کاربر"""
        errors = []

        if not self.txt_username.text().strip():
            errors.append("نام کاربری الزامی است")

        if not self.txt_password.text():
            errors.append("کلمه عبور الزامی است")

        if self.txt_password.text() != self.txt_confirm_password.text():
            errors.append("کلمه عبور و تکرار آن مطابقت ندارند")

        if not self.txt_full_name.text().strip():
            errors.append("نام کامل الزامی است")

        if errors:
            QMessageBox.warning(self, "خطا در فرم", "\n".join(errors))
            return False

        return True

    def clear_form(self):
        """پاک کردن فرم"""
        self.txt_username.clear()
        self.txt_password.clear()
        self.txt_confirm_password.clear()
        self.txt_full_name.clear()
        self.txt_email.clear()
        self.txt_phone.clear()
        self.cmb_role.setCurrentIndex(0)
        self.chk_active.setChecked(True)

    def edit_user(self, user_id):
        """ویرایش کاربر"""
        try:
            user = next((u for u in self.users_data if u['id'] == user_id), None)
            if user:
                # پر کردن فرم با اطلاعات کاربر
                self.tabs.setCurrentIndex(1)  # رفتن به تب ایجاد کاربر

                self.txt_username.setText(user['username'])
                self.txt_full_name.setText(user['full_name'])
                self.txt_email.setText(user['email'])
                self.txt_phone.setText(user['phone'])

                # تغییر متن دکمه
                self.btn_create_user.setText("بروزرسانی کاربر")
                self.current_user_id = user_id

        except Exception as e:
            logger.error(f"خطا در ویرایش کاربر: {e}")

    def delete_user(self, user_id):
        """حذف کاربر"""
        try:
            reply = QMessageBox.question(
                self, 'تأیید حذف',
                'آیا از حذف این کاربر اطمینان دارید؟',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # TODO: حذف کاربر از سرویس
                logger.info(f"حذف کاربر با ID: {user_id}")

                QMessageBox.information(self, "موفق", "کاربر با موفقیت حذف شد")
                self.load_users()  # بارگذاری مجدد لیست
                self.user_deleted.emit(user_id)

        except Exception as e:
            logger.error(f"خطا در حذف کاربر: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در حذف کاربر: {str(e)}")

    def load_user_permissions(self):
        """بارگذاری دسترسی‌های کاربر انتخاب شده"""
        try:
            user_id = self.cmb_user_select.currentData()
            if user_id:
                # TODO: بارگذاری دسترسی‌ها از سرویس
                self.btn_save_permissions.setEnabled(True)
            else:
                self.btn_save_permissions.setEnabled(False)

        except Exception as e:
            logger.error(f"خطا در بارگذاری دسترسی‌ها: {e}")

    def save_permissions(self):
        """ذخیره دسترسی‌های کاربر"""
        try:
            user_id = self.cmb_user_select.currentData()
            permissions = {
                'reception': {
                    'view': self.chk_reception_view.isChecked(),
                    'edit': self.chk_reception_edit.isChecked(),
                    'delete': self.chk_reception_delete.isChecked()
                },
                'guests': {
                    'view': self.chk_guests_view.isChecked(),
                    'edit': self.chk_guests_edit.isChecked(),
                    'delete': self.chk_guests_delete.isChecked()
                },
                'rooms': {
                    'view': self.chk_rooms_view.isChecked(),
                    'edit': self.chk_rooms_edit.isChecked(),
                    'assign': self.chk_rooms_assign.isChecked()
                }
            }

            # TODO: ذخیره دسترسی‌ها در سرویس
            logger.info(f"ذخیره دسترسی‌های کاربر {user_id}: {permissions}")

            QMessageBox.information(self, "موفق", "دسترسی‌ها با موفقیت ذخیره شدند")

        except Exception as e:
            logger.error(f"خطا در ذخیره دسترسی‌ها: {e}")
            QMessageBox.critical(self, "خطا", f"خطا در ذخیره دسترسی‌ها: {str(e)}")
