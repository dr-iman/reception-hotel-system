# app/utils/backup_utils.py
"""
ابزارهای کمکی برای پشتیبان‌گیری و بازیابی
"""

import logging
import os
import zipfile
import shutil
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import tempfile

try:
    import cryptography
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)

class BackupManager:
    """مدیریت پیشرفته پشتیبان‌گیری"""

    def __init__(self, backup_dir: str = None):
        self.backup_dir = backup_dir or os.path.join('data', 'backups')
        self.temp_dir = os.path.join('data', 'temp')

        # ایجاد پوشه‌های مورد نیاز
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)

    def compress_files(self, files: List[str], output_path: str) -> bool:
        """
        فشرده‌سازی فایل‌ها به فرمت ZIP

        Args:
            files: لیست مسیر فایل‌ها برای فشرده‌سازی
            output_path: مسیر فایل خروجی

        Returns:
            bool: موفقیت آمیز بودن عملیات
        """

        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    if os.path.exists(file_path):
                        # اضافه کردن فایل به آرشیو
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)

                        logger.debug(f"فایل {file_path} به آرشیو اضافه شد")
                    else:
                        logger.warning(f"فایل {file_path} یافت نشد")

            logger.info(f"فشرده‌سازی با موفقیت انجام شد: {output_path}")
            return True

        except Exception as e:
            logger.error(f"خطا در فشرده‌سازی فایل‌ها: {e}")
            return False

    def encrypt_data(self, data: bytes, password: str) -> Optional[bytes]:
        """
        رمزنگاری داده‌ها با استفاده از رمز عبور

        Args:
            data: داده برای رمزنگاری
            password: رمز عبور

        Returns:
            Optional[bytes]: داده رمزنگاری شده یا None در صورت خطا
        """

        if not CRYPTO_AVAILABLE:
            logger.error("کتابخانه cryptography برای رمزنگاری در دسترس نیست")
            return None

        try:
            # تولید کلید از رمز عبور
            password_bytes = password.encode()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

            # رمزنگاری داده
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data)

            # ترکیب salt و داده رمزنگاری شده
            result = salt + encrypted_data

            return result

        except Exception as e:
            logger.error(f"خطا در رمزنگاری داده: {e}")
            return None

    def decrypt_data(self, encrypted_data: bytes, password: str) -> Optional[bytes]:
        """
        رمزگشایی داده‌های رمزنگاری شده

        Args:
            encrypted_data: داده رمزنگاری شده
            password: رمز عبور

        Returns:
            Optional[bytes]: داده رمزگشایی شده یا None در صورت خطا
        """

        if not CRYPTO_AVAILABLE:
            logger.error("کتابخانه cryptography برای رمزگشایی در دسترس نیست")
            return None

        try:
            # استخراج salt و داده رمزنگاری شده
            salt = encrypted_data[:16]
            actual_encrypted = encrypted_data[16:]

            # تولید کلید از رمز عبور
            password_bytes = password.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

            # رمزگشایی داده
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(actual_encrypted)

            return decrypted_data

        except Exception as e:
            logger.error(f"خطا در رمزگشایی داده: {e}")
            return None

    def create_backup_snapshot(self,
                             include_database: bool = True,
                             include_files: bool = True,
                             include_config: bool = True,
                             include_logs: bool = False,
                             backup_name: str = None,
                             encrypt: bool = False,
                             password: str = None) -> Dict[str, Any]:
        """
        ایجاد snapshot از سیستم

        Args:
            include_database: آیا از دیتابیس پشتیبان گرفته شود؟
            include_files: آیا از فایل‌های سیستم پشتیبان گرفته شود؟
            include_config: آیا از تنظیمات پشتیبان گرفته شود؟
            include_logs: آیا از لاگ‌ها پشتیبان گرفته شود؟
            backup_name: نام پشتیبان
            encrypt: آیا پشتیبان رمزنگاری شود؟
            password: رمز عبور برای رمزنگاری

        Returns:
            Dict[str, Any]: اطلاعات پشتیبان ایجاد شده
        """

        try:
            # تعیین نام پشتیبان
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if not backup_name:
                backup_name = f"backup_{timestamp}"

            # ایجاد پوشه موقت برای پشتیبان
            temp_backup_dir = os.path.join(self.temp_dir, backup_name)
            os.makedirs(temp_backup_dir, exist_ok=True)

            files_to_backup = []
            metadata = {
                'backup_name': backup_name,
                'timestamp': datetime.now().isoformat(),
                'includes': {},
                'file_hashes': {},
                'total_size': 0
            }

            # پشتیبان‌گیری از دیتابیس
            if include_database:
                db_backup_path = self._backup_database(temp_backup_dir)
                if db_backup_path:
                    files_to_backup.append(db_backup_path)
                    metadata['includes']['database'] = True
                    metadata['file_hashes']['database'] = self._calculate_file_hash(db_backup_path)

            # پشتیبان‌گیری از فایل‌های سیستم
            if include_files:
                system_files = self._backup_system_files(temp_backup_dir)
                files_to_backup.extend(system_files)
                metadata['includes']['files'] = True
                for file_path in system_files:
                    metadata['file_hashes'][os.path.basename(file_path)] = self._calculate_file_hash(file_path)

            # پشتیبان‌گیری از تنظیمات
            if include_config:
                config_backup_path = self._backup_config(temp_backup_dir)
                if config_backup_path:
                    files_to_backup.append(config_backup_path)
                    metadata['includes']['config'] = True
                    metadata['file_hashes']['config'] = self._calculate_file_hash(config_backup_path)

            # پشتیبان‌گیری از لاگ‌ها
            if include_logs:
                logs_backup_path = self._backup_logs(temp_backup_dir)
                if logs_backup_path:
                    files_to_backup.append(logs_backup_path)
                    metadata['includes']['logs'] = True
                    metadata['file_hashes']['logs'] = self._calculate_file_hash(logs_backup_path)

            # ذخیره metadata
            metadata_path = os.path.join(temp_backup_dir, 'backup_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            files_to_backup.append(metadata_path)

            # فشرده‌سازی پشتیبان
            backup_zip_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
            if self.compress_files(files_to_backup, backup_zip_path):
                metadata['backup_file'] = backup_zip_path
                metadata['backup_size'] = os.path.getsize(backup_zip_path)

                # رمزنگاری اگر درخواست شده
                if encrypt and password:
                    encrypted_path = backup_zip_path + '.encrypted'
                    with open(backup_zip_path, 'rb') as f:
                        original_data = f.read()

                    encrypted_data = self.encrypt_data(original_data, password)
                    if encrypted_data:
                        with open(encrypted_path, 'wb') as f:
                            f.write(encrypted_data)

                        # حذف فایل اصلی و استفاده از فایل رمزنگاری شده
                        os.remove(backup_zip_path)
                        backup_zip_path = encrypted_path
                        metadata['encrypted'] = True
                        metadata['backup_file'] = encrypted_path
                        metadata['backup_size'] = os.path.getsize(encrypted_path)

            # محاسبه hash نهایی
            metadata['backup_hash'] = self._calculate_file_hash(backup_zip_path)

            # پاکسازی پوشه موقت
            shutil.rmtree(temp_backup_dir)

            logger.info(f"پشتیبان با موفقیت ایجاد شد: {backup_zip_path}")
            return metadata

        except Exception as e:
            logger.error(f"خطا در ایجاد پشتیبان: {e}")
            return {}

    def verify_backup_integrity(self, backup_path: str, password: str = None) -> Tuple[bool, str]:
        """
        بررسی سلامت و یکپارچگی پشتیبان

        Args:
            backup_path: مسیر فایل پشتیبان
            password: رمز عبور برای پشتیبان‌های رمزنگاری شده

        Returns:
            Tuple[bool, str]: (سلامت پشتیبان, پیغام)
        """

        try:
            if not os.path.exists(backup_path):
                return False, "فایل پشتیبان یافت نشد"

            # بررسی فرمت فایل
            is_encrypted = backup_path.endswith('.encrypted')

            # رمزگشایی اگر لازم باشد
            if is_encrypted and not password:
                return False, "پشتیبان رمزنگاری شده است. رمز عبور required است."

            working_file = backup_path
            if is_encrypted and password:
                # رمزگشایی موقت
                with open(backup_path, 'rb') as f:
                    encrypted_data = f.read()

                decrypted_data = self.decrypt_data(encrypted_data, password)
                if not decrypted_data:
                    return False, "رمزگشایی ناموفق. رمز عبور نادرست است."

                # ایجاد فایل موقت رمزگشایی شده
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                temp_file.write(decrypted_data)
                temp_file.close()
                working_file = temp_file.name

            try:
                # بررسی یکپارچگی فایل ZIP
                with zipfile.ZipFile(working_file, 'r') as zipf:
                    # تست بازیابی
                    bad_file = zipf.testzip()
                    if bad_file is not None:
                        return False, f"فایل آسیب دیده در آرشیو: {bad_file}"

                    # بررسی وجود metadata
                    if 'backup_metadata.json' not in zipf.namelist():
                        return False, "فایل metadata در پشتیبان یافت نشد"

                    # خواندن metadata
                    with zipf.open('backup_metadata.json') as meta_file:
                        metadata = json.load(meta_file)

                    # بررسی hash فایل‌ها
                    for file_info in zipf.infolist():
                        if file_info.filename != 'backup_metadata.json':
                            with zipf.open(file_info.filename) as f:
                                file_data = f.read()
                                file_hash = hashlib.sha256(file_data).hexdigest()

                                expected_hash = metadata['file_hashes'].get(file_info.filename)
                                if expected_hash and file_hash != expected_hash:
                                    return False, f"hash فایل {file_info.filename} مطابقت ندارد"

                return True, "پشتیبان سالم و یکپارچه است"

            finally:
                # پاکسازی فایل موقت
                if is_encrypted and password and working_file != backup_path:
                    os.unlink(working_file)

        except Exception as e:
            logger.error(f"خطا در بررسی سلامت پشتیبان: {e}")
            return False, f"خطا در بررسی سلامت: {str(e)}"

    def _backup_database(self, backup_dir: str) -> Optional[str]:
        """پشتیبان‌گیری از دیتابیس"""
        try:
            # این بخش نیاز به پیاده‌سازی بر اساس نوع دیتابیس دارد
            # در اینجا یک نمونه ساده ارائه می‌شود

            backup_path = os.path.join(backup_dir, 'database_backup.sql')

            # شبیه‌سازی پشتیبان‌گیری از دیتابیس
            # در نسخه واقعی از pg_dump یا mysqldump استفاده می‌شود
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write("-- Database Backup\n")
                f.write(f"-- Generated at: {datetime.now().isoformat()}\n")
                f.write("-- This is a simulated database backup\n")

            return backup_path

        except Exception as e:
            logger.error(f"خطا در پشتیبان‌گیری از دیتابیس: {e}")
            return None

    def _backup_system_files(self, backup_dir: str) -> List[str]:
        """پشتیبان‌گیری از فایل‌های سیستم"""
        files_to_backup = []

        try:
            # پشتیبان‌گیری از فایل‌های پیکربندی
            config_files = [
                'config/database_config.py',
                'config/app_config.py',
                'config/payment_config.py'
            ]

            for config_file in config_files:
                if os.path.exists(config_file):
                    shutil.copy2(config_file, backup_dir)
                    files_to_backup.append(os.path.join(backup_dir, os.path.basename(config_file)))

            # پشتیبان‌گیری از فایل‌های مهم دیگر
            important_files = [
                'requirements.txt',
                'main.py'
            ]

            for important_file in important_files:
                if os.path.exists(important_file):
                    shutil.copy2(important_file, backup_dir)
                    files_to_backup.append(os.path.join(backup_dir, os.path.basename(important_file)))

            return files_to_backup

        except Exception as e:
            logger.error(f"خطا در پشتیبان‌گیری از فایل‌های سیستم: {e}")
            return []

    def _backup_config(self, backup_dir: str) -> Optional[str]:
        """پشتیبان‌گیری از تنظیمات"""
        try:
            config_backup_path = os.path.join(backup_dir, 'system_config.json')

            # جمع‌آوری تنظیمات سیستم
            system_config = {
                'backup_timestamp': datetime.now().isoformat(),
                'system_info': {
                    'python_version': os.sys.version,
                    'platform': os.sys.platform,
                    'working_directory': os.getcwd()
                },
                'environment_variables': dict(os.environ)
            }

            with open(config_backup_path, 'w', encoding='utf-8') as f:
                json.dump(system_config, f, ensure_ascii=False, indent=2)

            return config_backup_path

        except Exception as e:
            logger.error(f"خطا در پشتیبان‌گیری از تنظیمات: {e}")
            return None

    def _backup_logs(self, backup_dir: str) -> Optional[str]:
        """پشتیبان‌گیری از لاگ‌ها"""
        try:
            logs_backup_path = os.path.join(backup_dir, 'system_logs.zip')

            log_files = []
            log_dir = 'data/logs'
            if os.path.exists(log_dir):
                for log_file in os.listdir(log_dir):
                    if log_file.endswith('.log'):
                        log_files.append(os.path.join(log_dir, log_file))

            if log_files:
                self.compress_files(log_files, logs_backup_path)
                return logs_backup_path

            return None

        except Exception as e:
            logger.error(f"خطا در پشتیبان‌گیری از لاگ‌ها: {e}")
            return None

    def _calculate_file_hash(self, file_path: str) -> str:
        """محاسبه hash فایل"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"خطا در محاسبه hash فایل: {e}")
            return ""

# توابع مستقل برای استفاده آسان
def compress_files(files: List[str], output_path: str) -> bool:
    """
    فشرده‌سازی فایل‌ها

    Args:
        files: لیست مسیر فایل‌ها
        output_path: مسیر فایل خروجی

    Returns:
        bool: موفقیت آمیز بودن
    """
    manager = BackupManager()
    return manager.compress_files(files, output_path)

def encrypt_data(data: bytes, password: str) -> Optional[bytes]:
    """
    رمزنگاری داده‌ها

    Args:
        data: داده برای رمزنگاری
        password: رمز عبور

    Returns:
        Optional[bytes]: داده رمزنگاری شده
    """
    manager = BackupManager()
    return manager.encrypt_data(data, password)

def decrypt_data(encrypted_data: bytes, password: str) -> Optional[bytes]:
    """
    رمزگشایی داده‌ها

    Args:
        encrypted_data: داده رمزنگاری شده
        password: رمز عبور

    Returns:
        Optional[bytes]: داده رمزگشایی شده
    """
    manager = BackupManager()
    return manager.decrypt_data(encrypted_data, password)

def create_backup_snapshot(**kwargs) -> Dict[str, Any]:
    """
    ایجاد snapshot از سیستم

    Args:
        **kwargs: پارامترهای پشتیبان‌گیری

    Returns:
        Dict[str, Any]: اطلاعات پشتیبان
    """
    manager = BackupManager()
    return manager.create_backup_snapshot(**kwargs)

def verify_backup_integrity(backup_path: str, password: str = None) -> Tuple[bool, str]:
    """
    بررسی سلامت پشتیبان

    Args:
        backup_path: مسیر فایل پشتیبان
        password: رمز عبور

    Returns:
        Tuple[bool, str]: نتیجه بررسی
    """
    manager = BackupManager()
    return manager.verify_backup_integrity(backup_path, password)
