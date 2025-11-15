# app/services/reception/initial_data_service.py
"""
سرویس ایجاد داده‌های اولیه و نمونه برای سیستم پذیرش
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import db_session
from app.models.reception.guest_models import Guest, Stay, Companion, CompanionStay
from app.models.reception.room_status_models import RoomAssignment, RoomStatusChange
from app.models.reception.payment_models import Payment, GuestFolio, FolioTransaction, CashierShift
from app.models.reception.housekeeping_models import HousekeepingTask, HousekeepingStaff
from app.models.reception.maintenance_models import MaintenanceRequest, MaintenanceStaff
from app.models.reception.staff_models import User, Department, Role
from app.models.shared.hotel_models import HotelRoom, RoomType
from config import config

logger = logging.getLogger(__name__)

class InitialDataService:
    """سرویس ایجاد داده‌های اولیه سیستم"""

    @staticmethod
    def create_reception_initial_data():
        """ایجاد داده‌های اولیه سیستم پذیرش"""
        try:
            logger.info("🚀 شروع ایجاد داده‌های اولیه سیستم پذیرش...")

            with db_session() as session:
                # ایجاد نقش‌ها و دپارتمان‌ها
                InitialDataService._create_roles_and_departments(session)

                # ایجاد کاربران نمونه
                InitialDataService._create_sample_users(session)

                # ایجاد اتاق‌ها و انواع اتاق
                InitialDataService._create_rooms_and_types(session)

                # ایجاد مهمانان و اقامت‌های نمونه
                InitialDataService._create_sample_guests_and_stays(session)

                # ایجاد داده‌های خانه‌داری
                InitialDataService._create_housekeeping_data(session)

                # ایجاد داده‌های تعمیرات
                InitialDataService._create_maintenance_data(session)

                session.commit()

            logger.info("✅ داده‌های اولیه سیستم پذیرش با موفقیت ایجاد شدند")
            return True

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد داده‌های اولیه: {e}")
            return False

    @staticmethod
    def _create_roles_and_departments(session: Session):
        """ایجاد نقش‌ها و دپارتمان‌های اولیه"""
        departments = [
            {'name': 'پذیرش', 'code': 'RECEPTION', 'description': 'بخش پذیرش و میزبانی'},
            {'name': 'خانه‌داری', 'code': 'HOUSEKEEPING', 'description': 'بخش نظافت و خانه‌داری'},
            {'name': 'تعمیرات', 'code': 'MAINTENANCE', 'description': 'بخش تعمیرات و تاسیسات'},
            {'name': 'مالی', 'code': 'FINANCE', 'description': 'بخش مالی و حسابداری'},
            {'name': 'مدیریت', 'code': 'MANAGEMENT', 'description': 'مدیریت هتل'}
        ]

        roles = [
            {'name': 'مدیر سیستم', 'code': 'ADMIN', 'permissions': ['all']},
            {'name': 'سرپرست پذیرش', 'code': 'RECEPTION_SUPERVISOR', 'permissions': ['reception_manage', 'reports_view']},
            {'name': 'کارمند پذیرش', 'code': 'RECEPTION_AGENT', 'permissions': ['guest_checkin', 'guest_checkout', 'payment_process']},
            {'name': 'سرپرست خانه‌داری', 'code': 'HOUSEKEEPING_SUPERVISOR', 'permissions': ['housekeeping_manage', 'reports_view']},
            {'name': 'کارگر خانه‌داری', 'code': 'HOUSEKEEPING_STAFF', 'permissions': ['housekeeping_tasks']},
            {'name': 'تکنسین تعمیرات', 'code': 'MAINTENANCE_TECH', 'permissions': ['maintenance_work']},
            {'name': 'صندوق‌دار', 'code': 'CASHIER', 'permissions': ['payment_process', 'cashier_shift']}
        ]

        for dept_data in departments:
            department = session.query(Department).filter_by(code=dept_data['code']).first()
            if not department:
                department = Department(**dept_data)
                session.add(department)

        for role_data in roles:
            role = session.query(Role).filter_by(code=role_data['code']).first()
            if not role:
                role = Role(**role_data)
                session.add(role)

        session.flush()
        logger.info("✅ نقش‌ها و دپارتمان‌های اولیه ایجاد شدند")

    @staticmethod
    def _create_sample_users(session: Session):
        """ایجاد کاربران نمونه"""
        users = [
            {
                'username': 'admin',
                'password_hash': 'hashed_password_123',  # در عمل باید hash شود
                'first_name': 'مدیر',
                'last_name': 'سیستم',
                'email': 'admin@hotel.com',
                'phone': '+982112345671',
                'is_active': True,
                'role_id': session.query(Role.id).filter_by(code='ADMIN').scalar(),
                'department_id': session.query(Department.id).filter_by(code='MANAGEMENT').scalar()
            },
            {
                'username': 'reception1',
                'password_hash': 'hashed_password_123',
                'first_name': 'علی',
                'last_name': 'محمدی',
                'email': 'reception1@hotel.com',
                'phone': '+982112345672',
                'is_active': True,
                'role_id': session.query(Role.id).filter_by(code='RECEPTION_AGENT').scalar(),
                'department_id': session.query(Department.id).filter_by(code='RECEPTION').scalar()
            },
            {
                'username': 'housekeeping1',
                'password_hash': 'hashed_password_123',
                'first_name': 'فاطمه',
                'last_name': 'احمدی',
                'email': 'housekeeping1@hotel.com',
                'phone': '+982112345673',
                'is_active': True,
                'role_id': session.query(Role.id).filter_by(code='HOUSEKEEPING_STAFF').scalar(),
                'department_id': session.query(Department.id).filter_by(code='HOUSEKEEPING').scalar()
            }
        ]

        for user_data in users:
            user = session.query(User).filter_by(username=user_data['username']).first()
            if not user:
                user = User(**user_data)
                session.add(user)

        session.flush()
        logger.info("✅ کاربران نمونه ایجاد شدند")

    @staticmethod
    def _create_rooms_and_types(session: Session):
        """ایجاد اتاق‌ها و انواع اتاق نمونه"""
        room_types = [
            {
                'name': 'اتاق استاندارد',
                'code': 'STD',
                'description': 'اتاق استاندارد دو تخته',
                'base_rate': Decimal('1500000'),
                'max_occupancy': 2,
                'amenities': ['TV', 'WiFi', 'تهویه مطبوع']
            },
            {
                'name': 'اتاق دلوکس',
                'code': 'DLX',
                'description': 'اتاق دلوکس با امکانات ویژه',
                'base_rate': Decimal('2500000'),
                'max_occupancy': 3,
                'amenities': ['TV', 'WiFi', 'تهویه مطبوع', 'مینی بار', 'صندوق امانات']
            },
            {
                'name': 'سوئیت',
                'code': 'SUITE',
                'description': 'سوئیت مجلل',
                'base_rate': Decimal('4000000'),
                'max_occupancy': 4,
                'amenities': ['TV', 'WiFi', 'تهویه مطبوع', 'مینی بار', 'صندوق امانات', 'جکوزی']
            }
        ]

        for type_data in room_types:
            room_type = session.query(RoomType).filter_by(code=type_data['code']).first()
            if not room_type:
                room_type = RoomType(**type_data)
                session.add(room_type)

        session.flush()

        # ایجاد اتاق‌های نمونه
        rooms = []
        for floor in range(1, 6):
            for room_num in range(1, 21):
                room_number = f"{floor}{room_num:02d}"

                if room_num <= 10:
                    room_type_id = session.query(RoomType.id).filter_by(code='STD').scalar()
                elif room_num <= 15:
                    room_type_id = session.query(RoomType.id).filter_by(code='DLX').scalar()
                else:
                    room_type_id = session.query(RoomType.id).filter_by(code='SUITE').scalar()

                rooms.append({
                    'room_number': room_number,
                    'floor': floor,
                    'room_type_id': room_type_id,
                    'is_active': True,
                    'bed_type': 'دو تخته' if room_num <= 10 else 'یک تخته king',
                    'view_type': 'شهری' if room_num % 2 == 0 else 'حیاط'
                })

        for room_data in rooms:
            room = session.query(HotelRoom).filter_by(room_number=room_data['room_number']).first()
            if not room:
                room = HotelRoom(**room_data)
                session.add(room)

        session.flush()
        logger.info("✅ اتاق‌ها و انواع اتاق ایجاد شدند")

    @staticmethod
    def _create_sample_guests_and_stays(session: Session):
        """ایجاد مهمانان و اقامت‌های نمونه"""
        sample_guests = [
            {
                'first_name': 'رضا',
                'last_name': 'اکبری',
                'national_id': '1234567890',
                'phone': '+989121234567',
                'email': 'reza.akbari@example.com',
                'nationality': 'ایرانی',
                'date_of_birth': date(1985, 5, 15)
            },
            {
                'first_name': 'سارا',
                'last_name': 'محمدی',
                'national_id': '0987654321',
                'phone': '+989123456789',
                'email': 'sara.mohammadi@example.com',
                'nationality': 'ایرانی',
                'date_of_birth': date(1990, 8, 22)
            },
            {
                'first_name': 'John',
                'last_name': 'Smith',
                'passport_number': 'AB123456',
                'phone': '+441234567890',
                'email': 'john.smith@example.com',
                'nationality': 'آمریکایی',
                'date_of_birth': date(1978, 3, 10)
            }
        ]

        for guest_data in sample_guests:
            guest = session.query(Guest).filter_by(national_id=guest_data.get('national_id')).first()
            if not guest:
                guest = Guest(**guest_data)
                session.add(guest)

        session.flush()

        # ایجاد اقامت‌های نمونه
        today = date.today()
        sample_stays = [
            {
                'guest_id': session.query(Guest.id).filter_by(national_id='1234567890').scalar(),
                'planned_check_in': datetime(today.year, today.month, today.day, 14, 0),
                'planned_check_out': datetime(today.year, today.month, today.day + 3, 12, 0),
                'stay_purpose': 'business',
                'total_amount': Decimal('4500000'),
                'advance_payment': Decimal('1500000'),
                'remaining_balance': Decimal('3000000'),
                'status': 'checked_in'
            },
            {
                'guest_id': session.query(Guest.id).filter_by(national_id='0987654321').scalar(),
                'planned_check_in': datetime(today.year, today.month, today.day + 1, 14, 0),
                'planned_check_out': datetime(today.year, today.month, today.day + 4, 12, 0),
                'stay_purpose': 'leisure',
                'total_amount': Decimal('6000000'),
                'advance_payment': Decimal('2000000'),
                'remaining_balance': Decimal('4000000'),
                'status': 'confirmed'
            }
        ]

        for stay_data in sample_stays:
            stay = Stay(**stay_data)
            session.add(stay)

        session.flush()

        # ایجاد صورت‌حساب‌های نمونه
        for stay in session.query(Stay).all():
            folio = GuestFolio(
                stay_id=stay.id,
                opening_balance=Decimal('0'),
                total_charges=stay.total_amount,
                total_payments=stay.advance_payment,
                current_balance=stay.remaining_balance,
                folio_status='open'
            )
            session.add(folio)

        session.flush()
        logger.info("✅ مهمانان و اقامت‌های نمونه ایجاد شدند")

    @staticmethod
    def _create_housekeeping_data(session: Session):
        """ایجاد داده‌های خانه‌داری"""
        # ایجاد پرسنل خانه‌داری
        housekeeping_staff = [
            {
                'first_name': 'زهرا',
                'last_name': 'کریمی',
                'phone': '+989124567890',
                'is_active': True,
                'specialization': 'cleaning'
            },
            {
                'first_name': 'مریم',
                'last_name': 'جعفری',
                'phone': '+989125678901',
                'is_active': True,
                'specialization': 'laundry'
            }
        ]

        for staff_data in housekeeping_staff:
            staff = HousekeepingStaff(**staff_data)
            session.add(staff)

        session.flush()

        # ایجاد وظایف خانه‌داری نمونه
        today = datetime.now()
        sample_tasks = [
            {
                'room_id': session.query(HotelRoom.id).filter_by(room_number='101').scalar(),
                'task_type': 'daily_cleaning',
                'assigned_to': session.query(HousekeepingStaff.id).first(),
                'scheduled_time': today.replace(hour=10, minute=0),
                'priority': 'medium',
                'status': 'completed'
            },
            {
                'room_id': session.query(HotelRoom.id).filter_by(room_number='201').scalar(),
                'task_type': 'checkout_cleaning',
                'assigned_to': session.query(HousekeepingStaff.id).first(),
                'scheduled_time': today.replace(hour=11, minute=0),
                'priority': 'high',
                'status': 'in_progress'
            }
        ]

        for task_data in sample_tasks:
            task = HousekeepingTask(**task_data)
            session.add(task)

        logger.info("✅ داده‌های خانه‌داری ایجاد شدند")

    @staticmethod
    def _create_maintenance_data(session: Session):
        """ایجاد داده‌های تعمیرات"""
        # ایجاد تکنسین‌های تعمیرات
        maintenance_staff = [
            {
                'first_name': 'حمید',
                'last_name': 'رضایی',
                'phone': '+989126789012',
                'is_active': True,
                'specialization': 'electrical'
            },
            {
                'first_name': 'محمد',
                'last_name': 'حسینی',
                'phone': '+989127890123',
                'is_active': True,
                'specialization': 'plumbing'
            }
        ]

        for staff_data in maintenance_staff:
            staff = MaintenanceStaff(**staff_data)
            session.add(staff)

        session.flush()

        # ایجاد درخواست‌های تعمیرات نمونه
        sample_requests = [
            {
                'room_id': session.query(HotelRoom.id).filter_by(room_number='105').scalar(),
                'issue_type': 'electrical',
                'description': 'لامپ خواب خراب است',
                'reported_by': session.query(User.id).filter_by(username='reception1').scalar(),
                'priority': 'medium',
                'status': 'assigned'
            }
        ]

        for request_data in sample_requests:
            request = MaintenanceRequest(**request_data)
            session.add(request)

        logger.info("✅ داده‌های تعمیرات ایجاد شدند")

    @staticmethod
    def clear_sample_data():
        """پاک کردن داده‌های نمونه (برای تست)"""
        try:
            with db_session() as session:
                # حذف داده‌های نمونه به ترتیب وابستگی
                session.query(FolioTransaction).delete()
                session.query(Payment).delete()
                session.query(GuestFolio).delete()
                session.query(CompanionStay).delete()
                session.query(Companion).delete()
                session.query(Stay).delete()
                session.query(Guest).delete()

                session.query(RoomAssignment).delete()
                session.query(RoomStatusChange).delete()

                session.query(HousekeepingTask).delete()
                session.query(HousekeepingStaff).delete()

                session.query(MaintenanceRequest).delete()
                session.query(MaintenanceStaff).delete()

                session.query(User).delete()
                session.query(Role).delete()
                session.query(Department).delete()

                session.commit()

            logger.info("✅ داده‌های نمونه با موفقیت پاک شدند")
            return True

        except Exception as e:
            logger.error(f"❌ خطا در پاک کردن داده‌های نمونه: {e}")
            return False

    @staticmethod
    def get_initial_data_status() -> Dict[str, Any]:
        """دریافت وضعیت داده‌های اولیه"""
        try:
            with db_session() as session:
                counts = {
                    'guests': session.query(Guest).count(),
                    'stays': session.query(Stay).count(),
                    'rooms': session.query(HotelRoom).count(),
                    'users': session.query(User).count(),
                    'housekeeping_staff': session.query(HousekeepingStaff).count(),
                    'maintenance_staff': session.query(MaintenanceStaff).count()
                }

                return {
                    'success': True,
                    'data_status': counts,
                    'has_initial_data': any(counts.values()),
                    'message': 'وضعیت داده‌های اولیه بررسی شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در بررسی وضعیت داده‌های اولیه: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'INITIAL_DATA_STATUS_ERROR'
            }
