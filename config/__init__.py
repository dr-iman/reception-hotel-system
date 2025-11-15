# config/__init__.py
"""
پیکربندی‌های اصلی سیستم پذیرش هتل
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import time

@dataclass
class DatabaseConfig:
    """پیکربندی دیتابیس PostgreSQL"""
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    database: str = os.getenv('DB_NAME', 'hotel_reception')
    username: str = os.getenv('DB_USER', 'postgres')
    password: str = os.getenv('DB_PASS', 'password')
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '20'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '30'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))

    @property
    def url(self) -> str:
        """ایجاد URL اتصال به دیتابیس"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class RedisConfig:
    """پیکربندی Redis برای کش و همگام‌سازی"""
    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    db: int = int(os.getenv('REDIS_DB', '0'))
    password: str = os.getenv('REDIS_PASS', '')
    socket_timeout: int = int(os.getenv('REDIS_TIMEOUT', '5'))
    health_check_interval: int = int(os.getenv('REDIS_HEALTH_CHECK', '30'))

    @property
    def connection_string(self) -> str:
        """ایجاد رشته اتصال به Redis"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"

@dataclass
class NetworkConfig:
    """پیکربندی شبکه و ارتباطات"""
    reservation_system_url: str = os.getenv('RESERVATION_URL', 'http://localhost:8000')
    api_timeout: int = int(os.getenv('API_TIMEOUT', '30'))
    retry_attempts: int = int(os.getenv('RETRY_ATTEMPTS', '3'))
    retry_delay: int = int(os.getenv('RETRY_DELAY', '5'))
    enable_ssl_verification: bool = os.getenv('SSL_VERIFICATION', 'True').lower() == 'true'

@dataclass
class PaymentConfig:
    """پیکربندی سیستم پرداخت"""
    # تنظیمات کارت‌خوان
    pos_enabled: bool = os.getenv('POS_ENABLED', 'True').lower() == 'true'
    pos_terminal_id: str = os.getenv('POS_TERMINAL_ID', '')
    pos_merchant_id: str = os.getenv('POS_MERCHANT_ID', '')
    pos_base_url: str = os.getenv('POS_BASE_URL', 'https://pos-api.example.com')

    # تنظیمات تست
    test_mode: bool = os.getenv('PAYMENT_TEST_MODE', 'True').lower() == 'true'
    test_success_card: str = os.getenv('TEST_SUCCESS_CARD', '1111')
    test_failure_card: str = os.getenv('TEST_FAILURE_CARD', '2222')

    # نرخ‌ها و کارمزدها
    commission_rate: float = float(os.getenv('COMMISSION_RATE', '0.01'))  # 1%
    tax_rate: float = float(os.getenv('TAX_RATE', '0.09'))  # 9%
    labor_rate: float = float(os.getenv('LABOR_RATE', '50000'))  # نرخ ساعتی کارگر

    # محدودیت‌ها
    max_cash_payment: float = float(os.getenv('MAX_CASH_PAYMENT', '10000000'))  # 10 میلیون
    daily_transaction_limit: float = float(os.getenv('DAILY_TRANSACTION_LIMIT', '50000000'))  # 50 میلیون

@dataclass
class HousekeepingConfig:
    """پیکربندی سیستم خانه‌داری"""
    # تنظیمات خودکار
    auto_cleaning_schedule: bool = os.getenv('AUTO_CLEANING', 'True').lower() == 'true'
    auto_inspection: bool = os.getenv('AUTO_INSPECTION', 'True').lower() == 'true'

    # زمان‌بندی
    check_out_time: str = os.getenv('CHECK_OUT_TIME', '12:00')
    cleaning_start_time: str = os.getenv('CLEANING_START_TIME', '08:00')
    cleaning_end_time: str = os.getenv('CLEANING_END_TIME', '18:00')

    # زمان‌های استاندارد
    standard_cleaning_time: int = int(os.getenv('STANDARD_CLEANING_TIME', '45'))  # دقیقه
    deep_cleaning_time: int = int(os.getenv('DEEP_CLEANING_TIME', '120'))  # دقیقه
    cleaning_timeout: int = int(os.getenv('CLEANING_TIMEOUT', '120'))  # دقیقه

    # کیفیت و استانداردها
    min_quality_score: int = int(os.getenv('MIN_QUALITY_SCORE', '3'))
    inspection_required: bool = os.getenv('INSPECTION_REQUIRED', 'True').lower() == 'true'

    @property
    def check_out_time_obj(self) -> time:
        """تبدیل زمان خروج به object"""
        return self._parse_time(self.check_out_time)

    @property
    def cleaning_start_time_obj(self) -> time:
        """تبدیل زمان شروع نظافت به object"""
        return self._parse_time(self.cleaning_start_time)

    @property
    def cleaning_end_time_obj(self) -> time:
        """تبدیل زمان پایان نظافت به object"""
        return self._parse_time(self.cleaning_end_time)

    def _parse_time(self, time_str: str) -> time:
        """تبدیل رشته زمان به object"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except (ValueError, AttributeError):
            return time(12, 0)  # پیش‌فرض

