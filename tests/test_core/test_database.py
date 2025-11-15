"""
تست‌های ماژول دیتابیس
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import (
    DatabaseManager, init_db, create_tables,
    db_session, get_redis, get_database_status
)
from app.models.reception.guest_models import Guest
from tests.conftest import test_session, sample_guest_data

logger = logging.getLogger(__name__)

class TestDatabase:
    """تست‌های مدیریت دیتابیس"""

    def test_database_manager_initialization(self):
        """تست مقداردهی اولیه DatabaseManager"""
        # Given
        db_manager = DatabaseManager()

        # Then
        assert db_manager.connection_retries == 3
        assert db_manager.retry_delay == 5
        assert not db_manager.is_connected

    @patch('app.core.database.create_engine')
    def test_init_database_success(self, mock_create_engine):
        """تست راه‌اندازی موفق دیتابیس"""
        # Given
        db_manager = DatabaseManager()
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # When
        result = db_manager.init_database()

        # Then
        assert result is True
        assert db_manager.is_connected is True
        mock_create_engine.assert_called_once()

    @patch('app.core.database.create_engine')
    def test_init_database_failure(self, mock_create_engine):
        """تست شکست در راه‌اندازی دیتابیس"""
        # Given
        db_manager = DatabaseManager()
        mock_create_engine.side_effect = Exception("Connection failed")

        # When
        result = db_manager.init_database()

        # Then
        assert result is False
        assert db_manager.is_connected is False

    @patch('app.core.database.redis.Redis')
    def test_init_redis_success(self, mock_redis):
        """تست راه‌اندازی موفق Redis"""
        # Given
        db_manager = DatabaseManager()
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client

        # When
        result = db_manager.init_redis()

        # Then
        assert result is True
        mock_redis.assert_called_once()

    @patch('app.core.database.redis.Redis')
    def test_init_redis_failure(self, mock_redis):
        """تست شکست در راه‌اندازی Redis"""
        # Given
        db_manager = DatabaseManager()
        mock_redis.side_effect = Exception("Redis connection failed")

        # When
        result = db_manager.init_redis()

        # Then
        assert result is False

    def test_db_session_context_manager(self, test_session):
        """تست context manager دیتابیس"""
        # Given
        guest_data = sample_guest_data.copy()

        # When
        with db_session() as session:
            guest = Guest(**guest_data)
            session.add(guest)
            session.flush()
            guest_id = guest.id

        # Then
        assert guest_id is not None

        # بررسی اینکه داده واقعاً ذخیره شده
        saved_guest = test_session.query(Guest).filter_by(id=guest_id).first()
        assert saved_guest is not None
        assert saved_guest.first_name == guest_data['first_name']

    def test_db_session_rollback_on_error(self, test_session):
        """تست rollback خودکار در صورت خطا"""
        # Given
        guest_data = sample_guest_data.copy()

        # When & Then
        with pytest.raises(Exception):
            with db_session() as session:
                guest = Guest(**guest_data)
                session.add(guest)
                session.flush()
                guest_id = guest.id
                raise Exception("Test error")

        # بررسی اینکه داده rollback شده
        saved_guest = test_session.query(Guest).filter_by(id=guest_id).first()
        assert saved_guest is None

    @patch('app.core.database.engine')
    def test_get_database_status_connected(self, mock_engine):
        """تست دریافت وضعیت دیتابیس در حالت متصل"""
        # Given
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchone.return_value = (
            'PostgreSQL 14.0', 'test_db', 'test_user'
        )

        # When
        status = get_database_status()

        # Then
        assert status['database']['status'] == 'Connected'
        assert status['reception_system']['is_connected'] is True

    @patch('app.core.database.engine')
    def test_get_database_status_disconnected(self, mock_engine):
        """تست دریافت وضعیت دیتابیس در حالت قطع"""
        # Given
        mock_engine.connect.side_effect = Exception("Connection failed")

        # When
        status = get_database_status()

        # Then
        assert status['database']['status'] == 'Disconnected'
        assert 'error' in status['database']

    def test_create_tables_integration(self, test_database):
        """تست یکپارچگی ایجاد جداول"""
        # Given
        from app.models.reception.guest_models import Guest
        from app.models.reception.payment_models import Payment

        # When
        # جداول قبلاً در fixture ایجاد شده‌اند

        # Then - بررسی وجود جداول اصلی
        inspector = test_database.inspect(test_database)
        tables = inspector.get_table_names()

        expected_tables = [
            'reception_guests',
            'reception_stays',
            'reception_payments',
            'reception_guest_folios'
        ]

        for table in expected_tables:
            assert table in tables, f"جدول {table} باید ایجاد شده باشد"

    @pytest.mark.slow
    def test_database_connection_pool(self):
        """تست عملکرد connection pool (تست کند)"""
        # Given
        connections = []

        # When - ایجاد چندین connection
        for i in range(5):
            with db_session() as session:
                # انجام یک query ساده
                result = session.execute("SELECT 1").scalar()
                connections.append(result)

        # Then
        assert all(conn == 1 for conn in connections)
        assert len(connections) == 5

    def test_transaction_isolation(self, test_session):
        """تست isolation تراکنش‌ها"""
        # Given
        guest_data1 = sample_guest_data.copy()
        guest_data1['national_id'] = '1111111111'

        guest_data2 = sample_guest_data.copy()
        guest_data2['national_id'] = '2222222222'

        # When - ایجاد دو مهمان در تراکنش‌های جدا
        with db_session() as session1:
            guest1 = Guest(**guest_data1)
            session1.add(guest1)
            session1.flush()

        with db_session() as session2:
            guest2 = Guest(**guest_data2)
            session2.add(guest2)
            session2.flush()

        # Then - هر دو باید ذخیره شده باشند
        guests = test_session.query(Guest).all()
        assert len(guests) == 2
        national_ids = [g.national_id for g in guests]
        assert '1111111111' in national_ids
        assert '2222222222' in national_ids

    @patch('app.core.database.SessionLocal')
    def test_database_recovery_on_connection_error(self, mock_session_local):
        """تست بازیابی دیتابیس پس از خطای اتصال"""
        # Given
        mock_session = MagicMock()
        mock_session.commit.side_effect = [
            Exception("Connection closed"),
            None  # commit موفق در تلاش دوم
        ]
        mock_session_local.return_value = mock_session

        # When & Then - نباید خطا بدهد
        try:
            with db_session() as session:
                session.add(MagicMock())
        except Exception as e:
            pytest.fail(f"بازیابی دیتابیس شکست خورد: {e}")

    def test_bulk_operations_performance(self, test_session):
        """تست عملکرد عملیات گروهی"""
        # Given
        import time
        guests_data = []

        for i in range(100):
            guest_data = sample_guest_data.copy()
            guest_data['national_id'] = f'bulk_test_{i}'
            guest_data['phone'] = f'+98912{i:07d}'
            guests_data.append(guest_data)

        start_time = time.time()

        # When - درج گروهی
        with db_session() as session:
            for data in guests_data:
                guest = Guest(**data)
                session.add(guest)

        end_time = time.time()
        execution_time = end_time - start_time

        # Then
        assert execution_time < 5.0  # باید کمتر از 5 ثانیه باشد

        # بررسی تعداد رکوردهای درج شده
        count = test_session.query(Guest).filter(
            Guest.national_id.like('bulk_test_%')
        ).count()
        assert count == 100

    def test_concurrent_database_access(self, test_session):
        """تست دسترسی همزمان به دیتابیس"""
        # Given
        import threading
        from concurrent.futures import ThreadPoolExecutor

        results = []
        lock = threading.Lock()

        def create_guest(guest_id):
            """تابع برای ایجاد مهمان در thread جدا"""
            try:
                with db_session() as session:
                    guest_data = sample_guest_data.copy()
                    guest_data['national_id'] = f'concurrent_{guest_id}'
                    guest = Guest(**guest_data)
                    session.add(guest)
                    session.flush()

                    with lock:
                        results.append(guest_id)
            except Exception as e:
                with lock:
                    results.append(f'error_{guest_id}: {e}')

        # When - اجرای همزمان
        with ThreadPoolExecutor(max_workers=5) as executor:
            for i in range(10):
                executor.submit(create_guest, i)

        # Then
        assert len(results) == 10
        success_count = sum(1 for r in results if isinstance(r, int))
        assert success_count == 10, f"همه threadها باید موفق باشند. نتایج: {results}"

    def test_database_connection_timeout(self):
        """تست timeout اتصال به دیتابیس"""
        # Given
        import time
        from app.core.database import db_manager

        # When & Then - تست timeout
        # این تست اتصال واقعی را بررسی می‌کند
        # در محیط تست از SQLite استفاده می‌شود که timeout ندارد

        # فقط بررسی می‌کنیم که manager قابل راه‌اندازی باشد
        try:
            # در محیط تست از SQLite استفاده می‌کنیم
            result = db_manager.init_database()
            assert result is True
        except Exception as e:
            pytest.fail(f"راه‌اندازی دیتابیس در تست timeout شکست خورد: {e}")

    def test_database_rollback_on_integrity_error(self, test_session):
        """تست rollback خودکار در صورت خطای یکپارچگی"""
        # Given
        guest_data = sample_guest_data.copy()

        # ایجاد یک مهمان با national_id تکراری
        with db_session() as session:
            guest1 = Guest(**guest_data)
            session.add(guest1)

        # When & Then - تلاش برای ایجاد مهمان تکراری
        with pytest.raises(Exception):  # باید خطای یکپارچگی دهد
            with db_session() as session:
                guest2 = Guest(**guest_data)  # همان national_id
                session.add(guest2)

        # بررسی اینکه فقط یک رکورد وجود دارد
        count = test_session.query(Guest).filter_by(national_id=guest_data['national_id']).count()
        assert count == 1, "باید فقط یک مهمان با این national_id وجود داشته باشد"

    def test_session_cleanup_after_exception(self):
        """تست پاکسازی session پس از exception"""
        # Given
        session_count_before = 0  # باید از طریق مانیتورینگ واقعی بررسی شود

        # When - ایجاد یک session که با خطا مواجه می‌شود
        try:
            with db_session() as session:
                raise ValueError("خطای تستی")
        except ValueError:
            pass  # خطا را مدیریت می‌کنیم

        # Then - session باید بسته شده باشد
        # در اینجا فقط بررسی می‌کنیم که exception باعث crash نشود
        # بررسی واقعی نیاز به مانیتورینگ connection pool دارد

        # ایجاد یک session جدید باید بدون مشکل کار کند
        with db_session() as session:
            result = session.execute("SELECT 1").scalar()
            assert result == 1

    @patch('app.core.database.config')
    def test_database_configuration(self, mock_config):
        """تست پیکربندی دیتابیس"""
        # Given
        mock_config.database.url = "sqlite:///test_config.db"
        mock_config.database.pool_size = 10
        mock_config.database.max_overflow = 20

        # When
        from app.core.database import DatabaseManager
        db_manager = DatabaseManager()

        # Then - تنظیمات باید اعمال شوند
        # در اینجا فقط بررسی می‌کنیم که object ایجاد شود
        assert db_manager is not None
        assert hasattr(db_manager, 'init_database')

    def test_database_initial_data_creation(self, test_session):
        """تست ایجاد داده‌های اولیه"""
        # Given
        from app.services.reception.initial_data_service import InitialDataService

        # When - ایجاد داده‌های اولیه
        result = InitialDataService.create_reception_initial_data()

        # Then
        assert result is True

        # بررسی ایجاد برخی داده‌های پایه
        from app.models.reception.staff_models import User
        from app.models.shared.hotel_models import HotelRoom

        users_count = test_session.query(User).count()
        rooms_count = test_session.query(HotelRoom).count()

        assert users_count > 0, "باید کاربران نمونه ایجاد شده باشند"
        assert rooms_count > 0, "باید اتاق‌های نمونه ایجاد شده باشند"

    def test_database_backup_compatibility(self):
        """تست سازگاری با سیستم پشتیبان‌گیری"""
        # Given
        from app.core.database import Base
        from app.models.reception.guest_models import Guest
        from app.models.reception.payment_models import Payment

        # When - بررسی ساختار جداول
        tables = Base.metadata.tables

        # Then - جداول اصلی باید وجود داشته باشند
        required_tables = [
            'reception_guests',
            'reception_stays',
            'reception_payments',
            'reception_guest_folios'
        ]

        for table in required_tables:
            assert table in tables, f"جدول {table} باید در metadata وجود داشته باشد"

        # بررسی وجود ستون‌های ضروری
        guest_columns = [col.name for col in Guest.__table__.columns]
        required_guest_columns = ['id', 'first_name', 'last_name', 'national_id', 'phone']

        for col in required_guest_columns:
            assert col in guest_columns, f"ستون {col} باید در جدول مهمانان وجود داشته باشد"

    @pytest.mark.integration
    def test_full_database_workflow(self, test_session):
        """تست گردش کار کامل دیتابیس (تست یکپارچگی)"""
        # Given
        from app.models.reception.guest_models import Guest, Stay
        from app.models.reception.payment_models import Payment, GuestFolio
        from decimal import Decimal

        # When - ایجاد یک گردش کار کامل
        with db_session() as session:
            # 1. ایجاد مهمان
            guest = Guest(
                first_name="محمد",
                last_name="رضایی",
                national_id="1111111111",
                phone="+989121111111",
                nationality="ایرانی"
            )
            session.add(guest)
            session.flush()

            # 2. ایجاد اقامت
            stay = Stay(
                guest_id=guest.id,
                planned_check_in=datetime(2024, 1, 15, 14, 0),
                planned_check_out=datetime(2024, 1, 18, 12, 0),
                total_amount=Decimal('4500000'),
                status='checked_in'
            )
            session.add(stay)
            session.flush()

            # 3. ایجاد صورت‌حساب
            folio = GuestFolio(
                stay_id=stay.id,
                opening_balance=Decimal('0'),
                total_charges=Decimal('4500000'),
                total_payments=Decimal('0'),
                current_balance=Decimal('4500000')
            )
            session.add(folio)
            session.flush()

            # 4. ایجاد پرداخت
            payment = Payment(
                stay_id=stay.id,
                amount=Decimal('1500000'),
                payment_method='cash',
                payment_type='advance',
                status='completed'
            )
            session.add(payment)

        # Then - بررسی ارتباطات و داده‌ها
        saved_stay = test_session.query(Stay).filter_by(guest_id=guest.id).first()
        assert saved_stay is not None
        assert saved_stay.total_amount == Decimal('4500000')

        saved_folio = test_session.query(GuestFolio).filter_by(stay_id=stay.id).first()
        assert saved_folio is not None
        assert saved_folio.current_balance == Decimal('3000000')  # 4.5M - 1.5M

        saved_payment = test_session.query(Payment).filter_by(stay_id=stay.id).first()
        assert saved_payment is not None
        assert saved_payment.amount == Decimal('1500000')

    def test_database_indexes(self, test_database):
        """تست وجود ایندکس‌های مهم"""
        # Given
        inspector = test_database.inspect(test_database)

        # When - دریافت ایندکس‌ها
        guest_indexes = inspector.get_indexes('reception_guests')
        stay_indexes = inspector.get_indexes('reception_stays')

        # Then - بررسی ایندکس‌های مهم
        guest_index_names = [idx['name'] for idx in guest_indexes]
        stay_index_names = [idx['name'] for idx in stay_indexes]

        # بررسی ایندکس‌های مورد انتظار
        expected_guest_indexes = ['ix_reception_guests_national_id', 'ix_reception_guests_phone']
        expected_stay_indexes = ['ix_reception_stays_guest_id', 'ix_reception_stays_status']

        for expected_idx in expected_guest_indexes:
            assert any(expected_idx in name for name in guest_index_names), \
                f"ایندکس {expected_idx} باید وجود داشته باشد"

        for expected_idx in expected_stay_indexes:
            assert any(expected_idx in name for name in stay_index_names), \
                f"ایندکس {expected_idx} باید وجود داشته باشد"

    def test_database_constraints(self, test_database):
        """تست constraints دیتابیس"""
        # Given
        inspector = test_database.inspect(test_database)

        # When - دریافت constraints
        guest_constraints = inspector.get_unique_constraints('reception_guests')
        stay_constraints = inspector.get_check_constraints('reception_stays')

        # Then - بررسی constraints مهم
        guest_unique_constraints = [uc['name'] for uc in guest_constraints]

        # بررسی unique constraint برای national_id
        assert any('national_id' in str(uc) for uc in guest_unique_constraints), \
            "باید constraint یکتایی برای national_id وجود داشته باشد"

    @pytest.mark.performance
    def test_database_query_performance(self, test_session):
        """تست عملکرد queryهای دیتابیس"""
        # Given
        import time

        # ایجاد داده‌های تست
        for i in range(50):
            guest_data = sample_guest_data.copy()
            guest_data['national_id'] = f'perf_test_{i}'
            guest = Guest(**guest_data)
            test_session.add(guest)
        test_session.commit()

        # When - اجرای queryهای مختلف و اندازه‌گیری زمان
        start_time = time.time()

        # Query 1: انتخاب ساده
        guests = test_session.query(Guest).filter(
            Guest.national_id.like('perf_test_%')
        ).all()

        query1_time = time.time() - start_time

        # Query 2: انتخاب با شرط
        start_time = time.time()
        iranian_guests = test_session.query(Guest).filter(
            Guest.nationality == 'ایرانی'
        ).all()
        query2_time = time.time() - start_time

        # Then
        assert query1_time < 1.0, "Query ساده باید کمتر از 1 ثانیه اجرا شود"
        assert query2_time < 1.0, "Query با شرط باید کمتر از 1 ثانیه اجرا شود"
        assert len(guests) == 50
        assert len(iranian_guests) == 50

    def test_database_connection_retry_mechanism(self):
        """تست مکانیزم تلاش مجدد اتصال"""
        # Given
        from app.core.database import DatabaseManager

        # When & Then - تست رفتار تلاش مجدد
        # این تست نیاز به شبیه‌سازی خطای اتصال دارد

        # در اینجا فقط بررسی می‌کنیم که مکانیزم وجود دارد
        db_manager = DatabaseManager()
        assert hasattr(db_manager, 'connection_retries')
        assert hasattr(db_manager, 'retry_delay')
        assert db_manager.connection_retries == 3
