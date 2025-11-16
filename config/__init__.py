# config/__init__.py
"""
پیکربندی‌های اصلی سیستم پذیرش هتل - نسخه بهینه شده
"""

import os
import sys
from pathlib import Path

# اضافه کردن مسیر پروژه به Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ایمپورت ماژول‌های پیکربندی از فایل‌های جداگانه
from .database_config import database_config, redis_config
from .network_config import api_config, network_config
from .payment_config import payment_config, receipt_config
from .sync_config import sync_config, channel_config
from .environment import environment_settings, current_environment
from .app_config import app_config
from .utils import config_validator, config_logger

# کلاس اصلی پیکربندی برای backward compatibility
class Config:
    """کلاس اصلی پیکربندی برای دسترسی یکپارچه"""
    
    def __init__(self):
        self.environment = current_environment
        self.debug = environment_settings.get('DEBUG', False)
        self.version = "1.0.0"
        
        # ماژول‌های پیکربندی
        self.database = database_config
        self.redis = redis_config
        self.network = network_config
        self.api = api_config
        self.payment = payment_config
        self.receipt = receipt_config
        self.sync = sync_config
        self.channels = channel_config
        self.app = app_config
        
        # تنظیمات محیطی
        self._setup_environment()
    
    def _setup_environment(self):
        """تنظیمات بر اساس محیط اجرا"""
        if self.environment == 'production':
            self.debug = False
        elif self.environment == 'development':
            self.debug = True
    
    @property
    def is_production(self):
        return self.environment == 'production'
    
    @property
    def is_development(self):
        return self.environment == 'development'
    
    @property
    def is_testing(self):
        return self.environment == 'testing'
    
    def validate(self):
        """اعتبارسنجی تمام تنظیمات"""
        return config_validator.validate_all(self)
    
    def log_summary(self):
        """ثبت خلاصه‌ای از تنظیمات"""
        config_logger.log_config_summary(self)
    
    def to_dict(self):
        """تبدیل به دیکشنری (بدون اطلاعات حساس)"""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'version': self.version,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
                'username': self.database.username,
                # پسورد شامل نمی‌شود
            },
            'redis': {
                'host': self.redis.host,
                'port': self.redis.port,
                'db': self.redis.db
            },
            'is_production': self.is_production,
            'is_development': self.is_development
        }

# ایجاد instance جهانی
config = Config()

# توابع کمکی برای دسترسی آسان
def get_database_url():
    """دریافت URL اتصال به دیتابیس"""
    return database_config.url

def get_redis_connection_params():
    """دریافت پارامترهای اتصال به Redis"""
    return redis_config.get_connection_params()

def get_api_headers(service='default'):
    """دریافت headers برای API calls"""
    return api_config.get_headers(service)

def validate_config():
    """اعتبارسنجی تنظیمات"""
    return config.validate()

def log_configuration():
    """ثبت تنظیمات در لاگ"""
    config.log_summary()

# ایمپورت مستقیم برای سهولت دسترسی
__all__ = [
    # Instance اصلی
    'config',
    
    # ماژول‌های پیکربندی
    'database_config', 'redis_config',
    'api_config', 'network_config',
    'payment_config', 'receipt_config',
    'sync_config', 'channel_config',
    'app_config',
    
    # محیط اجرا
    'environment_settings', 'current_environment',
    
    # ابزارها
    'config_validator', 'config_logger',
    
    # توابع کمکی
    'get_database_url',
    'get_redis_connection_params', 
    'get_api_headers',
    'validate_config',
    'log_configuration',
    
    # کلاس‌ها
    'Config'
]

# اعتبارسنجی خودکار هنگام ایمپورت
try:
    if config.is_production:
        config_logger.log_sensitive_config_issues(config)
        
    # اعتبارسنجی اولیه
    validation_errors = validate_config()
    if validation_errors:
        print("⚠️  هشدار: برخی تنظیمات نیاز به توجه دارند:")
        for section, errors in validation_errors.items():
            print(f"   {section}: {errors}")
            
except Exception as e:
    print(f"⚠️  خطا در اعتبارسنجی تنظیمات: {e}")