@dataclass
class MaintenanceConfig:
    """پیکربندی سیستم تاسیسات و تعمیرات"""
    # تنظیمات پاسخگویی
    emergency_response_time: int = int(os.getenv('EMERGENCY_RESPONSE_TIME', '30'))  # دقیقه
    normal_response_time: int = int(os.getenv('NORMAL_RESPONSE_TIME', '120'))  # دقیقه

    # محدودیت‌ها
    max_concurrent_work: int = int(os.getenv('MAX_CONCURRENT_WORK', '3'))
    max_work_order_duration: int = int(os.getenv('MAX_WORK_DURATION', '480'))  # دقیقه

    # تعمیرات پیشگیرانه
    preventive_maintenance_enabled: bool = os.getenv('PREVENTIVE_MAINTENANCE', 'True').lower() == 'true'
    pm_check_interval: int = int(os.getenv('PM_CHECK_INTERVAL', '24'))  # ساعت

    # موجودی
    low_stock_threshold: int = int(os.getenv('LOW_STOCK_THRESHOLD', '5'))
    critical_stock_threshold: int = int(os.getenv('CRITICAL_STOCK_THRESHOLD', '2'))

@dataclass
class NotificationConfig:
    """پیکربندی سیستم اطلاع‌رسانی"""
    # فعال/غیرفعال کردن کانال‌ها
    enabled: bool = os.getenv('NOTIFICATIONS_ENABLED', 'True').lower() == 'true'
    sms_enabled: bool = os.getenv('SMS_ENABLED', 'False').lower() == 'true'
    email_enabled: bool = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    push_enabled: bool = os.getenv('PUSH_ENABLED', 'True').lower() == 'true'

    # SMS Gateway
    sms_api_key: str = os.getenv('SMS_API_KEY', '')
    sms_sender: str = os.getenv('SMS_SENDER', 'Hotel')
    sms_base_url: str = os.getenv('SMS_BASE_URL', 'https://sms-api.example.com')

    # Email
    smtp_server: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port: int = int(os.getenv('SMTP_PORT', '587'))
    smtp_username: str = os.getenv('SMTP_USERNAME', '')
    smtp_password: str = os.getenv('SMTP_PASSWORD', '')
    email_from: str = os.getenv('EMAIL_FROM', 'noreply@hotel.com')

    # تنظیمات عمومی
    max_notification_age: int = int(os.getenv('MAX_NOTIFICATION_AGE', '30'))  # روز
    cleanup_interval: int = int(os.getenv('NOTIFICATION_CLEANUP_INTERVAL', '24'))  # ساعت

@dataclass
class SecurityConfig:
    """پیکربندی امنیتی سیستم"""
    # احراز هویت
    secret_key: str = os.getenv('SECRET_KEY', 'hotel-reception-secret-key-2024')
    token_expiry_hours: int = int(os.getenv('TOKEN_EXPIRY_HOURS', '8'))
    session_timeout_minutes: int = int(os.getenv('SESSION_TIMEOUT', '30'))

    # امنیت ورود
    max_login_attempts: int = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
    lockout_duration_minutes: int = int(os.getenv('LOCKOUT_DURATION', '15'))
    password_min_length: int = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))
    password_require_special: bool = os.getenv('PASSWORD_SPECIAL', 'True').lower() == 'true'
    password_require_numbers: bool = os.getenv('PASSWORD_NUMBERS', 'True').lower() == 'true'
    password_expiry_days: int = int(os.getenv('PASSWORD_EXPIRY_DAYS', '90'))

    # امنیت داده
    encrypt_sensitive_data: bool = os.getenv('ENCRYPT_DATA', 'True').lower() == 'true'
    audit_log_enabled: bool = os.getenv('AUDIT_LOG_ENABLED', 'True').lower() == 'true'

