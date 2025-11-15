# config/utils.py
"""
ابزارهای کمکی برای مدیریت پیکربندی
"""

import os
import logging
from typing import Any, Dict, List
from dataclasses import asdict, is_dataclass

class ConfigValidator:
    """اعتبارسنجی تنظیمات پیکربندی"""

    @staticmethod
    def validate_database_config(config) -> List[str]:
        """اعتبارسنجی تنظیمات دیتابیس"""
        errors = []

        if not config.host:
            errors.append("Database host is required")

        if config.port <= 0 or config.port > 65535:
            errors.append("Database port must be between 1 and 65535")

        if not config.database:
            errors.append("Database name is required")

        if not config.username:
            errors.append("Database username is required")

        return errors

    @staticmethod
    def validate_redis_config(config) -> List[str]:
        """اعتبارسنجی تنظیمات Redis"""
        errors = []

        if not config.host:
            errors.append("Redis host is required")

        if config.port <= 0 or config.port > 65535:
            errors.append("Redis port must be between 1 and 65535")

        if config.db < 0 or config.db > 15:
            errors.append("Redis database must be between 0 and 15")

        return errors

    @staticmethod
    def validate_payment_config(config) -> List[str]:
        """اعتبارسنجی تنظیمات پرداخت"""
        errors = []

        if config.pos_enabled and not config.pos_terminal_id:
            errors.append("POS terminal ID is required when POS is enabled")

        if config.commission_rate < 0 or config.commission_rate > 1:
            errors.append("Commission rate must be between 0 and 1")

        if config.tax_rate < 0 or config.tax_rate > 1:
            errors.append("Tax rate must be between 0 and 1")

        return errors

    @classmethod
    def validate_all(cls, config) -> Dict[str, List[str]]:
        """اعتبارسنجی تمام تنظیمات"""
        errors = {}

        # اعتبارسنجی هر بخش
        if hasattr(config, 'database'):
            db_errors = cls.validate_database_config(config.database)
            if db_errors:
                errors['database'] = db_errors

        if hasattr(config, 'redis'):
            redis_errors = cls.validate_redis_config(config.redis)
            if redis_errors:
                errors['redis'] = redis_errors

        if hasattr(config, 'payment'):
            payment_errors = cls.validate_payment_config(config.payment)
            if payment_errors:
                errors['payment'] = payment_errors

        return errors

class ConfigLogger:
    """لاگینگ تنظیمات (بدون اطلاعات حساس)"""

    @staticmethod
    def log_config_summary(config):
        """ثبت خلاصه‌ای از تنظیمات در لاگ"""
        logger = logging.getLogger(__name__)

        logger.info("🔧 Configuration Summary:")
        logger.info(f"   Environment: {config.environment}")
        logger.info(f"   Debug Mode: {config.debug}")
        logger.info(f"   Database: {config.database.host}:{config.database.port}/{config.database.database}")
        logger.info(f"   Redis: {config.redis.host}:{config.redis.port}/{config.redis.db}")
        logger.info(f"   Auto Sync: {sync_config.auto_sync_enabled}")
        logger.info(f"   Payment Test Mode: {config.payment.test_mode}")

    @staticmethod
    def log_sensitive_config_issues(config):
        """بررسی و لاگ مسائل امنیتی در تنظیمات"""
        logger = logging.getLogger(__name__)

        # بررسی پسوردهای پیش‌فرض
        if config.database.password == 'password':
            logger.warning("⚠️  Using default database password")

        if config.redis.password == '':
            logger.warning("⚠️  Redis password is empty")

        if config.security.secret_key == 'hotel-reception-secret-key-2024':
            logger.warning("⚠️  Using default secret key")

        # بررسی تنظیمات امنیتی
        if config.debug and config.is_production:
            logger.error("❌ Debug mode is enabled in production environment!")

        if not config.security.encrypt_sensitive_data:
            logger.warning("⚠️  Sensitive data encryption is disabled")

def export_config_to_dict(config) -> Dict[str, Any]:
    """تبدیل پیکربندی به دیکشنری (برای export)"""
    if is_dataclass(config):
        return asdict(config)
    elif hasattr(config, '__dict__'):
        return config.__dict__
    else:
        return {}

def generate_config_template() -> str:
    """ایجاد template فایل .env"""
    template = """# Hotel Reception System Configuration
# Environment Settings
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=hotel_reception
DB_USER=postgres
DB_PASS=password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASS=

# Network Configuration
RESERVATION_URL=http://localhost:8000
API_TIMEOUT=30

# Payment Configuration
POS_ENABLED=True
POS_TERMINAL_ID=TEST_TERMINAL
POS_MERCHANT_ID=TEST_MERCHANT
PAYMENT_TEST_MODE=True

# Sync Configuration
AUTO_SYNC_ENABLED=True
SYNC_INTERVAL=300
DAILY_SYNC_TIME=00:00

# Security Configuration
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT=30
MAX_LOGIN_ATTEMPTS=5

# Housekeeping Configuration
CHECK_OUT_TIME=12:00
AUTO_CLEANING=True

# Notification Configuration
NOTIFICATIONS_ENABLED=True
SMS_ENABLED=False
EMAIL_ENABLED=False

# Backup Configuration
BACKUP_ENABLED=True
BACKUP_TIME=02:00
"""
    return template

# ایجاد instance های global
config_validator = ConfigValidator()
config_logger = ConfigLogger()
