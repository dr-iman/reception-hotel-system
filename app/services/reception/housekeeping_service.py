# app/services/reception/housekeeping_service.py
"""
سرویس مدیریت خانه‌داری و نظافت اتاق‌ها
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.core.database import db_session
from app.models.reception.housekeeping_models import HousekeepingTask, HousekeepingStaff, QualityInspection
from app.models.reception.room_status_models import RoomStatusChange
from app.models.shared.hotel_models import HotelRoom
from app.models.reception.guest_models import Stay
from config import config

logger = logging.getLogger(__name__)

class HousekeepingService:
    """سرویس مدیریت خانه‌داری و نظافت"""

    @staticmethod
    def create_cleaning_task(room_id: int, task_type: str, scheduled_time: datetime = None,
                           priority: str = 'medium', assigned_to: int = None) -> Dict[str, Any]:
        """ایجاد وظیفه نظافت جدید"""
        try:
            with db_session() as session:
                # بررسی وجود اتاق
                room = session.query(HotelRoom).filter(HotelRoom.id == room_id).first()
                if not room:
                    return {
                        'success': False,
                        'error': 'اتاق یافت نشد',
                        'error_code': 'ROOM_NOT_FOUND'
                    }

                # ایجاد وظیفه نظافت
                task = HousekeepingTask(
                    room_id=room_id,
                    task_type=task_type,
                    scheduled_time=scheduled_time or datetime.now(),
                    priority=priority,
                    status='pending',
                    assigned_to=assigned_to
                )

                session.add(task)
                session.flush()

                # ثبت تغییر وضعیت اتاق
                status_change = RoomStatusChange(
                    room_id=room_id,
                    previous_status='vacant',  # یا وضعیت قبلی
                    new_status='cleaning',
                    status_reason=f'وظیفه نظافت: {task_type}',
                    changed_by=0,  # سیستم
                    change_type='housekeeping'
                )
                session.add(status_change)

                session.commit()

                logger.info(f"🧹 وظیفه نظافت ایجاد شد: اتاق {room_id}, نوع {task_type}")

                return {
                    'success': True,
                    'task_id': task.id,
                    'room_id': room_id,
                    'task_type': task_type,
                    'scheduled_time': task.scheduled_time,
                    'message': 'وظیفه نظافت با موفقیت ایجاد شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد وظیفه نظافت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'TASK_CREATION_ERROR'
            }

    @staticmethod
    def assign_task(task_id: int, staff_id: int) -> Dict[str, Any]:
        """محول کردن وظیفه به کارمند خانه‌داری"""
        try:
            with db_session() as session:
                task = session.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد',
                        'error_code': 'TASK_NOT_FOUND'
                    }

                staff = session.query(HousekeepingStaff).filter(HousekeepingStaff.id == staff_id).first()
                if not staff:
                    return {
                        'success': False,
                        'error': 'کارمند خانه‌داری یافت نشد',
                        'error_code': 'STAFF_NOT_FOUND'
                    }

                # به‌روزرسانی وظیفه
                task.assigned_to = staff_id
                task.assigned_at = datetime.now()
                task.status = 'assigned'

                session.commit()

                logger.info(f"👤 وظیفه {task_id} به کارمند {staff_id} محول شد")

                return {
                    'success': True,
                    'task_id': task_id,
                    'staff_id': staff_id,
                    'assigned_at': task.assigned_at,
                    'message': 'وظیفه با موفقیت محول شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در محول کردن وظیفه: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'TASK_ASSIGNMENT_ERROR'
            }

    @staticmethod
    def start_task(task_id: int, actual_start_time: datetime = None) -> Dict[str, Any]:
        """شروع کار نظافت"""
        try:
            with db_session() as session:
                task = session.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد',
                        'error_code': 'TASK_NOT_FOUND'
                    }

                if task.status not in ['assigned', 'pending']:
                    return {
                        'success': False,
                        'error': 'وضعیت وظیفه برای شروع کار نامناسب است',
                        'error_code': 'INVALID_TASK_STATUS'
                    }

                # به‌روزرسانی وظیفه
                task.actual_start = actual_start_time or datetime.now()
                task.status = 'in_progress'

                session.commit()

                logger.info(f"⏱️ وظیفه نظافت شروع شد: {task_id}")

                return {
                    'success': True,
                    'task_id': task_id,
                    'start_time': task.actual_start,
                    'message': 'کار نظافت شروع شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در شروع کار نظافت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'TASK_START_ERROR'
            }

    @staticmethod
    def complete_task(task_id: int, notes: str = None, completion_time: datetime = None) -> Dict[str, Any]:
        """اتمام کار نظافت"""
        try:
            with db_session() as session:
                task = session.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد',
                        'error_code': 'TASK_NOT_FOUND'
                    }

                if task.status != 'in_progress':
                    return {
                        'success': False,
                        'error': 'وظیفه در حال انجام نیست',
                        'error_code': 'TASK_NOT_IN_PROGRESS'
                    }

                # به‌روزرسانی وظیفه
                task.completed_at = completion_time or datetime.now()
                task.status = 'completed'
                task.notes = notes

                # محاسبه زمان انجام کار
                if task.actual_start and task.completed_at:
                    task.actual_duration = (task.completed_at - task.actual_start).total_seconds() / 60  # دقیقه

                # به‌روزرسانی وضعیت اتاق
                status_change = RoomStatusChange(
                    room_id=task.room_id,
                    previous_status='cleaning',
                    new_status='inspection',
                    status_reason='اتمام نظافت - نیاز به بازرسی',
                    changed_by=0,  # سیستم
                    change_type='housekeeping'
                )
                session.add(status_change)

                session.commit()

                logger.info(f"✅ وظیفه نظافت تکمیل شد: {task_id}")

                return {
                    'success': True,
                    'task_id': task_id,
                    'completion_time': task.completed_at,
                    'actual_duration': task.actual_duration,
                    'message': 'کار نظافت با موفقیت تکمیل شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در اتمام کار نظافت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'TASK_COMPLETION_ERROR'
            }

    @staticmethod
    def verify_task(task_id: int, inspector_id: int, quality_rating: int,
                   inspection_notes: str = None) -> Dict[str, Any]:
        """تأیید کیفیت کار نظافت"""
        try:
            with db_session() as session:
                task = session.query(HousekeepingTask).filter(HousekeepingTask.id == task_id).first()
                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد',
                        'error_code': 'TASK_NOT_FOUND'
                    }

                if task.status != 'completed':
                    return {
                        'success': False,
                        'error': 'وظیفه تکمیل نشده است',
                        'error_code': 'TASK_NOT_COMPLETED'
                    }

                # ایجاد رکورد بازرسی کیفیت
                inspection = QualityInspection(
                    task_id=task_id,
                    inspector_id=inspector_id,
                    quality_rating=quality_rating,
                    inspection_notes=inspection_notes,
                    inspection_date=datetime.now()
                )
                session.add(inspection)

                # به‌روزرسانی وظیفه
                task.quality_rating = quality_rating
                task.verified_by = inspector_id
                task.verified_at = datetime.now()
                task.status = 'verified'

                # به‌روزرسانی وضعیت اتاق
                status_change = RoomStatusChange(
                    room_id=task.room_id,
                    previous_status='inspection',
                    new_status='vacant',
                    status_reason='تأیید کیفیت نظافت',
                    changed_by=inspector_id,
                    change_type='inspection'
                )
                session.add(status_change)

                session.commit()

                logger.info(f"🔍 کیفیت وظیفه {task_id} تأیید شد: امتیاز {quality_rating}")

                return {
                    'success': True,
                    'task_id': task_id,
                    'inspection_id': inspection.id,
                    'quality_rating': quality_rating,
                    'message': 'کیفیت کار با موفقیت تأیید شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در تأیید کیفیت کار: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'QUALITY_VERIFICATION_ERROR'
            }

    @staticmethod
    def get_tasks(status: str = None, staff_id: int = None, date: date = None) -> Dict[str, Any]:
        """دریافت لیست وظایف خانه‌داری"""
        try:
            with db_session() as session:
                query = session.query(HousekeepingTask).options(
                    joinedload(HousekeepingTask.room),
                    joinedload(HousekeepingTask.staff)
                )

                # فیلترها
                if status:
                    query = query.filter(HousekeepingTask.status == status)

                if staff_id:
                    query = query.filter(HousekeepingTask.assigned_to == staff_id)

                if date:
                    query = query.filter(func.date(HousekeepingTask.scheduled_time) == date)

                tasks = query.order_by(
                    HousekeepingTask.priority.desc(),
                    HousekeepingTask.scheduled_time.asc()
                ).all()

                tasks_data = [
                    {
                        'task_id': task.id,
                        'room_id': task.room_id,
                        'room_number': task.room.room_number if task.room else 'نامشخص',
                        'task_type': task.task_type,
                        'status': task.status,
                        'priority': task.priority,
                        'scheduled_time': task.scheduled_time,
                        'assigned_to': task.assigned_to,
                        'staff_name': f"{task.staff.first_name} {task.staff.last_name}" if task.staff else 'محول نشده',
                        'actual_start': task.actual_start,
                        'completed_at': task.completed_at,
                        'quality_rating': task.quality_rating
                    }
                    for task in tasks
                ]

                return {
                    'success': True,
                    'tasks': tasks_data,
                    'count': len(tasks_data)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست وظایف: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'TASKS_RETRIEVAL_ERROR'
            }

    @staticmethod
    def get_housekeeping_staff() -> Dict[str, Any]:
        """دریافت لیست کارکنان خانه‌داری"""
        try:
            with db_session() as session:
                staff = session.query(HousekeepingStaff).filter(
                    HousekeepingStaff.is_active == True
                ).all()

                staff_data = [
                    {
                        'staff_id': s.id,
                        'first_name': s.first_name,
                        'last_name': s.last_name,
                        'phone': s.phone,
                        'specialization': s.specialization,
                        'is_active': s.is_active,
                        'current_tasks': session.query(HousekeepingTask).filter(
                            HousekeepingTask.assigned_to == s.id,
                            HousekeepingTask.status.in_(['assigned', 'in_progress'])
                        ).count()
                    }
                    for s in staff
                ]

                return {
                    'success': True,
                    'staff': staff_data,
                    'count': len(staff_data)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست کارکنان: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'STAFF_RETRIEVAL_ERROR'
            }

    @staticmethod
    def get_cleaning_schedule(date: date = None) -> Dict[str, Any]:
        """دریافت برنامه نظافت برای تاریخ مشخص"""
        try:
            with db_session() as session:
                target_date = date or date.today()

                # اتاق‌های خروجی امروز
                checkout_rooms = session.query(RoomAssignment.room_id).filter(
                    RoomAssignment.actual_check_out == target_date
                ).subquery()

                # اتاق‌های موجود برای نظافت
                available_rooms = session.query(HotelRoom).filter(
                    HotelRoom.is_active == True,
                    HotelRoom.id.notin_(
                        session.query(RoomAssignment.room_id).filter(
                            RoomAssignment.actual_check_out.is_(None)
                        )
                    )
                ).all()

                # وظایف برنامه‌ریزی شده برای امروز
                scheduled_tasks = session.query(HousekeepingTask).filter(
                    func.date(HousekeepingTask.scheduled_time) == target_date
                ).all()

                schedule_data = {
                    'date': target_date,
                    'available_rooms': [
                        {
                            'room_id': room.id,
                            'room_number': room.room_number,
                            'room_type': room.room_type,
                            'floor': room.floor
                        }
                        for room in available_rooms
                    ],
                    'scheduled_tasks': [
                        {
                            'task_id': task.id,
                            'room_number': task.room.room_number if task.room else 'نامشخص',
                            'task_type': task.task_type,
                            'status': task.status,
                            'assigned_staff': f"{task.staff.first_name} {task.staff.last_name}" if task.staff else None
                        }
                        for task in scheduled_tasks
                    ],
                    'checkout_rooms': [
                        {
                            'room_id': room_id,
                            'room_number': session.query(HotelRoom.room_number).filter(HotelRoom.id == room_id).scalar()
                        }
                        for room_id in session.query(checkout_rooms.c.room_id).all()
                    ]
                }

                return {
                    'success': True,
                    'schedule': schedule_data
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت برنامه نظافت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SCHEDULE_RETRIEVAL_ERROR'
            }

    @staticmethod
    def get_performance_metrics(staff_id: int = None, start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """دریافت معیارهای عملکرد خانه‌داری"""
        try:
            with db_session() as session:
                if not start_date:
                    start_date = date.today() - timedelta(days=30)
                if not end_date:
                    end_date = date.today()

                query = session.query(HousekeepingTask)

                if staff_id:
                    query = query.filter(HousekeepingTask.assigned_to == staff_id)

                tasks = query.filter(
                    HousekeepingTask.scheduled_time >= start_date,
                    HousekeepingTask.scheduled_time <= end_date
                ).all()

                completed_tasks = [t for t in tasks if t.status == 'verified']
                total_tasks = len(tasks)

                if total_tasks == 0:
                    return {
                        'success': True,
                        'metrics': {
                            'total_tasks': 0,
                            'completed_tasks': 0,
                            'completion_rate': 0,
                            'average_quality': 0,
                            'average_duration': 0
                        }
                    }

                # محاسبه معیارها
                completion_rate = len(completed_tasks) / total_tasks * 100

                quality_ratings = [t.quality_rating for t in completed_tasks if t.quality_rating]
                average_quality = sum(quality_ratings) / len(quality_ratings) if quality_ratings else 0

                durations = [t.actual_duration for t in completed_tasks if t.actual_duration]
                average_duration = sum(durations) / len(durations) if durations else 0

                metrics = {
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'total_tasks': total_tasks,
                    'completed_tasks': len(completed_tasks),
                    'completion_rate': round(completion_rate, 2),
                    'average_quality': round(average_quality, 2),
                    'average_duration': round(average_duration, 2)
                }

                return {
                    'success': True,
                    'metrics': metrics
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت معیارهای عملکرد: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'PERFORMANCE_METRICS_ERROR'
            }
