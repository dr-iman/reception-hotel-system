# main.py
"""
فایل اجرایی اصلی سیستم پذیرش هتل - نسخه با پشتیبانی Redis
"""

import sys
import os
import logging
from pathlib import Path

# افزودن مسیر پروژه به sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont

# تنظیمات لاگ‌گیری
def setup_logging():
    """تنظیمات لاگ‌گیری"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info("شروع سیستم پذیرش هتل - با پشتیبانی Redis")
    logger.info("=" * 50)

    return logger

def initialize_redis(logger):
    """راه‌اندازی Redis"""
    try:
        from app.core.database import init_redis
        
        logger.info("در حال اتصال به Redis...")
        if init_redis():
            logger.info("✅ اتصال به Redis موفق بود")
            return True
        else:
            logger.warning("⚠️ اتصال به Redis ناموفق بود - ادامه بدون Redis")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ خطا در راه‌اندازی Redis: {e} - ادامه بدون Redis")
        return False

def initialize_database(logger):
    """راه‌اندازی پایگاه داده"""
    try:
        logger.info("در حال اتصال به پایگاه داده...")

        from app.core.database import init_db, create_tables
        from app.services.reception.initial_data_service import InitialDataService

        # راه‌اندازی دیتابیس
        if not init_db():
            logger.error("اتصال به دیتابیس ناموفق بود")
            return False

        # ایجاد جداول
        logger.info("در حال ایجاد ساختار داده‌ها...")
        create_tables()

        # بررسی و ایجاد داده‌های اولیه
        logger.info("در حال بارگذاری داده‌های اولیه...")
        InitialDataService.create_reception_initial_data()

        logger.info("پایگاه داده با موفقیت راه‌اندازی شد")
        return True

    except Exception as e:
        logger.error(f"خطا در راه‌اندازی پایگاه داده: {e}")
        return False

def setup_application():
    """تنظیمات کلی برنامه"""
    # تنظیم فونت برای پشتیبانی از فارسی
    font = QFont()
    font.setFamily("Tahoma")
    font.setPointSize(9)
    QApplication.setFont(font)

    # ایجاد برنامه
    app = QApplication(sys.argv)

    # تنظیم نام برنامه
    app.setApplicationName("سیستم پذیرش هتل")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("هتل آراد")

    return app

def main():
    """تابع اصلی"""
    # تنظیمات لاگ‌گیری
    logger = setup_logging()

    try:
        # تنظیمات برنامه
        app = setup_application()

        # راه‌اندازی Redis
        redis_initialized = initialize_redis(logger)

        # راه‌اندازی دیتابیس
        if not initialize_database(logger):
            logger.error("خروج به دلیل خطا در راه‌اندازی دیتابیس")
            return 1

        # ایجاد و نمایش پنجره اصلی
        logger.info("در حال ایجاد پنجره اصلی...")
        from app.views.main_window import MainWindow
        main_window = MainWindow()
        main_window.show()

        # نمایش حداکثر شده
        main_window.showMaximized()

        logger.info("برنامه با موفقیت راه‌اندازی شد و آماده استفاده است")
        if redis_initialized:
            logger.info("✅ سیستم با پشتیبانی کامل Redis فعال است")
        else:
            logger.info("⚠️ سیستم بدون Redis در حال اجراست")

        # اجرای حلقه اصلی
        return app.exec_()

    except Exception as e:
        logger.critical(f"خطای بحرانی در اجرای برنامه: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
