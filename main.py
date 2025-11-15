# main.py - نسخه بهینه شده برای Redis 8.2.3
import sys
import os
import logging
from pathlib import Path

# پاک کردن کش قبل از هر چیزی
def clear_python_cache():
    """پاک کردن کامل کش‌های Python"""
    import shutil
    cache_dirs = [
        '__pycache__',
        'app/__pycache__', 
        'app/models/__pycache__',
        'app/core/__pycache__',
        'app/services/__pycache__',
        'app/views/__pycache__'
    ]
    
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            shutil.rmtree(cache_path)
            print(f"🧹 پاک شد: {cache_dir}")

clear_python_cache()

# تنظیمات محیط
os.environ['SQLALCHEMY_SILENCE_UBER_WARNING'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'

# افزودن مسیر پروژه
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

def setup_logging():
    """تنظیمات لاگ‌گیری"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def initialize_redis_8_2_3(logger):
    """راه‌اندازی Redis برای نسخه 8.2.3"""
    try:
        from app.core.database import init_redis
        
        logger.info("🔗 در حال اتصال به Redis 8.2.3...")
        if init_redis():
            logger.info("✅ اتصال به Redis موفق بود")
            return True
        else:
            logger.warning("⚠️ اتصال به Redis ناموفق - ادامه بدون Redis")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ خطا در Redis: {e} - ادامه بدون Redis")
        return False

def initialize_database_fixed(logger):
    """راه‌اندازی دیتابیس با حل تعارض مدل‌ها"""
    try:
        from app.core.database import init_db, create_tables
        from app.services.reception.initial_data_service import InitialDataService
        
        logger.info("🗄️ در حال اتصال به دیتابیس...")
        if not init_db():
            logger.error("❌ اتصال به دیتابیس ناموفق")
            return False

        # ایجاد جداول
        logger.info("📋 در حال ایجاد جداول...")
        create_tables()

        # داده‌های اولیه
        logger.info("📥 در حال بارگذاری داده‌های اولیه...")
        InitialDataService.create_reception_initial_data()

        logger.info("✅ دیتابیس با موفقیت راه‌اندازی شد")
        return True

    except Exception as e:
        logger.error(f"❌ خطا در دیتابیس: {e}")
        return False

def main():
    """تابع اصلی"""
    logger = setup_logging()
    
    try:
        logger.info("🚀 شروع سیستم پذیرش هتل...")
        logger.info("🔧 نسخه Redis: 8.2.3")

        # تنظیمات UI
        app = QApplication(sys.argv)
        font = QFont()
        font.setFamily("Tahoma")
        font.setPointSize(9)
        app.setFont(font)
        
        app.setApplicationName("سیستم پذیرش هتل")
        app.setApplicationVersion("2.0.0")

        # راه‌اندازی Redis
        redis_ok = initialize_redis_8_2_3(logger)

        # راه‌اندازی دیتابیس
        if not initialize_database_fixed(logger):
            logger.error("💥 خروج به دلیل خطا در دیتابیس")
            return 1

        # ایجاد پنجره اصلی
        logger.info("🖥️ در حال ایجاد رابط کاربری...")
        from app.views.main_window import MainWindow
        main_window = MainWindow()
        main_window.showMaximized()
        
        if redis_ok:
            logger.info("🎉 سیستم با پشتیبانی کامل Redis 8.2.3 راه‌اندازی شد!")
        else:
            logger.info("⚠️ سیستم بدون Redis در حال اجراست")
        
        return app.exec_()

    except Exception as e:
        logger.critical(f"💥 خطای بحرانی: {str(e)[:200]}...")
        return 1

if __name__ == '__main__':
    sys.exit(main())