@dataclass
class BackupConfig:
    """پیکربندی پشتیبان‌گیری"""
    enabled: bool = os.getenv('BACKUP_ENABLED', 'True').lower() == 'true'
    auto_backup: bool = os.getenv('AUTO_BACKUP', 'True').lower() == 'true'

    # زمان‌بندی
    backup_time: str = os.getenv('BACKUP_TIME', '02:00')
    backup_interval_hours: int = int(os.getenv('BACKUP_INTERVAL', '24'))

    # تنظیمات فایل
    max_backup_files: int = int(os.getenv('MAX_BACKUP_FILES', '30'))
    backup_retention_days: int = int(os.getenv('BACKUP_RETENTION_DAYS', '90'))
    compress_backups: bool = os.getenv('COMPRESS_BACKUPS', 'True').lower() == 'true'

    # مسیرها
    backup_dir: str = os.getenv('BACKUP_DIR', 'data/backups')
    temp_dir: str = os.getenv('TEMP_DIR', 'data/temp')

@dataclass
class LoggingConfig:
    """پیکربندی سیستم لاگینگ"""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    max_file_size: int = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
    backup_count: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    log_format: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # مسیر فایل‌های لاگ
    log_dir: str = os.getenv('LOG_DIR', 'data/logs')
    access_log: str = os.getenv('ACCESS_LOG', 'access.log')
    error_log: str = os.getenv('ERROR_LOG', 'error.log')
    audit_log: str = os.getenv('AUDIT_LOG', 'audit.log')

    @property
    def log_level(self) -> int:
        """تبدیل سطح لاگ به مقدار عددی"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_map.get(self.level.upper(), logging.INFO)

@dataclass
class UIConfig:
    """پیکربندی رابط کاربری"""
    # تنظیمات نمایش
    language: str = os.getenv('UI_LANGUAGE', 'fa')
    theme: str = os.getenv('UI_THEME', 'default')
    font_family: str = os.getenv('UI_FONT_FAMILY', 'B Nazanin')
    font_size: int = int(os.getenv('UI_FONT_SIZE', '10'))

    # تنظیمات پنجره
    window_width: int = int(os.getenv('WINDOW_WIDTH', '1400'))
    window_height: int = int(os.getenv('WINDOW_HEIGHT', '800'))
    maximize_on_start: bool = os.getenv('MAXIMIZE_ON_START', 'True').lower() == 'true'

    # به‌روزرسانی Real-time
    refresh_interval: int = int(os.getenv('REFRESH_INTERVAL', '30'))  # ثانیه
    real_time_updates: bool = os.getenv('REAL_TIME_UPDATES', 'True').lower() == 'true'

    # تنظیمات پیشرفته
    enable_animations: bool = os.getenv('ENABLE_ANIMATIONS', 'True').lower() == 'true'
    show_system_tray: bool = os.getenv('SHOW_SYSTEM_TRAY', 'True').lower() == 'true'

@dataclass
class AppConfig:
    """پیکربندی اصلی برنامه"""

    # اطلاعات برنامه
    app_name: str = "سیستم پذیرش هتل"
    version: str = "1.0.0"
    environment: str = os.getenv('ENVIRONMENT', 'development')
    debug: bool = os.getenv('DEBUG', 'True').lower() == 'true'

    # مسیرهای اصلی
    base_dir: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir: str = os.path.join(base_dir, 'data')

    # ماژول‌های پیکربندی
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    payment: PaymentConfig = field(default_factory=PaymentConfig)
    housekeeping: HousekeepingConfig = field(default_factory=HousekeepingConfig)
    maintenance: MaintenanceConfig = field(default_factory=MaintenanceConfig)
    notification: NotificationConfig = field(default_factory=NotificationConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    backup: BackupConfig = field(default_factory=BackupConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    ui: UIConfig = field(default_factory=UIConfig)

    def __post_init__(self):
        """ایجاد پوشه‌های مورد نیاز پس از مقداردهی"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backup.backup_dir, exist_ok=True)
        os.makedirs(self.logging.log_dir, exist_ok=True)

    @property
    def is_production(self) -> bool:
        """بررسی محیط اجرا"""
        return self.environment.lower() == 'production'

    @property
    def is_development(self) -> bool:
        """بررسی محیط توسعه"""
        return self.environment.lower() == 'development'

    @property
    def is_testing(self) -> bool:
        """بررسی محیط تست"""
        return self.environment.lower() == 'testing'

# ایجاد instance جهانی
config = AppConfig()

# ایمپورت پیکربندی همگام‌سازی
from config.sync_config import sync_config, channel_config
