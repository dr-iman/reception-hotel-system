"""
فایل پیکربندی مشترک برای تمام تست‌ها
شامل fixtureها و تنظیمات تست
"""

import pytest
import os
import sys
import tempfile
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch

# اضافه کردن مسیر پروژه به Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import db_session, init_db, create_tables, Base
from app.services.reception.initial_data_service import InitialDataService
from config import config

# تنظیمات تست
TEST_DATABASE_URL = "sqlite:///./test_hotel_reception.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """تنظیمات اولیه محیط تست"""
    print("\n" + "="*60)
    print("🔄 راه‌اندازی محیط تست...")
    print("="*60)

    # تغییر تنظیمات برای محیط تست
    original_db_url = config.database.url
    config.database.url = TEST_DATABASE_URL

    yield

    # بازگردانی تنظیمات
    config.database.url = original_db_url
    print("\n✅ محیط تست پاکسازی شد")

@pytest.fixture(scope="function")
def test_database():
    """ایجاد دیتابیس تست موقت"""
    import sqlite3
    from sqlalchemy import create_engine

    # ایجاد دیتابیس تست
    test_engine = create_engine(TEST_DATABASE_URL)

    # ایجاد جداول
    Base.metadata.create_all(bind=test_engine)

    yield test_engine

    # پاکسازی
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def test_session(test_database):
    """ایجاد session تست"""
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=test_database)
    session = Session()

    yield session

    # rollback و بستن session
    session.rollback()
    session.close()

@pytest.fixture(scope="function")
def sample_guest_data():
    """داده‌های نمونه برای مهمان"""
    return {
        'first_name': 'رضا',
        'last_name': 'اکبری',
        'national_id': '1234567890',
        'phone': '+989121234567',
        'email': 'reza.akbari@example.com',
        'nationality': 'ایرانی',
        'date_of_birth': date(1985, 5, 15)
    }

@pytest.fixture(scope="function")
def sample_stay_data():
    """داده‌های نمونه برای اقامت"""
    return {
        'planned_check_in': datetime(2024, 1, 15, 14, 0),
        'planned_check_out': datetime(2024, 1, 18, 12, 0),
        'stay_purpose': 'business',
        'total_amount': Decimal('4500000'),
        'advance_payment': Decimal('1500000'),
        'remaining_balance': Decimal('3000000'),
        'status': 'confirmed'
    }

@pytest.fixture(scope="function")
def sample_payment_data():
    """داده‌های نمونه برای پرداخت"""
    return {
        'amount': Decimal('1000000'),
        'payment_method': 'cash',
        'payment_type': 'settlement',
        'description': 'پرداخت تستی'
    }

@pytest.fixture(scope="function")
def mock_redis():
    """Mock برای Redis"""
    with patch('app.core.database.get_redis') as mock_redis:
        mock_client = MagicMock()
        mock_redis.return_value = mock_client
        yield mock_client

@pytest.fixture(scope="function")
def mock_payment_gateway():
    """Mock برای درگاه پرداخت"""
    with patch('app.core.payment_processor.POSPaymentGateway') as mock_gateway:
        mock_instance = MagicMock()
        mock_gateway.return_value = mock_instance
        mock_instance.process_payment.return_value = {
            'success': True,
            'transaction_id': 'TXN_TEST_123',
            'reference_number': 'REF_TEST_456'
        }
        yield mock_instance

# fixtureهای کمکی
@pytest.fixture
def current_date():
    """تاریخ جاری"""
    return date.today()

@pytest.fixture
def current_datetime():
    """زمان جاری"""
    return datetime.now()

@pytest.fixture
def decimal_100000():
    """مقدار Decimal 100,000"""
    return Decimal('100000')

@pytest.fixture
def decimal_500000():
    """مقدار Decimal 500,000"""
    return Decimal('500000')

# تنظیمات pytest
def pytest_configure(config):
    """پیکربندی pytest"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )

def pytest_sessionstart(session):
    """شروع session تست"""
    print("\n🚀 شروع اجرای تست‌های سیستم پذیرش هتل")

def pytest_sessionfinish(session, exitstatus):
    """پایان session تست"""
    print(f"\n🏁 پایان اجرای تست‌ها - وضعیت خروج: {exitstatus}")
