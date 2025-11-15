# main.py
"""
فایل اجرایی اصلی سیستم پذیرش هتل
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

from app.views.main_window import MainWindow
from app.core.database import init_db, init_redis, create_tables
from app.services.reception.initial_data_service import InitialDataService
from config import config

# تنظیمات لاگ‌گیری
def setup_logging():
    """تنظیمات لاگ‌گیری"""
    # ایجاد دایرکتوری لاگ‌ها اگر وجود ندارد
    config.app.log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.app.log_dir / 'reception_system.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 50)
    logger.info(f"شروع سیستم پذیرش هتل - نسخه {config.app.version}")
    logger.info("=" * 50)

    return logger

def initialize_database(logger):
    """راه‌اندازی پایگاه داده"""
    try:
        logger.info("در حال اتصال به پایگاه داده...")

        # راه‌اندازی دیتابیس
        if not init_db():
            logger.error("اتصال به دیتابیس ناموفق بود")
            return False

        # راه‌اندازی Redis
        if not init_redis():
            logger.warning("اتصال به Redis ناموفق بود")

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
    app.setApplicationName(config.app.app_name)
    app.setApplicationVersion(config.app.version)
    app.setOrganizationName(config.app.company_name)

    return app

def main():
    """تابع اصلی"""
    # تنظیمات لاگ‌گیری
    logger = setup_logging()

    try:
        # تنظیمات برنامه
        app = setup_application()

        # راه‌اندازی دیتابیس
        if not initialize_database(logger):
            logger.error("خروج به دلیل خطا در راه‌اندازی دیتابیس")
            return 1

        # ایجاد و نمایش پنجره اصلی
        logger.info("در حال ایجاد پنجره اصلی...")
        main_window = MainWindow()
        main_window.show()

        # نمایش حداکثر شده
        main_window.showMaximized()

        logger.info("برنامه با موفقیت راه‌اندازی شد و آماده استفاده است")

        # اجرای حلقه اصلی
        return app.exec_()

    except Exception as e:
        logger.critical(f"خطای بحرانی در اجرای برنامه: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
