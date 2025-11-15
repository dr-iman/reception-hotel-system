# app/services/reception/maintenance_service.py
"""
سرویس مدیریت تعمیرات و درخواست‌های تاسیسات
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func

from app.core.database import db_session
from app.models.reception.maintenance_models import MaintenanceRequest, MaintenanceStaff, MaintenanceWorkLog
from app.models.reception.room_status_models import RoomStatusChange
from app.models.shared.hotel_models import HotelRoom
from app.models.reception.staff_models import User
from config import config

logger = logging.getLogger(__name__)

class MaintenanceService:
    """سرویس مدیریت تعمیرات و تاسیسات"""

    @staticmethod
    def create_maintenance_request(room_id: int, issue_type: str, description: str,
                                 reported_by: int, priority: str = 'medium') -> Dict[str, Any]:
        """ایجاد درخواست تعمیرات جدید"""
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

                # بررسی کاربر گزارش دهنده
                reporter = session.query(User).filter(User.id == reported_by).first()
                if not reporter:
                    return {
                        'success': False,
                        'error': 'کاربر گزارش دهنده یافت نشد',
                        'error_code': 'USER_NOT_FOUND'
                    }

                # ایجاد درخواست تعمیرات
                request = MaintenanceRequest(
                    room_id=room_id,
                    issue_type=issue_type,
                    description=description,
                    reported_by=reported_by,
                    priority=priority,
                    status='pending'
                )

                session.add(request)
                session.flush()

                # ثبت تغییر وضعیت اتاق (در صورت نیاز)
                if priority in ['high', 'critical']:
                    status_change = RoomStatusChange(
                        room_id=room_id,
                        previous_status='vacant',  # یا وضعیت قبلی
                        new_status='maintenance',
                        status_reason=f'درخواست تعمیرات: {issue_type}',
                        changed_by=reported_by,
                        change_type='maintenance'
                    )
                    session.add(status_change)

                session.commit()

                logger.info(f"🔧 درخواست تعمیرات ایجاد شد: اتاق {room_id}, نوع {issue_type}")

                return {
                    'success': True,
                    'request_id': request.id,
                    'room_id': room_id,
                    'issue_type': issue_type,
                    'priority': priority,
                    'message': 'درخواست تعمیرات با موفقیت ایجاد شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد درخواست تعمیرات: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REQUEST_CREATION_ERROR'
            }

    @staticmethod
    def assign_request(request_id: int, technician_id: int, estimated_duration: int = None) -> Dict[str, Any]:
        """محول کردن درخواست به تکنسین"""
        try:
            with db_session() as session:
                request = session.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
                if not request:
                    return {
                        'success': False,
                        'error': 'درخواست یافت نشد',
                        'error_code': 'REQUEST_NOT_FOUND'
                    }

                technician = session.query(MaintenanceStaff).filter(MaintenanceStaff.id == technician_id).first()
                if not technician:
                    return {
                        'success': False,
                        'error': 'تکنسین یافت نشد',
                        'error_code': 'TECHNICIAN_NOT_FOUND'
                    }

                # به‌روزرسانی درخواست
                request.assigned_to = technician_id
                request.assigned_at = datetime.now()
                request.estimated_duration = estimated_duration
                request.status = 'assigned'

                session.commit()

                logger.info(f"👤 درخواست {request_id} به تکنسین {technician_id} محول شد")

                return {
                    'success': True,
                    'request_id': request_id,
                    'technician_id': technician_id,
                    'assigned_at': request.assigned_at,
                    'message': 'درخواست با موفقیت محول شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در محول کردن درخواست: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REQUEST_ASSIGNMENT_ERROR'
            }

    @staticmethod
    def start_work(request_id: int, actual_start_time: datetime = None) -> Dict[str, Any]:
        """شروع کار تعمیرات"""
        try:
            with db_session() as session:
                request = session.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
                if not request:
                    return {
                        'success': False,
                        'error': 'درخواست یافت نشد',
                        'error_code': 'REQUEST_NOT_FOUND'
                    }

                if request.status != 'assigned':
                    return {
                        'success': False,
                        'error': 'درخواست محول نشده است',
                        'error_code': 'REQUEST_NOT_ASSIGNED'
                    }

                # به‌روزرسانی درخواست
                request.actual_start = actual_start_time or datetime.now()
                request.status = 'in_progress'

                # ایجاد لاگ کار
                work_log = MaintenanceWorkLog(
                    request_id=request_id,
                    technician_id=request.assigned_to,
                    action='start_work',
                    description='شروع کار تعمیرات',
                    log_time=datetime.now()
                )
                session.add(work_log)

                session.commit()

                logger.info(f"⏱️ کار تعمیرات شروع شد: {request_id}")

                return {
                    'success': True,
                    'request_id': request_id,
                    'start_time': request.actual_start,
                    'message': 'کار تعمیرات شروع شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در شروع کار تعمیرات: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'WORK_START_ERROR'
            }

    @staticmethod
    def update_work_progress(request_id: int, progress_notes: str,
                           parts_used: str = None, additional_time: int = None) -> Dict[str, Any]:
        """به‌روزرسانی پیشرفت کار"""
        try:
            with db_session() as session:
                request = session.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
                if not request:
                    return {
                        'success': False,
                        'error': 'درخواست یافت نشد',
                        'error_code': 'REQUEST_NOT_FOUND'
                    }

                if request.status != 'in_progress':
                    return {
                        'success': False,
                        'error': 'کار در حال انجام نیست',
                        'error_code': 'WORK_NOT_IN_PROGRESS'
                    }

                # ایجاد لاگ پیشرفت
                work_log = MaintenanceWorkLog(
                    request_id=request_id,
                    technician_id=request.assigned_to,
                    action='progress_update',
                    description=progress_notes,
                    parts_used=parts_used,
                    additional_time_minutes=additional_time,
                    log_time=datetime.now()
                )
                session.add(work_log)

                # به‌روزرسانی زمان تخمینی در صورت نیاز
                if additional_time:
                    request.estimated_duration = (request.estimated_duration or 0) + additional_time

                session.commit()

                logger.info(f"📝 پیشرفت کار به‌روزرسانی شد: {request_id}")

                return {
                    'success': True,
                    'request_id': request_id,
                    'log_id': work_log.id,
                    'message': 'پیشرفت کار با موفقیت به‌روزرسانی شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی پیشرفت کار: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'PROGRESS_UPDATE_ERROR'
            }

    @staticmethod
    def complete_work(request_id: int, work_notes: str = None,
                     parts_cost: Decimal = None, completion_time: datetime = None) -> Dict[str, Any]:
        """اتمام کار تعمیرات"""
        try:
            with db_session() as session:
                request = session.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
                if not request:
                    return {
                        'success': False,
                        'error': 'درخواست یافت نشد',
                        'error_code': 'REQUEST_NOT_FOUND'
                    }

                if request.status != 'in_progress':
                    return {
                        'success': False,
                        'error': 'کار در حال انجام نیست',
                        'error_code': 'WORK_NOT_IN_PROGRESS'
                    }

                # به‌روزرسانی درخواست
                request.completed_at = completion_time or datetime.now()
                request.work_notes = work_notes
                request.parts_cost = parts_cost
                request.status = 'completed'

                # محاسبه زمان انجام کار
                if request.actual_start and request.completed_at:
                    request.actual_duration = (request.completed_at - request.actual_start).total_seconds() / 60  # دقیقه

                # ایجاد لاگ اتمام کار
                work_log = MaintenanceWorkLog(
                    request_id=request_id,
                    technician_id=request.assigned_to,
                    action='complete_work',
                    description='اتمام کار تعمیرات',
                    log_time=datetime.now()
                )
                session.add(work_log)

                session.commit()

                logger.info(f"✅ کار تعمیرات تکمیل شد: {request_id}")

                return {
                    'success': True,
                    'request_id': request_id,
                    'completion_time': request.completed_at,
                    'actual_duration': request.actual_duration,
                    'message': 'کار تعمیرات با موفقیت تکمیل شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در اتمام کار تعمیرات: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'WORK_COMPLETION_ERROR'
            }

    @staticmethod
    def verify_work(request_id: int, verifier_id: int, verification_notes: str = None) -> Dict[str, Any]:
        """تأیید کیفیت کار تعمیرات"""
        try:
            with db_session() as session:
                request = session.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
                if not request:
                    return {
                        'success': False,
                        'error': 'درخواست یافت نشد',
                        'error_code': 'REQUEST_NOT_FOUND'
                    }

                if request.status != 'completed':
                    return {
                        'success': False,
                        'error': 'کار تکمیل نشده است',
                        'error_code': 'WORK_NOT_COMPLETED'
                    }

                # به‌روزرسانی درخواست
                request.verified_by = verifier_id
                request.verified_at = datetime.now()
                request.verification_notes = verification_notes
                request.status = 'verified'

                # به‌روزرسانی وضعیت اتاق
                status_change = RoomStatusChange(
                    room_id=request.room_id,
                    previous_status='maintenance',
                    new_status='vacant',
                    status_reason='تأیید کیفیت تعمیرات',
                    changed_by=verifier_id,
                    change_type='maintenance'
                )
                session.add(status_change)

                session.commit()

                logger.info(f"🔍 کیفیت کار تعمیرات تأیید شد: {request_id}")

                return {
                    'success': True,
                    'request_id': request_id,
                    'verified_at': request.verified_at,
                    'message': 'کیفیت کار با موفقیت تأیید شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در تأیید کیفیت کار: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'WORK_VERIFICATION_ERROR'
            }

    @staticmethod
    def get_maintenance_requests(status: str = None, technician_id: int = None,
                               priority: str = None) -> Dict[str, Any]:
        """دریافت لیست درخواست‌های تعمیرات"""
        try:
            with db_session() as session:
                query = session.query(MaintenanceRequest).options(
                    joinedload(MaintenanceRequest.room),
                    joinedload(MaintenanceRequest.technician),
                    joinedload(MaintenanceRequest.reporter)
                )

                # فیلترها
                if status:
                    query = query.filter(MaintenanceRequest.status == status)

                if technician_id:
                    query = query.filter(MaintenanceRequest.assigned_to == technician_id)

                if priority:
                    query = query.filter(MaintenanceRequest.priority == priority)

                requests = query.order_by(
                    MaintenanceRequest.priority.desc(),
                    MaintenanceRequest.created_at.asc()
                ).all()

                requests_data = [
                    {
                        'request_id': req.id,
                        'room_id': req.room_id,
                        'room_number': req.room.room_number if req.room else 'نامشخص',
                        'issue_type': req.issue_type,
                        'description': req.description,
                        'status': req.status,
                        'priority': req.priority,
                        'reported_by': req.reported_by,
                        'reporter_name': f"{req.reporter.first_name} {req.reporter.last_name}" if req.reporter else 'نامشخص',
                        'assigned_to': req.assigned_to,
                        'technician_name': f"{req.technician.first_name} {req.technician.last_name}" if req.technician else 'محول نشده',
                        'created_at': req.created_at,
                        'assigned_at': req.assigned_at,
                        'completed_at': req.completed_at
                    }
                    for req in requests
                ]

                return {
                    'success': True,
                    'requests': requests_data,
                    'count': len(requests_data)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست درخواست‌ها: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REQUESTS_RETRIEVAL_ERROR'
            }

    @staticmethod
    def get_maintenance_technicians() -> Dict[str, Any]:
        """دریافت لیست تکنسین‌های تعمیرات"""
        try:
            with db_session() as session:
                technicians = session.query(MaintenanceStaff).filter(
                    MaintenanceStaff.is_active == True
                ).all()

                technicians_data = [
                    {
                        'technician_id': t.id,
                        'first_name': t.first_name,
                        'last_name': t.last_name,
                        'phone': t.phone,
                        'specialization': t.specialization,
                        'is_active': t.is_active,
                        'current_requests': session.query(MaintenanceRequest).filter(
                            MaintenanceRequest.assigned_to == t.id,
                            MaintenanceRequest.status.in_(['assigned', 'in_progress'])
                        ).count()
                    }
                    for t in technicians
                ]

                return {
                    'success': True,
                    'technicians': technicians_data,
                    'count': len(technicians_data)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت لیست تکنسین‌ها: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'TECHNICIANS_RETRIEVAL_ERROR'
            }

    @staticmethod
    def get_work_logs(request_id: int) -> Dict[str, Any]:
        """دریافت لاگ‌های کار برای یک درخواست"""
        try:
            with db_session() as session:
                logs = session.query(MaintenanceWorkLog).options(
                    joinedload(MaintenanceWorkLog.technician)
                ).filter(
                    MaintenanceWorkLog.request_id == request_id
                ).order_by(MaintenanceWorkLog.log_time.asc()).all()

                logs_data = [
                    {
                        'log_id': log.id,
                        'action': log.action,
                        'description': log.description,
                        'parts_used': log.parts_used,
                        'additional_time': log.additional_time_minutes,
                        'technician_name': f"{log.technician.first_name} {log.technician.last_name}" if log.technician else 'سیستم',
                        'log_time': log.log_time
                    }
                    for log in logs
                ]

                return {
                    'success': True,
                    'logs': logs_data,
                    'count': len(logs_data)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت لاگ‌های کار: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'WORK_LOGS_RETRIEVAL_ERROR'
            }

    @staticmethod
    def get_maintenance_metrics(start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """دریافت معیارهای عملکرد تعمیرات"""
        try:
            with db_session() as session:
                if not start_date:
                    start_date = date.today() - timedelta(days=30)
                if not end_date:
                    end_date = date.today()

                requests = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.created_at >= start_date,
                    MaintenanceRequest.created_at <= end_date
                ).all()

                completed_requests = [r for r in requests if r.status == 'verified']
                total_requests = len(requests)

                if total_requests == 0:
                    return {
                        'success': True,
                        'metrics': {
                            'total_requests': 0,
                            'completed_requests': 0,
                            'completion_rate': 0,
                            'average_duration': 0,
                            'total_parts_cost': 0
                        }
                    }

                # محاسبه معیارها
                completion_rate = len(completed_requests) / total_requests * 100

                durations = [r.actual_duration for r in completed_requests if r.actual_duration]
                average_duration = sum(durations) / len(durations) if durations else 0

                parts_costs = [r.parts_cost for r in completed_requests if r.parts_cost]
                total_parts_cost = sum(parts_costs) if parts_costs else Decimal('0')

                # توزیع بر اساس نوع مشکل
                issue_types = {}
                for req in requests:
                    issue_types[req.issue_type] = issue_types.get(req.issue_type, 0) + 1

                metrics = {
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'total_requests': total_requests,
                    'completed_requests': len(completed_requests),
                    'completion_rate': round(completion_rate, 2),
                    'average_duration': round(average_duration, 2),
                    'total_parts_cost': float(total_parts_cost),
                    'issue_type_distribution': issue_types
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
                'error_code': 'MAINTENANCE_METRICS_ERROR'
            }
