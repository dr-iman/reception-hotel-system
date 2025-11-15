# config/environment.py
"""
تنظیمات محیط‌های مختلف (توسعه، تست، تولید)
"""

import os
from typing import Dict, Any

class EnvironmentConfig:
    """مدیریت تنظیمات بر اساس محیط اجرا"""

    # تنظیمات پیش‌فرض برای تمام محیط‌ها
    BASE_SETTINGS: Dict[str, Any] = {
        'APP_NAME': 'سیستم پذیرش هتل',
        'VERSION': '1.0.0',
        'SUPPORT_EMAIL': 'support@hotel.com',
        'SUPPORT_PHONE': '+982112345678'
    }

    # تنظیمات محیط توسعه
    DEVELOPMENT: Dict[str, Any] = {
        'DEBUG': True,
        'LOG_LEVEL': 'DEBUG',
        'DB_NAME': 'hotel_reception_dev',
        'PAYMENT_TEST_MODE': True,
        'AUTO_SYNC_ENABLED': True,
        'ENABLE_ANIMATIONS': True
    }

    # تنظیمات محیط تست
    TESTING: Dict[str, Any] = {
        'DEBUG': True,
        'LOG_LEVEL': 'DEBUG',
        'DB_NAME': 'hotel_reception_test',
        'PAYMENT_TEST_MODE': True,
        'AUTO_SYNC_ENABLED': False,
        'ENABLE_ANIMATIONS': False
    }

    # تنظیمات محیط تولید
    PRODUCTION: Dict[str, Any] = {
        'DEBUG': False,
        'LOG_LEVEL': 'INFO',
        'DB_NAME': 'hotel_reception_prod',
        'PAYMENT_TEST_MODE': False,
        'AUTO_SYNC_ENABLED': True,
        'ENABLE_ANIMATIONS': False,
        'SSL_VERIFICATION': True,
        'ENCRYPT_DATA': True
    }

    @classmethod
    def get_environment_settings(cls, environment: str) -> Dict[str, Any]:
        """دریافت تنظیمات محیط مشخص"""
        env_map = {
            'development': cls.DEVELOPMENT,
            'testing': cls.TESTING,
            'production': cls.PRODUCTION
        }

        settings = cls.BASE_SETTINGS.copy()
        settings.update(env_map.get(environment.lower(), cls.DEVELOPMENT))
        return settings

    @classmethod
    def setup_environment(cls, environment: str = None):
        """تنظیم متغیرهای محیطی بر اساس محیط اجرا"""
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development')

        settings = cls.get_environment_settings(environment)

        # تنظیم متغیرهای محیطی
        for key, value in settings.items():
            if key not in os.environ:  # فقط اگر از قبل تنظیم نشده
                os.environ[key] = str(value)

        return settings

# تنظیم خودکار محیط در هنگام ایمپورت
current_environment = os.getenv('ENVIRONMENT', 'development')
environment_settings = EnvironmentConfig.setup_environment(current_environment)
