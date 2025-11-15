# app/core/housekeeping_manager.py
"""
مدیریت پیشرفته خانه‌داری و نظافت هتل
"""

import logging
import threading
from datetime import datetime, timedelta, time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from app.core.database import db_session, get_redis
from config import config

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"

@dataclass
class CleaningChecklist:
    """چک‌لیست نظافت استاندارد"""
    bathroom_items: List[str]
    bedroom_items: List[str]
    amenities_items: List[str]
    common_area_items: List[str]

class HousekeepingManager:
    """مدیریت هوشمند خانه‌داری"""

    def __init__(self):
        self.redis = get_redis()
        self.auto_scheduling = config.housekeeping.auto_cleaning_schedule
        self.check_out_time = self._parse_time(config.housekeeping.check_out_time)
        self.cleaning_timeout = config.housekeeping.cleaning_timeout

        # چک‌لیست‌های استاندارد
        self.standard_checklists = {
            'checkout_cleaning': CleaningChecklist(
                bathroom_items=[
                    "تمیز کردن وان/دوش",
                    "شستشوی توالت",
                    "تمیز کردن سینک",
                    "تعویض حوله‌ها",
                    "پر کردن شامپو و صابون",
                    "تمیز کردن آینه",
                    "شستشوی کف"
                ],
                bedroom_items=[
                    "تعویض ملافه‌ها",
                    "تمیز کردن تخت",
                    "گردگیری مبلمان",
                    "تمیز کردن میزها",
                    "خالی کردن سطل زباله",
                    "تمیز کردن پنجره‌ها",
                    "جارو برقی فرش",
                    "شستشوی کف"
                ],
                amenities_items=[
                    "پر کردن مینی‌بار",
                    "بررسی چای/قهوه",
                    "تعویض لوازم بهداشتی",
                    "بررسی تلویزیون",
                    "بررسی اینترنت"
                ],
                common_area_items=[]
            ),
            'stayover_cleaning': CleaningChecklist(
                bathroom_items=[
                    "تمیز کردن سینک",
                    "شستشوی توالت",
                    "خالی کردن سطل زباله",
                    "تعویض حوله‌ها",
                    "پر کردن شامپو و صابون"
                ],
                bedroom_items=[
                    "تمیز کردن تخت",
                    "خالی کردن سطل زباله",
                    "گردگیری سطوح",
                    "جارو برقی فرش"
                ],
                amenities_items=[
                    "پر کردن مینی‌بار",
                    "بررسی چای/قهوه"
                ],
                common_area_items=[]
            ),
            'deep_cleaning': CleaningChecklist(
                bathroom_items=[
                    "تمیز کردن کامل وان/دوش",
                    "شستشوی عمقی توالت",
                    "تمیز کردن سینک و شیرآلات",
                    "تمیز کردن کاشی‌ها",
                    "شستشوی پرده حمام",
                    "تمیز کردن هواکش"
                ],
                bedroom_items=[
                    "شستشوی فرش",
                    "گردگیری کامل دیوارها",
                    "تمیز کردن پنجره‌ها و چارچوب",
                    "شستشوی پرده‌ها",
                    "تمیز کردن کمدها",
                    "گردگیری چراغ‌ها"
                ],
                amenities_items=[
                    "تمیز کردن یخچال",
                    "شستشوی سماور",
                    "تمیز کردن گاوصندوق"
                ],
                common_area_items=[]
            )
        }

        # شروع مانیتورینگ خودکار
        if self.auto_scheduling:
            self._start_auto_monitoring()

    def _parse_time(self, time_str: str) -> time:
        """تبدیل رشته زمان به object زمان"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return time(hour, minute)
        except:
            return time(12, 0)  # پیش‌فرض ساعت 12

    def _start_auto_monitoring(self):
        """شروع مانیتورینگ خودکار خانه‌داری"""
        self.monitor_thread = threading.Thread(target=self._auto_monitor_worker, daemon=True)
        self.monitor_thread.start()
        logger.info("🚀 مانیتورینگ خودکار خانه‌داری شروع شد")

    def _auto_monitor_worker(self):
        """کارگر مانیتورینگ خودکار"""
        while True:
            try:
                # بررسی خروج‌های امروز
                self._schedule_checkout_cleanings()

                # بررسی اتاق‌های نیازمند نظافت
                self._check_cleaning_timeouts()

                # ایجاد گزارش روزانه
                self._generate_daily_housekeeping_report()

                # خواب به مدت 5 دقیقه
                threading.Event().wait(300)

            except Exception as e:
                logger.error(f"❌ خطا در مانیتورینگ خودکار خانه‌داری: {e}")
                threading.Event().wait(60)  # خواب کوتاه در صورت خطا

    def _schedule_checkout_cleanings(self):
        """برنامه‌ریزی نظافت‌های پس از خروج"""
        try:
            from app.models.reception.room_status_models import RoomAssignment
            from app.models.reception.housekeeping_models import HousekeepingTask

            today = datetime.now().date()

            with db_session() as session:
                # یافتن اتاق‌هایی که امروز مهمانشان خارج شده است
                checkout_rooms = session.query(RoomAssignment).filter(
                    RoomAssignment.actual_check_out == today,
                    RoomAssignment.assignment_type == 'primary'
                ).all()

                for assignment in checkout_rooms:
                    # بررسی وجود وظیفه قبلی
                    existing_task = session.query(HousekeepingTask).filter(
                        HousekeepingTask.room_id == assignment.room_id,
                        HousekeepingTask.task_type == 'checkout_cleaning',
                        HousekeepingTask.status.in_(['pending', 'assigned', 'in_progress'])
                    ).first()

                    if not existing_task:
                        # ایجاد وظیفه نظافت جدید
                        scheduled_time = datetime.now() + timedelta(minutes=30)

                        task = HousekeepingTask(
                            room_id=assignment.room_id,
                            task_type='checkout_cleaning',
                            priority=TaskPriority.HIGH.value,
                            status=TaskStatus.PENDING.value,
                            scheduled_time=scheduled_time,
                            required_supplies=self._get_required_supplies('checkout_cleaning'),
                            special_equipment=['جارو برقی', 'سطل نظافت']
                        )

                        session.add(task)

                        # ایجاد آیتم‌های چک‌لیست
                        self._create_checklist_items(task, 'checkout_cleaning')

                        logger.info(f"🧹 وظیفه نظافت خروج برای اتاق {assignment.room_id} ایجاد شد")

                session.commit()

        except Exception as e:
            logger.error(f"❌ خطا در برنامه‌ریزی نظافت‌های خروج: {e}")

    def _check_cleaning_timeouts(self):
        """بررسی timeout وظایف نظافت"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            timeout_threshold = datetime.now() - timedelta(minutes=self.cleaning_timeout)

            with db_session() as session:
                # یافتن وظایفی که زمان‌شان گذشته است
                overdue_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.status.in_(['assigned', 'in_progress']),
                    HousekeepingTask.scheduled_time < timeout_threshold
                ).all()

                for task in overdue_tasks:
                    # ارسال هشدار
                    self._send_cleaning_alert(task)
                    logger.warning(f"⚠️ وظیفه نظافت اتاق {task.room_id} overdue شده است")

        except Exception as e:
            logger.error(f"❌ خطا در بررسی timeout نظافت: {e}")

    def _send_cleaning_alert(self, task):
        """ارسال هشدار نظافت"""
        try:
            from app.core.notification_service import notification_service

            message = f"وظیفه نظافت اتاق {task.room_id} overdue شده است. لطفاً پیگیری کنید."

            notification_service.send_to_department(
                department='housekeeping',
                title='هشدار تأخیر نظافت',
                message=message,
                notification_type='warning'
            )

        except Exception as e:
            logger.error(f"❌ خطا در ارسال هشدار نظافت: {e}")

    def create_cleaning_task(self, room_id: int, task_type: str,
                           scheduled_time: datetime, priority: str = 'normal',
                           assigned_to: Optional[int] = None) -> Dict[str, Any]:
        """ایجاد وظیفه نظافت جدید"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            with db_session() as session:
                task = HousekeepingTask(
                    room_id=room_id,
                    task_type=task_type,
                    priority=priority,
                    status=TaskStatus.PENDING.value if not assigned_to else TaskStatus.ASSIGNED.value,
                    scheduled_time=scheduled_time,
                    assigned_to=assigned_to,
                    required_supplies=self._get_required_supplies(task_type),
                    special_equipment=self._get_special_equipment(task_type)
                )

                session.add(task)
                session.commit()

                # ایجاد آیتم‌های چک‌لیست
                self._create_checklist_items(task, task_type)

                logger.info(f"✅ وظیفه نظافت {task_type} برای اتاق {room_id} ایجاد شد")

                return {
                    'success': True,
                    'task_id': task.id,
                    'message': 'وظیفه نظافت ایجاد شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد وظیفه نظافت: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def assign_task(self, task_id: int, staff_id: int) -> Dict[str, Any]:
        """محول کردن وظیفه به کارمند"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            with db_session() as session:
                task = session.query(HousekeepingTask).filter(
                    HousekeepingTask.id == task_id
                ).first()

                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد'
                    }

                task.assigned_to = staff_id
                task.status = TaskStatus.ASSIGNED.value
                session.commit()

                logger.info(f"👤 وظیفه {task_id} به کارمند {staff_id} محول شد")

                return {
                    'success': True,
                    'message': 'وظیفه محول شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در محول کردن وظیفه: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def start_task(self, task_id: int, staff_id: int) -> Dict[str, Any]:
        """شروع انجام وظیفه"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            with db_session() as session:
                task = session.query(HousekeepingTask).filter(
                    HousekeepingTask.id == task_id,
                    HousekeepingTask.assigned_to == staff_id
                ).first()

                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد یا به شما محول نشده است'
                    }

                task.status = TaskStatus.IN_PROGRESS.value
                task.started_at = datetime.now()
                session.commit()

                logger.info(f"▶️ وظیفه {task_id} شروع شد")

                return {
                    'success': True,
                    'message': 'وظیفه شروع شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در شروع وظیفه: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def complete_task(self, task_id: int, staff_id: int,
                     cleaning_notes: str = None) -> Dict[str, Any]:
        """اتمام وظیفه نظافت"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            with db_session() as session:
                task = session.query(HousekeepingTask).filter(
                    HousekeepingTask.id == task_id,
                    HousekeepingTask.assigned_to == staff_id
                ).first()

                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد'
                    }

                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.now()
                task.cleaning_notes = cleaning_notes
                session.commit()

                # به‌روزرسانی وضعیت اتاق
                self._update_room_status(task.room_id, 'cleaning_completed')

                logger.info(f"✅ وظیفه {task_id} تکمیل شد")

                return {
                    'success': True,
                    'message': 'وظیفه تکمیل شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در اتمام وظیفه: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def verify_task(self, task_id: int, inspector_id: int,
                   quality_score: int, inspection_notes: str = None) -> Dict[str, Any]:
        """تأیید کیفیت نظافت"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            with db_session() as session:
                task = session.query(HousekeepingTask).filter(
                    HousekeepingTask.id == task_id,
                    HousekeepingTask.status == TaskStatus.COMPLETED.value
                ).first()

                if not task:
                    return {
                        'success': False,
                        'error': 'وظیفه یافت نشد یا هنوز تکمیل نشده است'
                    }

                task.status = TaskStatus.VERIFIED.value
                task.verified_at = datetime.now()
                task.quality_score = quality_score
                task.inspection_notes = inspection_notes
                session.commit()

                # به‌روزرسانی وضعیت اتاق به "آماده"
                self._update_room_status(task.room_id, 'ready')

                logger.info(f"🔍 وظیفه {task_id} تأیید شد - امتیاز: {quality_score}")

                return {
                    'success': True,
                    'message': 'وظیفه تأیید شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در تأیید وظیفه: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_checklist_items(self, task, task_type: str):
        """ایجاد آیتم‌های چک‌لیست برای وظیفه"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingChecklist

            checklist = self.standard_checklists.get(task_type)
            if not checklist:
                return

            with db_session() as session:
                # آیتم‌های حمام
                for item in checklist.bathroom_items:
                    checklist_item = HousekeepingChecklist(
                        task_id=task.id,
                        item_name=item,
                        category='bathroom',
                        status='pending'
                    )
                    session.add(checklist_item)

                # آیتم‌های اتاق خواب
                for item in checklist.bedroom_items:
                    checklist_item = HousekeepingChecklist(
                        task_id=task.id,
                        item_name=item,
                        category='bedroom',
                        status='pending'
                    )
                    session.add(checklist_item)

                # آیتم‌های امکانات
                for item in checklist.amenities_items:
                    checklist_item = HousekeepingChecklist(
                        task_id=task.id,
                        item_name=item,
                        category='amenities',
                        status='pending'
                    )
                    session.add(checklist_item)

                session.commit()

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد آیتم‌های چک‌لیست: {e}")

    def _get_required_supplies(self, task_type: str) -> List[str]:
        """دریافت مواد مصرفی مورد نیاز برای نوع وظیفه"""
        supplies = {
            'checkout_cleaning': ['ملافه تمیز', 'روتختی', 'حوله', 'شامپو', 'صابون', 'دستمال توالت'],
            'stayover_cleaning': ['حوله', 'شامپو', 'صابون', 'دستمال توالت'],
            'deep_cleaning': ['ملافه تمیز', 'روتختی', 'حوله', 'شامپو', 'صابون', 'دستمال توالت', 'مواد شوینده قوی'],
            'inspection': []
        }
        return supplies.get(task_type, [])

    def _get_special_equipment(self, task_type: str) -> List[str]:
        """دریافت تجهیزات ویژه مورد نیاز"""
        equipment = {
            'checkout_cleaning': ['جارو برقی', 'سطل نظافت'],
            'deep_cleaning': ['جارو برقی', 'بخارشو', 'نردبان'],
            'inspection': ['چک‌لیست', 'قلم']
        }
        return equipment.get(task_type, [])

    def _update_room_status(self, room_id: int, status: str):
        """به‌روزرسانی وضعیت اتاق"""
        try:
            from app.models.reception.room_status_models import RoomStatusChange

            with db_session() as session:
                status_change = RoomStatusChange(
                    room_id=room_id,
                    new_status=status,
                    changed_by=0,  # سیستم
                    change_type='automatic'
                )
                session.add(status_change)
                session.commit()

        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی وضعیت اتاق: {e}")

    def _generate_daily_housekeeping_report(self):
        """ایجاد گزارش روزانه خانه‌داری"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            today = datetime.now().date()

            with db_session() as session:
                # آمار وظایف امروز
                total_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.scheduled_time >= today
                ).count()

                completed_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.scheduled_time >= today,
                    HousekeepingTask.status.in_(['completed', 'verified'])
                ).count()

                in_progress_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.scheduled_time >= today,
                    HousekeepingTask.status == 'in_progress'
                ).count()

                completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

                # ذخیره در Redis برای نمایش در داشبورد
                report_data = {
                    'date': today.isoformat(),
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'in_progress_tasks': in_progress_tasks,
                    'completion_rate': round(completion_rate, 1),
                    'generated_at': datetime.now().isoformat()
                }

                self.redis.set(f'housekeeping_report:{today}', str(report_data))

                logger.info(f"📊 گزارش روزانه خانه‌داری ایجاد شد: {completion_rate}% تکمیل")

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد گزارش روزانه خانه‌داری: {e}")

    def get_todays_tasks(self, department: str = None) -> List[Dict[str, Any]]:
        """دریافت وظایف امروز"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            today = datetime.now().date()

            with db_session() as session:
                query = session.query(HousekeepingTask).filter(
                    HousekeepingTask.scheduled_time >= today
                )

                if department:
                    # فیلتر بر اساس بخش (در صورت نیاز)
                    pass

                tasks = query.order_by(
                    HousekeepingTask.priority.desc(),
                    HousekeepingTask.scheduled_time.asc()
                ).all()

                return [
                    {
                        'id': task.id,
                        'room_id': task.room_id,
                        'task_type': task.task_type,
                        'priority': task.priority,
                        'status': task.status,
                        'scheduled_time': task.scheduled_time.isoformat(),
                        'assigned_to': task.assigned_to,
                        'started_at': task.started_at.isoformat() if task.started_at else None,
                        'completed_at': task.completed_at.isoformat() if task.completed_at else None
                    }
                    for task in tasks
                ]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت وظایف امروز: {e}")
            return []

    def get_staff_performance(self, staff_id: int, days: int = 30) -> Dict[str, Any]:
        """دریافت عملکرد کارمند"""
        try:
            from app.models.reception.housekeeping_models import HousekeepingTask

            start_date = datetime.now().date() - timedelta(days=days)

            with db_session() as session:
                # آمار کلی
                total_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.assigned_to == staff_id,
                    HousekeepingTask.scheduled_time >= start_date
                ).count()

                completed_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.assigned_to == staff_id,
                    HousekeepingTask.scheduled_time >= start_date,
                    HousekeepingTask.status.in_(['completed', 'verified'])
                ).count()

                # میانگین امتیاز کیفیت
                quality_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.assigned_to == staff_id,
                    HousekeepingTask.scheduled_time >= start_date,
                    HousekeepingTask.quality_score.isnot(None)
                ).all()

                avg_quality = sum(task.quality_score for task in quality_tasks) / len(quality_tasks) if quality_tasks else 0

                return {
                    'staff_id': staff_id,
                    'period_days': days,
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
                    'average_quality': round(avg_quality, 1),
                    'performance_rating': self._calculate_performance_rating(completed_tasks, avg_quality)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت عملکرد کارمند: {e}")
            return {}

    def _calculate_performance_rating(self, completed_tasks: int, avg_quality: float) -> str:
        """محاسبه رتبه عملکرد"""
        if completed_tasks >= 20 and avg_quality >= 4.5:
            return "عالی"
        elif completed_tasks >= 15 and avg_quality >= 4.0:
            return "خوب"
        elif completed_tasks >= 10 and avg_quality >= 3.5:
            return "متوسط"
        else:
            return "نیاز به بهبود"

# ایجاد instance جهانی
housekeeping_manager = HousekeepingManager()
