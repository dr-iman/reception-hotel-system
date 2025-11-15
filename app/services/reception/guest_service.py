# app/services/reception/guest_service.py
"""
سرویس مدیریت مهمانان و اقامت‌ها
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import db_session
from app.models.reception.guest_models import Guest, Stay, Companion, CompanionStay
from app.models.reception.room_status_models import RoomAssignment
from app.models.reception.payment_models import GuestFolio, FolioTransaction
from config import config

logger = logging.getLogger(__name__)

class GuestService:
    """سرویس مدیریت کامل مهمانان"""

    @staticmethod
    def register_guest_from_reservation(guest_data: Dict, reservation_data: Dict) -> Dict[str, Any]:
        """ثبت مهمان جدید از سیستم رزرواسیون"""
        try:
            with db_session() as session:
                # بررسی وجود مهمان
                existing_guest = session.query(Guest).filter(
                    Guest.national_id == guest_data.get('national_id')
                ).first()

                if existing_guest:
                    guest = existing_guest
                    # به‌روزرسانی اطلاعات مهمان موجود
                    GuestService._update_guest_info(guest, guest_data)
                else:
                    # ایجاد مهمان جدید
                    guest = GuestService._create_guest(guest_data)
                    session.add(guest)

                session.flush()  # گرفتن ID مهمان

                # ایجاد اقامت
                stay = GuestService._create_stay(guest.id, reservation_data)
                session.add(stay)
                session.flush()

                # ایجاد صورت‌حساب
                folio = GuestService._create_guest_folio(stay.id)
                session.add(folio)

                # ثبت همراهان
                companions_data = guest_data.get('companions', [])
                for companion_data in companions_data:
                    companion = GuestService._create_companion(guest.id, companion_data)
                    session.add(companion)
                    session.flush()

                    # ارتباط همراه با اقامت
                    companion_stay = CompanionStay(
                        companion_id=companion.id,
                        stay_id=stay.id
                    )
                    session.add(companion_stay)

                session.commit()

                logger.info(f"✅ مهمان جدید ثبت شد: {guest.full_name} (ID: {guest.id})")

                return {
                    'success': True,
                    'guest_id': guest.id,
                    'stay_id': stay.id,
                    'folio_id': folio.id,
                    'message': 'مهمان با موفقیت ثبت شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ثبت مهمان: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'GUEST_REGISTRATION_ERROR'
            }

    @staticmethod
    def check_in_guest(stay_id: int, room_id: int, check_in_time: datetime = None) -> Dict[str, Any]:
        """ثبت ورود مهمان و تخصیص اتاق"""
        try:
            with db_session() as session:
                stay = session.query(Stay).filter(Stay.id == stay_id).first()
                if not stay:
                    return {
                        'success': False,
                        'error': 'اقامت یافت نشد',
                        'error_code': 'STAY_NOT_FOUND'
                    }

                # به‌روزرسانی زمان ورود واقعی
                stay.actual_check_in = check_in_time or datetime.now()
                stay.status = 'checked_in'

                # تخصیص اتاق
                room_assignment = RoomAssignment(
                    stay_id=stay_id,
                    room_id=room_id,
                    assignment_date=date.today(),
                    expected_check_out=stay.planned_check_out.date(),
                    assignment_type='primary'
                )
                session.add(room_assignment)

                # ایجاد تراکنش اتاق در صورت‌حساب
                folio = session.query(GuestFolio).filter(GuestFolio.stay_id == stay_id).first()
                if folio:
                    room_charge = FolioTransaction(
                        folio_id=folio.id,
                        transaction_type='charge',
                        amount=stay.total_amount,
                        description='هزینه اقامت اتاق',
                        category='room_charge',
                        subcategory='daily_rate'
                    )
                    session.add(room_charge)

                    # به‌روزرسانی مانده صورت‌حساب
                    folio.total_charges += stay.total_amount
                    folio.current_balance = folio.total_charges - folio.total_payments

                session.commit()

                logger.info(f"✅ ورود مهمان ثبت شد: Stay ID {stay_id}, Room {room_id}")

                return {
                    'success': True,
                    'stay_id': stay_id,
                    'room_id': room_id,
                    'check_in_time': stay.actual_check_in,
                    'message': 'ورود مهمان با موفقیت ثبت شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ثبت ورود مهمان: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CHECK_IN_ERROR'
            }

    @staticmethod
    def check_out_guest(stay_id: int, check_out_time: datetime = None) -> Dict[str, Any]:
        """ثبت خروج مهمان و تسویه حساب"""
        try:
            with db_session() as session:
                stay = session.query(Stay).filter(Stay.id == stay_id).first()
                if not stay:
                    return {
                        'success': False,
                        'error': 'اقامت یافت نشد',
                        'error_code': 'STAY_NOT_FOUND'
                    }

                # بررسی تسویه حساب
                folio = session.query(GuestFolio).filter(GuestFolio.stay_id == stay_id).first()
                if folio and folio.current_balance > 0:
                    return {
                        'success': False,
                        'error': 'مامان هنوز تسویه حساب نشده است',
                        'error_code': 'BALANCE_NOT_ZERO',
                        'remaining_balance': float(folio.current_balance)
                    }

                # به‌روزرسانی زمان خروج واقعی
                stay.actual_check_out = check_out_time or datetime.now()
                stay.status = 'checked_out'

                # به‌روزرسانی تخصیص اتاق
                room_assignment = session.query(RoomAssignment).filter(
                    RoomAssignment.stay_id == stay_id,
                    RoomAssignment.actual_check_out.is_(None)
                ).first()

                if room_assignment:
                    room_assignment.actual_check_out = date.today()

                # به‌روزرسانی صورت‌حساب
                if folio:
                    folio.folio_status = 'settled'

                session.commit()

                logger.info(f"✅ خروج مهمان ثبت شد: Stay ID {stay_id}")

                return {
                    'success': True,
                    'stay_id': stay_id,
                    'check_out_time': stay.actual_check_out,
                    'message': 'خروج مهمان با موفقیت ثبت شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ثبت خروج مهمان: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CHECK_OUT_ERROR'
            }

    @staticmethod
    def get_guest_details(guest_id: int) -> Dict[str, Any]:
        """دریافت اطلاعات کامل مهمان"""
        try:
            with db_session() as session:
                guest = session.query(Guest).filter(Guest.id == guest_id).first()
                if not guest:
                    return {
                        'success': False,
                        'error': 'مهمان یافت نشد',
                        'error_code': 'GUEST_NOT_FOUND'
                    }

                # اطلاعات اقامت‌های فعال
                active_stays = session.query(Stay).filter(
                    Stay.guest_id == guest_id,
                    Stay.status.in_(['confirmed', 'checked_in'])
                ).all()

                # اطلاعات همراهان
                companions = session.query(Companion).filter(
                    Companion.guest_id == guest_id
                ).all()

                guest_data = {
                    'id': guest.id,
                    'full_name': f"{guest.first_name} {guest.last_name}",
                    'national_id': guest.national_id,
                    'passport_number': guest.passport_number,
                    'phone': guest.phone,
                    'email': guest.email,
                    'nationality': guest.nationality,
                    'vip_status': guest.vip_status,
                    'special_requests': guest.special_requests,
                    'active_stays': [
                        {
                            'stay_id': stay.id,
                            'status': stay.status,
                            'planned_check_in': stay.planned_check_in,
                            'planned_check_out': stay.planned_check_out,
                            'actual_check_in': stay.actual_check_in
                        }
                        for stay in active_stays
                    ],
                    'companions': [
                        {
                            'id': comp.id,
                            'full_name': f"{comp.first_name} {comp.last_name}",
                            'relationship': comp.relationship
                        }
                        for comp in companions
                    ]
                }

                return {
                    'success': True,
                    'guest': guest_data
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاعات مهمان: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'GUEST_DETAILS_ERROR'
            }

    @staticmethod
    def search_guests(search_term: str, search_type: str = 'name') -> Dict[str, Any]:
        """جستجوی مهمانان"""
        try:
            with db_session() as session:
                query = session.query(Guest)

                if search_type == 'name':
                    query = query.filter(
                        (Guest.first_name.ilike(f"%{search_term}%")) |
                        (Guest.last_name.ilike(f"%{search_term}%"))
                    )
                elif search_type == 'national_id':
                    query = query.filter(Guest.national_id.ilike(f"%{search_term}%"))
                elif search_type == 'phone':
                    query = query.filter(Guest.phone.ilike(f"%{search_term}%"))
                elif search_type == 'passport':
                    query = query.filter(Guest.passport_number.ilike(f"%{search_term}%"))

                guests = query.limit(50).all()

                results = [
                    {
                        'id': guest.id,
                        'full_name': f"{guest.first_name} {guest.last_name}",
                        'national_id': guest.national_id,
                        'phone': guest.phone,
                        'email': guest.email,
                        'vip_status': guest.vip_status
                    }
                    for guest in guests
                ]

                return {
                    'success': True,
                    'count': len(results),
                    'guests': results
                }

        except Exception as e:
            logger.error(f"❌ خطا در جستجوی مهمانان: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'GUEST_SEARCH_ERROR'
            }

    # متدهای کمکی خصوصی
    @staticmethod
    def _create_guest(guest_data: Dict) -> Guest:
        """ایجاد شیء مهمان جدید"""
        return Guest(
            first_name=guest_data.get('first_name', ''),
            last_name=guest_data.get('last_name', ''),
            national_id=guest_data.get('national_id'),
            passport_number=guest_data.get('passport_number'),
            gender=guest_data.get('gender'),
            date_of_birth=guest_data.get('date_of_birth'),
            nationality=guest_data.get('nationality', 'ایرانی'),
            phone=guest_data.get('phone', ''),
            email=guest_data.get('email'),
            address=guest_data.get('address'),
            company_name=guest_data.get('company_name'),
            business_title=guest_data.get('business_title'),
            preferences=guest_data.get('preferences', {}),
            special_requests=guest_data.get('special_requests'),
            vip_status=guest_data.get('vip_status', False)
        )

    @staticmethod
    def _update_guest_info(guest: Guest, guest_data: Dict):
        """به‌روزرسانی اطلاعات مهمان موجود"""
        guest.first_name = guest_data.get('first_name', guest.first_name)
        guest.last_name = guest_data.get('last_name', guest.last_name)
        guest.phone = guest_data.get('phone', guest.phone)
        guest.email = guest_data.get('email', guest.email)
        guest.nationality = guest_data.get('nationality', guest.nationality)
        guest.preferences = guest_data.get('preferences', guest.preferences)
        guest.special_requests = guest_data.get('special_requests', guest.special_requests)
        guest.vip_status = guest_data.get('vip_status', guest.vip_status)

    @staticmethod
    def _create_stay(guest_id: int, reservation_data: Dict) -> Stay:
        """ایجاد شیء اقامت جدید"""
        return Stay(
            guest_id=guest_id,
            reservation_id=reservation_data.get('reservation_id'),
            planned_check_in=reservation_data.get('check_in_date'),
            planned_check_out=reservation_data.get('check_out_date'),
            stay_purpose=reservation_data.get('purpose', 'leisure'),
            total_amount=Decimal(str(reservation_data.get('total_amount', 0))),
            advance_payment=Decimal(str(reservation_data.get('advance_payment', 0))),
            remaining_balance=Decimal(str(reservation_data.get('remaining_balance', 0))),
            status='confirmed'
        )

    @staticmethod
    def _create_companion(guest_id: int, companion_data: Dict) -> Companion:
        """ایجاد شیء همراه جدید"""
        return Companion(
            guest_id=guest_id,
            first_name=companion_data.get('first_name', ''),
            last_name=companion_data.get('last_name', ''),
            relationship=companion_data.get('relationship', 'همراه'),
            date_of_birth=companion_data.get('date_of_birth'),
            national_id=companion_data.get('national_id'),
            phone=companion_data.get('phone')
        )

    @staticmethod
    def _create_guest_folio(stay_id: int) -> GuestFolio:
        """ایجاد صورت‌حساب مهمان"""
        return GuestFolio(
            stay_id=stay_id,
            opening_balance=0,
            total_charges=0,
            total_payments=0,
            current_balance=0,
            folio_status='open'
        )

    @staticmethod
    def update_guest_departure(guest_data: Dict, stay_data: Dict) -> Dict[str, Any]:
        """به‌روزرسانی وضعیت خروج مهمان (مورد استفاده در SyncManager)"""
        try:
            with db_session() as session:
                stay = session.query(Stay).filter(
                    Stay.reservation_id == stay_data.get('reservation_id')
                ).first()

                if stay:
                    stay.status = 'checked_out'
                    stay.actual_check_out = datetime.now()
                    session.commit()

                    return {
                        'success': True,
                        'message': 'وضعیت خروج به‌روزرسانی شد'
                    }
                else:
                    return {
                        'success': False,
                        'error': 'اقامت یافت نشد',
                        'error_code': 'STAY_NOT_FOUND'
                    }

        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی وضعیت خروج: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'DEPARTURE_UPDATE_ERROR'
            }

    @staticmethod
    def sync_tomorrows_arrivals(target_date: date) -> Dict[str, Any]:
        """همگام‌سازی مهمانان فردا"""
        # این متد با سیستم رزرواسیون ارتباط برقرار می‌کند
        # در این نسخه شبیه‌سازی شده است
        try:
            logger.info(f"🔄 همگام‌سازی مهمانان فردا: {target_date}")

            # در نسخه واقعی، اینجا با API رزرواسیون ارتباط برقرار می‌شود
            # mock_data = requests.get(f"{config.api.reservation_endpoints['guest_arrivals']}?date={target_date}")

            return {
                'success': True,
                'count': 0,  # در نسخه واقعی تعداد واقعی برگردانده می‌شود
                'message': 'همگام‌سازی مهمانان فردا انجام شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در همگام‌سازی مهمانان فردا: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYNC_ARRIVALS_ERROR'
            }
