# app/services/reception/room_service.py
"""
سرویس مدیریت اتاق‌ها و وضعیت‌ها
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session, joinedload

from app.core.database import db_session
from app.models.reception.room_status_models import RoomAssignment, RoomStatusChange, RoomStatusSnapshot
from app.models.reception.guest_models import Stay, Guest
from config import config

logger = logging.getLogger(__name__)

class RoomService:
    """سرویس مدیریت اتاق‌ها"""

    @staticmethod
    def get_room_status(room_id: int = None) -> Dict[str, Any]:
        """دریافت وضعیت اتاق‌ها"""
        try:
            with db_session() as session:
                if room_id:
                    # وضعیت یک اتاق خاص
                    room_status = RoomService._get_single_room_status(session, room_id)
                    return {
                        'success': True,
                        'room': room_status
                    }
                else:
                    # وضعیت تمام اتاق‌ها
                    rooms_status = RoomService._get_all_rooms_status(session)
                    return {
                        'success': True,
                        'rooms': rooms_status,
                        'count': len(rooms_status)
                    }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت وضعیت اتاق‌ها: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'ROOM_STATUS_ERROR'
            }

    @staticmethod
    def update_room_status(room_id: int, new_status: str,
                         changed_by: int, reason: str = None) -> Dict[str, Any]:
        """به‌روزرسانی وضعیت اتاق"""
        try:
            with db_session() as session:
                # دریافت آخرین وضعیت
                last_status = session.query(RoomStatusChange).filter(
                    RoomStatusChange.room_id == room_id
                ).order_by(RoomStatusChange.created_at.desc()).first()

                previous_status = last_status.new_status if last_status else 'vacant'

                # ایجاد تغییر وضعیت جدید
                status_change = RoomStatusChange(
                    room_id=room_id,
                    previous_status=previous_status,
                    new_status=new_status,
                    status_reason=reason,
                    changed_by=changed_by,
                    change_type='manual'
                )

                session.add(status_change)
                session.commit()

                logger.info(f"✅ وضعیت اتاق {room_id} از {previous_status} به {new_status} تغییر یافت")

                return {
                    'success': True,
                    'room_id': room_id,
                    'previous_status': previous_status,
                    'new_status': new_status,
                    'message': 'وضعیت اتاق با موفقیت به‌روزرسانی شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی وضعیت اتاق: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'ROOM_STATUS_UPDATE_ERROR'
            }

    @staticmethod
    def get_available_rooms(check_in: date, check_out: date,
                          room_type: str = None) -> Dict[str, Any]:
        """دریافت اتاق‌های خالی در بازه زمانی مشخص"""
        try:
            with db_session() as session:
                # اتاق‌های اشغال شده در بازه مورد نظر
                occupied_rooms = session.query(RoomAssignment.room_id).filter(
                    RoomAssignment.assignment_date <= check_out,
                    RoomAssignment.expected_check_out >= check_in,
                    RoomAssignment.actual_check_out.is_(None)
                ).subquery()

                # اتاق‌های خارج از سرویس
                out_of_service_rooms = session.query(RoomStatusChange.room_id).filter(
                    RoomStatusChange.new_status.in_(['maintenance', 'out_of_order']),
                    RoomStatusChange.created_at == session.query(
                        RoomStatusChange.created_at
                    ).filter(
                        RoomStatusChange.room_id == RoomStatusChange.room_id
                    ).order_by(RoomStatusChange.created_at.desc()).limit(1).scalar_subquery()
                ).subquery()

                # اتاق‌های خالی
                from app.models.shared.hotel_models import HotelRoom  # از سیستم مشترک

                query = session.query(HotelRoom).filter(
                    HotelRoom.id.notin_(occupied_rooms),
                    HotelRoom.id.notin_(out_of_service_rooms),
                    HotelRoom.is_active == True
                )

                if room_type:
                    query = query.filter(HotelRoom.room_type == room_type)

                available_rooms = query.all()

                rooms_data = [
                    {
                        'room_id': room.id,
                        'room_number': room.room_number,
                        'room_type': room.room_type,
                        'floor': room.floor,
                        'bed_type': room.bed_type,
                        'max_occupancy': room.max_occupancy,
                        'amenities': room.amenities or [],
                        'rate_per_night': float(room.rate_per_night) if room.rate_per_night else 0.0
                    }
                    for room in available_rooms
                ]

                return {
                    'success': True,
                    'available_rooms': rooms_data,
                    'count': len(rooms_data),
                    'check_in': check_in,
                    'check_out': check_out
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت اتاق‌های خالی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'AVAILABLE_ROOMS_ERROR'
            }

    @staticmethod
    def get_room_assignments(room_id: int = None, date: date = None) -> Dict[str, Any]:
        """دریافت تخصیص‌های اتاق"""
        try:
            with db_session() as session:
                query = session.query(RoomAssignment).options(
                    joinedload(RoomAssignment.stay).joinedload(Stay.guest)
                )

                if room_id:
                    query = query.filter(RoomAssignment.room_id == room_id)

                if date:
                    query = query.filter(
                        RoomAssignment.assignment_date <= date,
                        (RoomAssignment.expected_check_out >= date) |
                        (RoomAssignment.actual_check_out.is_(None) |
                         (RoomAssignment.actual_check_out >= date))
                    )

                assignments = query.order_by(RoomAssignment.assignment_date).all()

                assignments_data = [
                    {
                        'assignment_id': assignment.id,
                        'room_id': assignment.room_id,
                        'stay_id': assignment.stay_id,
                        'guest_name': f"{assignment.stay.guest.first_name} {assignment.stay.guest.last_name}",
                        'assignment_date': assignment.assignment_date,
                        'expected_check_out': assignment.expected_check_out,
                        'actual_check_out': assignment.actual_check_out,
                        'assignment_type': assignment.assignment_type
                    }
                    for assignment in assignments
                ]

                return {
                    'success': True,
                    'assignments': assignments_data,
                    'count': len(assignments_data)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت تخصیص‌های اتاق: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'ROOM_ASSIGNMENTS_ERROR'
            }

    @staticmethod
    def transfer_room(stay_id: int, new_room_id: int,
                     reason: str, changed_by: int) -> Dict[str, Any]:
        """جابجایی مهمان به اتاق دیگر"""
        try:
            with db_session() as session:
                # دریافت تخصیص فعلی
                current_assignment = session.query(RoomAssignment).filter(
                    RoomAssignment.stay_id == stay_id,
                    RoomAssignment.actual_check_out.is_(None)
                ).first()

                if not current_assignment:
                    return {
                        'success': False,
                        'error': 'تخصیص اتاق فعال یافت نشد',
                        'error_code': 'ACTIVE_ASSIGNMENT_NOT_FOUND'
                    }

                # بستن تخصیص فعلی
                current_assignment.actual_check_out = date.today()

                # ایجاد تخصیص جدید
                new_assignment = RoomAssignment(
                    stay_id=stay_id,
                    room_id=new_room_id,
                    assignment_date=date.today(),
                    expected_check_out=current_assignment.expected_check_out,
                    assignment_type='transfer',
                    transfer_reason=reason
                )
                session.add(new_assignment)

                # ثبت تغییر وضعیت اتاق‌ها
                old_room_change = RoomStatusChange(
                    room_id=current_assignment.room_id,
                    previous_status='occupied',
                    new_status='cleaning',
                    status_reason='جابجایی مهمان',
                    changed_by=changed_by,
                    change_type='transfer'
                )
                session.add(old_room_change)

                new_room_change = RoomStatusChange(
                    room_id=new_room_id,
                    previous_status='vacant',
                    new_status='occupied',
                    status_reason='جابجایی مهمان',
                    changed_by=changed_by,
                    change_type='transfer'
                )
                session.add(new_room_change)

                session.commit()

                logger.info(f"✅ مهمان از اتاق {current_assignment.room_id} به اتاق {new_room_id} منتقل شد")

                return {
                    'success': True,
                    'stay_id': stay_id,
                    'old_room_id': current_assignment.room_id,
                    'new_room_id': new_room_id,
                    'message': 'جابجایی اتاق با موفقیت انجام شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در جابجایی اتاق: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'ROOM_TRANSFER_ERROR'
            }

    @staticmethod
    def create_daily_snapshot() -> Dict[str, Any]:
        """ایجاد اسنپ‌شوت روزانه از وضعیت اتاق‌ها"""
        try:
            with db_session() as session:
                from app.models.shared.hotel_models import HotelRoom

                # شمارش اتاق‌ها بر اساس وضعیت
                total_rooms = session.query(HotelRoom).filter(HotelRoom.is_active == True).count()

                # دریافت آخرین وضعیت هر اتاق
                room_statuses = RoomService._get_current_room_statuses(session)

                status_counts = {
                    'vacant': 0,
                    'occupied': 0,
                    'cleaning': 0,
                    'maintenance': 0,
                    'out_of_order': 0,
                    'inspection': 0
                }

                for status in room_statuses.values():
                    status_counts[status] = status_counts.get(status, 0) + 1

                # آمار مهمانان
                today = date.today()
                checked_in_guests = session.query(Stay).filter(
                    Stay.status == 'checked_in',
                    Stay.actual_check_in <= today,
                    Stay.actual_check_out.is_(None)
                ).count()

                expected_arrivals = session.query(Stay).filter(
                    Stay.status == 'confirmed',
                    Stay.planned_check_in.date() == today
                ).count()

                expected_departures = session.query(Stay).filter(
                    Stay.status == 'checked_in',
                    Stay.planned_check_out.date() == today
                ).count()

                # ایجاد اسنپ‌شوت
                snapshot = RoomStatusSnapshot(
                    snapshot_date=today,
                    snapshot_time=datetime.now(),
                    total_rooms=total_rooms,
                    vacant_rooms=status_counts['vacant'],
                    occupied_rooms=status_counts['occupied'],
                    cleaning_rooms=status_counts['cleaning'],
                    maintenance_rooms=status_counts['maintenance'],
                    out_of_order_rooms=status_counts['out_of_order'],
                    total_guests=checked_in_guests,
                    checked_in_guests=checked_in_guests,
                    expected_arrivals=expected_arrivals,
                    expected_departures=expected_departures
                )

                session.add(snapshot)
                session.commit()

                logger.info(f"✅ اسنپ‌شوت روزانه وضعیت اتاق‌ها ایجاد شد: {today}")

                return {
                    'success': True,
                    'snapshot_id': snapshot.id,
                    'snapshot_date': today,
                    'statistics': {
                        'total_rooms': total_rooms,
                        'vacant_rooms': status_counts['vacant'],
                        'occupied_rooms': status_counts['occupied'],
                        'cleaning_rooms': status_counts['cleaning'],
                        'maintenance_rooms': status_counts['maintenance'],
                        'checked_in_guests': checked_in_guests
                    }
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد اسنپ‌شوت روزانه: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SNAPSHOT_CREATION_ERROR'
            }

    # متدهای کمکی خصوصی
    @staticmethod
    def _get_single_room_status(session: Session, room_id: int) -> Dict[str, Any]:
        """دریافت وضعیت یک اتاق خاص"""
        from app.models.shared.hotel_models import HotelRoom

        room = session.query(HotelRoom).filter(HotelRoom.id == room_id).first()
        if not room:
            return None

        # آخرین وضعیت
        last_status = session.query(RoomStatusChange).filter(
            RoomStatusChange.room_id == room_id
        ).order_by(RoomStatusChange.created_at.desc()).first()

        current_status = last_status.new_status if last_status else 'vacant'

        # تخصیص فعلی
        current_assignment = session.query(RoomAssignment).filter(
            RoomAssignment.room_id == room_id,
            RoomAssignment.actual_check_out.is_(None)
        ).first()

        guest_info = None
        if current_assignment and current_assignment.stay:
            guest = current_assignment.stay.guest
            guest_info = {
                'guest_id': guest.id,
                'full_name': f"{guest.first_name} {guest.last_name}",
                'stay_id': current_assignment.stay_id
            }

        return {
            'room_id': room.id,
            'room_number': room.room_number,
            'room_type': room.room_type,
            'floor': room.floor,
            'current_status': current_status,
            'last_status_change': last_status.created_at if last_status else None,
            'current_guest': guest_info,
            'amenities': room.amenities or [],
            'is_active': room.is_active
        }

    @staticmethod
    def _get_all_rooms_status(session: Session) -> List[Dict[str, Any]]:
        """دریافت وضعیت تمام اتاق‌ها"""
        from app.models.shared.hotel_models import HotelRoom

        rooms = session.query(HotelRoom).filter(HotelRoom.is_active == True).all()
        rooms_status = []

        for room in rooms:
            room_status = RoomService._get_single_room_status(session, room.id)
            if room_status:
                rooms_status.append(room_status)

        return rooms_status

    @staticmethod
    def _get_current_room_statuses(session: Session) -> Dict[int, str]:
        """دریافت وضعیت فعلی تمام اتاق‌ها"""
        from app.models.shared.hotel_models import HotelRoom

        # subquery برای آخرین وضعیت هر اتاق
        latest_status_subquery = session.query(
            RoomStatusChange.room_id,
            RoomStatusChange.new_status,
            RoomStatusChange.created_at
        ).distinct(RoomStatusChange.room_id).order_by(
            RoomStatusChange.room_id,
            RoomStatusChange.created_at.desc()
        ).subquery()

        room_statuses = session.query(
            latest_status_subquery.c.room_id,
            latest_status_subquery.c.new_status
        ).all()

        return {room_id: status for room_id, status in room_statuses}
