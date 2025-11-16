#!/usr/bin/env python3
"""
اسکریپت تست اتصال به Redis و دیتابیس
"""

import sys
import os
import logging
from pathlib import Path

# اضافه کردن مسیر پروژه به Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# تنظیمات لاگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('connection_test.log')
    ]
)

logger = logging.getLogger(__name__)

def test_redis_connection():
    """تست اتصال به Redis"""
    try:
        from app.core.database import get_redis, init_redis
        
        logger.info("🔗 تست اتصال به Redis...")
        
        if init_redis():
            redis_client = get_redis()
            redis_client.ping()
            logger.info("✅ اتصال به Redis موفقیت‌آمیز بود")
            
            # تست ذخیره و بازیابی داده
            test_key = "connection_test"
            test_value = "Hello Redis!"
            redis_client.set(test_key, test_value)
            retrieved_value = redis_client.get(test_key)
            
            if retrieved_value == test_value:
                logger.info("✅ تست ذخیره/بازیابی Redis موفقیت‌آمیز بود")
            else:
                logger.error("❌ تست ذخیره/بازیابی Redis ناموفق بود")
                
            return True
        else:
            logger.error("❌ اتصال به Redis ناموفق بود")
            return False
            
    except Exception as e:
        logger.error(f"❌ خطا در اتصال به Redis: {e}")
        return False

def test_database_connection():
    """تست اتصال به دیتابیس PostgreSQL"""
    try:
        from app.core.database import init_db, db_session, get_database_status
        
        logger.info("🔗 تست اتصال به دیتابیس PostgreSQL...")
        
        if init_db():
            status = get_database_status()
            logger.info(f"✅ اتصال به دیتابیس موفقیت‌آمیز بود")
            logger.info(f"📊 وضعیت دیتابیس: {status}")
            
            # تست ایجاد session
            with db_session() as session:
                result = session.execute("SELECT version(), current_database(), current_user")
                db_info = result.fetchone()
                logger.info(f"🐘 PostgreSQL Version: {db_info[0]}")
                logger.info(f"📁 Database: {db_info[1]}")
                logger.info(f"👤 User: {db_info[2]}")
                
            return True
        else:
            logger.error("❌ اتصال به دیتابیس ناموفق بود")
            return False
            
    except Exception as e:
        logger.error(f"❌ خطا در اتصال به دیتابیس: {e}")
        return False

def test_config_loading():
    """تست لود شدن تنظیمات"""
    try:
        from config import config
        
        logger.info("⚙️ تست لود شدن تنظیمات...")
        
        # تست تنظیمات دیتابیس
        db_config = config.database
        logger.info(f"📋 تنظیمات دیتابیس: {db_config.host}:{db_config.port}/{db_config.name}")
        
        # تست تنظیمات Redis
        redis_config = config.redis
        logger.info(f"📋 تنظیمات Redis: {redis_config.host}:{redis_config.port}/{redis_config.db}")
        
        logger.info("✅ تنظیمات با موفقیت لود شدند")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در لود تنظیمات: {e}")
        return False

def test_model_loading():
    """تست لود شدن مدل‌ها"""
    try:
        logger.info("🏗️ تست لود شدن مدل‌ها...")
        
        # تست لود مدل مهمان
        from app.models.reception.guest_models import Guest
        logger.info("✅ مدل Guest با موفقیت لود شد")
        
        # تست لود مدل خانه‌داری
        from app.models.reception.housekeeping_models import HousekeepingTask
        logger.info("✅ مدل HousekeepingTask با موفقیت لود شد")
        
        # تست لود مدل وضعیت اتاق
        from app.models.reception.room_status_models import RoomAssignment
        logger.info("✅ مدل RoomAssignment با موفقیت لود شد")
        
        logger.info("✅ تمام مدل‌ها با موفقیت لود شدند")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در لود مدل‌ها: {e}")
        return False

def test_core_modules():
    """تست لود شدن ماژول‌های core"""
    try:
        logger.info("🔧 تست لود شدن ماژول‌های core...")
        
        # تست HousekeepingManager
        from app.core.housekeeping_manager import HousekeepingManager
        manager = HousekeepingManager()
        logger.info("✅ HousekeepingManager با موفقیت لود شد")
        
        # تست وجود متدها
        if hasattr(manager, '_generate_daily_housekeeping_report'):
            logger.info("✅ متد _generate_daily_housekeeping_report وجود دارد")
        else:
            logger.error("❌ متد _generate_daily_housekeeping_report یافت نشد")
            
        # تست PaymentProcessor
        from app.core.payment_processor import PaymentProcessor
        payment_processor = PaymentProcessor()
        logger.info("✅ PaymentProcessor با موفقیت لود شد")
        
        # تست SyncManager
        from app.core.sync_manager import SyncManager
        sync_manager = SyncManager()
        logger.info("✅ SyncManager با موفقیت لود شد")
        
        logger.info("✅ تمام ماژول‌های core با موفقیت لود شدند")
        return True
        
    except Exception as e:
        logger.error(f"❌ خطا در لود ماژول‌های core: {e}")
        return False

def main():
    """تابع اصلی تست"""
    logger.info("🚀 شروع تست اتصال سیستم پذیرش هتل...")
    
    results = {
        "config": test_config_loading(),
        "redis": test_redis_connection(),
        "database": test_database_connection(),
        "models": test_model_loading(),
        "core_modules": test_core_modules()
    }
    
    # نمایش نتایج
    logger.info("\n" + "="*50)
    logger.info("📊 نتایج تست اتصال:")
    logger.info("="*50)
    
    for test_name, result in results.items():
        status = "✅ موفق" if result else "❌ ناموفق"
        logger.info(f"{test_name}: {status}")
    
    success_count = sum(results.values())
    total_tests = len(results)
    
    logger.info("="*50)
    logger.info(f"🎯 نتیجه نهایی: {success_count}/{total_tests} تست موفق")
    
    if success_count == total_tests:
        logger.info("🎉 تمام تست‌ها با موفقیت گذرانده شدند!")
        return 0
    else:
        logger.error("💥 برخی تست‌ها ناموفق بودند. لطفاً خطاها را بررسی کنید.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
