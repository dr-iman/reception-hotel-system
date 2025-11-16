# app/core/database.py
"""
مدیریت اتصال به دیتابیس - نسخه مشترک با سیستم رزرواسیون
"""

import logging
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import redis
import time
from config import config

logger = logging.getLogger(__name__)

# پایه مدل‌ها
Base = declarative_base()

# متغیرهای جهانی
engine = None
SessionLocal = None
redis_client = None

class DatabaseManager:
    """مدیریت پیشرفته اتصال به دیتابیس"""

    def __init__(self):
        self.connection_retries = 3
        self.retry_delay = 5
        self.is_connected = False

    def init_database(self):
        """راه‌اندازی اتصال به دیتابیس"""
        global engine, SessionLocal

        for attempt in range(self.connection_retries):
            try:
                logger.info(f"🔗 تلاش برای اتصال به دیتابیس پذیرش (تلاش {attempt + 1})...")

                # ایجاد engine با تنظیمات بهینه
                engine = create_engine(
                    config.database.url,
                    poolclass=QueuePool,
                    pool_size=20,
                    max_overflow=30,
                    pool_timeout=30,
                    pool_recycle=3600,
                    echo=config.debug,
                    connect_args={
                        'connect_timeout': 10,
                        'application_name': f'hotel_reception_{config.version}'
                    }
                )

                # تست اتصال
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()

                SessionLocal = scoped_session(sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=engine
                ))

                self.is_connected = True
                logger.info("✅ اتصال به دیتابیس پذیرش با موفقیت برقرار شد")
                return True

            except Exception as e:
                logger.error(f"❌ خطا در اتصال به دیتابیس (تلاش {attempt + 1}): {e}")
                if attempt < self.connection_retries - 1:
                    logger.info(f"⏳ انتظار {self.retry_delay} ثانیه برای تلاش مجدد...")
                    time.sleep(self.retry_delay)

        logger.error("❌ اتصال به دیتابیس پذیرش ناموفق بود")
        return False

    def init_redis(self):
        """راه‌اندازی اتصال به Redis"""
        global redis_client

        try:
            redis_client = redis.Redis(
                host=config.redis.host,
                port=config.redis.port,
                db=config.redis.db,
                password=config.redis.password or None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )

            # تست اتصال
            redis_client.ping()
            logger.info("✅ اتصال به Redis با موفقیت برقرار شد")
            return True

        except Exception as e:
            logger.error(f"❌ خطا در اتصال به Redis: {e}")
            redis_client = None
            return False

    def get_connection_status(self):
        """دریافت وضعیت اتصال"""
        try:
            with engine.connect() as conn:
                result = conn.execute("SELECT version(), current_database(), current_user")
                db_info = result.fetchone()

            redis_status = "Connected" if redis_client and redis_client.ping() else "Disconnected"

            return {
                'database': {
                    'status': 'Connected',
                    'version': db_info[0],
                    'name': db_info[1],
                    'user': db_info[2]
                },
                'redis': {
                    'status': redis_status
                },
                'reception_system': {
                    'is_connected': self.is_connected
                }
            }
        except Exception as e:
            return {
                'database': {'status': 'Disconnected', 'error': str(e)},
                'redis': {'status': 'Disconnected'},
                'reception_system': {'is_connected': False}
            }

# ایجاد مدیر دیتابیس
db_manager = DatabaseManager()

def init_db():
    """راه‌اندازی اولیه دیتابیس"""
    return db_manager.init_database()

def init_redis():
    """راه‌اندازی اولیه Redis"""
    return db_manager.init_redis()

def create_tables():
    """ایجاد جداول در دیتابیس"""
    if engine is None:
        if not init_db():
            raise Exception("اتصال به دیتابیس برقرار نشد")

    try:
        # ایمپورت تمام مدل‌ها برای ایجاد جداول
        from app.models.reception import guest_models, room_status_models, payment_models
        #from app.models.reception import housekeeping_models, maintenance_models, staff_models
        from app.models.reception import notification_models, report_models, staff_models

        Base.metadata.create_all(bind=engine)
        logger.info("✅ جداول سیستم پذیرش با موفقیت در دیتابیس ایجاد شدند")

        # ایجاد داده‌های اولیه
        create_initial_data()

    except Exception as e:
        logger.error(f"❌ خطا در ایجاد جداول: {e}")
        raise

def create_initial_data():
    """ایجاد داده‌های اولیه سیستم"""
    try:
        from app.services.reception.initial_data_service import create_reception_initial_data
        create_reception_initial_data()
        logger.info("✅ داده‌های اولیه سیستم پذیرش ایجاد شدند")
    except Exception as e:
        logger.error(f"⚠️ خطا در ایجاد داده‌های اولیه: {e}")

@contextmanager
def db_session():
    """Context manager برای مدیریت session"""
    if SessionLocal is None:
        if not init_db():
            raise Exception("اتصال به دیتابیس در دسترس نیست")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"❌ خطا در session دیتابیس: {e}")

        # تلاش برای بازیابی اتصال در صورت قطعی
        if "connection" in str(e).lower() or "closed" in str(e).lower():
            logger.info("🔄 تلاش برای بازیابی اتصال...")
            if init_db():
                session = SessionLocal()
                yield session
                session.commit()
            else:
                raise Exception("اتصال به دیتابیس قطع شده و بازیابی نشد")
        else:
            raise
    finally:
        session.close()

def get_redis():
    """دریافت client Redis"""
    if redis_client is None:
        db_manager.init_redis()
    return redis_client

def get_database_status():
    """دریافت وضعیت اتصال دیتابیس"""
    return db_manager.get_connection_status()
