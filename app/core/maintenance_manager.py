# app/core/maintenance_manager.py
"""
مدیریت پیشرفته تاسیسات و تعمیرات هتل
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from app.core.database import db_session, get_redis
from config import config

logger = logging.getLogger(__name__)

class MaintenancePriority(Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EMERGENCY = "emergency"

class MaintenanceStatus(Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"
    CANCELLED = "cancelled"

@dataclass
class MaintenanceCategory:
    """دسته‌بندی تعمیرات"""
    name: str
    typical_duration: int  # مدت زمان معمول (دقیقه)
    required_skills: List[str]
    common_parts: List[str]

class MaintenanceManager:
    """مدیریت هوشمند تاسیسات و تعمیرات"""

    def __init__(self):
        self.redis = get_redis()
        self.categories = {
            'electrical': MaintenanceCategory(
                name="برق",
                typical_duration=60,
                required_skills=["برق کاری", "عیب‌یابی"],
                common_parts=["کلید", "پریز", "لامپ", "فیوز"]
            ),
            'plumbing': MaintenanceCategory(
                name="لوله‌کشی",
                typical_duration=90,
                required_skills=["لوله‌کشی", "تعمیر شیرآلات"],
                common_parts=["شیر", "لوله", "درپوش", "واتراستاپ"]
            ),
            'hvac': MaintenanceCategory(
                name="تهویه مطبوع",
                typical_duration=120,
                required_skills=["تعمیر کولر", "سرویس سیستم گرمایش"],
                common_parts=["فیلتر", "کمپرسور", "ترموستات"]
            ),
            'furniture': MaintenanceCategory(
                name="مبلمان",
                typical_duration=45,
                required_skills=["نجاری", "تعمیر مبلمان"],
                common_parts=["پیچ", "مهره", "چسب", "روکش"]
            ),
            'appliances': MaintenanceCategory(
                name="لوازم خانگی",
                typical_duration=75,
                required_skills=["تعمیر لوازم برقی"],
                common_parts=["موتور", "برد الکترونیکی", "سنسور"]
            )
        }

        # شروع مانیتورینگ خودکار
        self._start_preventive_maintenance_monitor()

    def _start_preventive_maintenance_monitor(self):
        """شروع مانیتورینگ تعمیرات پیشگیرانه"""
        self.pm_monitor_thread = threading.Thread(target=self._pm_monitor_worker, daemon=True)
        self.pm_monitor_thread.start()
        logger.info("🚀 مانیتورینگ تعمیرات پیشگیرانه شروع شد")

    def _pm_monitor_worker(self):
        """کارگر مانیتورینگ تعمیرات پیشگیرانه"""
        while True:
            try:
                # بررسی تعمیرات پیشگیرانه overdue
                self._check_preventive_maintenance()

                # بررسی درخواست‌های urgent
                self._check_urgent_requests()

                # ایجاد گزارش روزانه
                self._generate_daily_maintenance_report()

                # خواب به مدت 10 دقیقه
                threading.Event().wait(600)

            except Exception as e:
                logger.error(f"❌ خطا در مانیتورینگ تعمیرات پیشگیرانه: {e}")
                threading.Event().wait(60)

    def _check_preventive_maintenance(self):
        """بررسی تعمیرات پیشگیرانه"""
        try:
            from app.models.reception.maintenance_models import PreventiveMaintenance

            today = datetime.now().date()

            with db_session() as session:
                # یافتن تعمیرات پیشگیرانه overdue
                overdue_pm = session.query(PreventiveMaintenance).filter(
                    PreventiveMaintenance.next_due <= today,
                    PreventiveMaintenance.status.in_(['scheduled', 'overdue'])
                ).all()

                for pm in overdue_pm:
                    # ایجاد درخواست تعمیرات
                    self._create_maintenance_request_from_pm(pm)
                    pm.status = 'overdue'

                    logger.warning(f"⚠️ تعمیرات پیشگیرانه overdue: {pm.maintenance_type}")

                session.commit()

        except Exception as e:
            logger.error(f"❌ خطا در بررسی تعمیرات پیشگیرانه: {e}")

    def _create_maintenance_request_from_pm(self, pm):
        """ایجاد درخواست تعمیرات از تعمیرات پیشگیرانه"""
        try:
            from app.models.reception.maintenance_models import MaintenanceRequest

            request = MaintenanceRequest(
                room_id=pm.room_id,
                equipment_id=pm.equipment_id,
                issue_type=pm.maintenance_type,
                issue_description=f"تعمیرات پیشگیرانه: {pm.description}",
                priority='normal',
                reported_by=0,  # سیستم
                room_available=True
            )

            with db_session() as session:
                session.add(request)
                session.commit()

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد درخواست تعمیرات: {e}")

    def _check_urgent_requests(self):
        """بررسی درخواست‌های فوری"""
        try:
            from app.models.reception.maintenance_models import MaintenanceRequest

            with db_session() as session:
                # یافتن درخواست‌های فوری بدون تکنسین
                urgent_requests = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.priority.in_(['high', 'emergency']),
                    MaintenanceRequest.assigned_to.is_(None),
                    MaintenanceRequest.status == 'open'
                ).all()

                for request in urgent_requests:
                    # یافتن تکنسین مناسب
                    suitable_technician = self._find_suitable_technician(request.issue_type)
                    if suitable_technician:
                        request.assigned_to = suitable_technician
                        request.status = 'assigned'
                        logger.info(f"🔧 درخواست فوری {request.id} به تکنسین {suitable_technician} محول شد")

                session.commit()

        except Exception as e:
            logger.error(f"❌ خطا در بررسی درخواست‌های فوری: {e}")

    def _find_suitable_technician(self, issue_type: str) -> Optional[int]:
        """یافتن تکنسین مناسب برای نوع مشکل"""
        try:
            from app.models.reception.staff_models import Staff

            category = self.categories.get(issue_type)
            if not category:
                return None

            with db_session() as session:
                # یافتن تکنسین‌های با مهارت مرتبط
                technicians = session.query(Staff).filter(
                    Staff.department == 'maintenance',
                    Staff.is_active == True
                ).all()

                for tech in technicians:
                    # در نسخه واقعی، مهارت‌ها از پروفایل کارمند بررسی می‌شود
                    # برای نمونه، اولین تکنسین available برمی‌گردد
                    if self._is_technician_available(tech.id):
                        return tech.id

                return None

        except Exception as e:
            logger.error(f"❌ خطا در یافتن تکنسین: {e}")
            return None

    def _is_technician_available(self, technician_id: int) -> bool:
        """بررسی availability تکنسین"""
        try:
            from app.models.reception.maintenance_models import MaintenanceWorkOrder

            with db_session() as session:
                # بررسی وظایف در حال انجام
                current_work = session.query(MaintenanceWorkOrder).filter(
                    MaintenanceWorkOrder.assigned_to == technician_id,
                    MaintenanceWorkOrder.status.in_(['scheduled', 'in_progress'])
                ).count()

                return current_work < 3  # حداکثر 3 کار همزمان

        except Exception as e:
            logger.error(f"❌ خطا در بررسی availability تکنسین: {e}")
            return False

    def create_maintenance_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """ایجاد درخواست تعمیرات جدید"""
        try:
            from app.models.reception.maintenance_models import MaintenanceRequest

            with db_session() as session:
                request = MaintenanceRequest(
                    room_id=request_data['room_id'],
                    reported_by=request_data['reported_by'],
                    issue_type=request_data['issue_type'],
                    issue_description=request_data['issue_description'],
                    priority=request_data.get('priority', 'normal'),
                    room_available=request_data.get('room_available', True),
                    estimated_downtime=request_data.get('estimated_downtime'),
                    estimated_cost=request_data.get('estimated_cost', 0)
                )

                session.add(request)
                session.commit()

                # ارسال notification
                self._send_new_request_notification(request)

                logger.info(f"🔧 درخواست تعمیرات جدید ایجاد شد: {request.id}")

                return {
                    'success': True,
                    'request_id': request.id,
                    'message': 'درخواست تعمیرات ایجاد شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد درخواست تعمیرات: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def assign_request(self, request_id: int, technician_id: int,
                      scheduled_start: datetime) -> Dict[str, Any]:
        """محول کردن درخواست به تکنسین"""
        try:
            from app.models.reception.maintenance_models import MaintenanceRequest, MaintenanceWorkOrder

            with db_session() as session:
                request = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.id == request_id
                ).first()

                if not request:
                    return {
                        'success': False,
                        'error': 'درخواست یافت نشد'
                    }

                # ایجاد دستورکار
                work_order = MaintenanceWorkOrder(
                    request_id=request_id,
                    assigned_to=technician_id,
                    work_description=request.issue_description,
                    scheduled_start=scheduled_start,
                    required_parts=self._get_required_parts(request.issue_type),
                    tools_needed=self._get_required_tools(request.issue_type)
                )

                request.assigned_to = technician_id
                request.status = MaintenanceStatus.ASSIGNED.value
                request.scheduled_date = scheduled_start

                session.add(work_order)
                session.commit()

                logger.info(f"👤 درخواست {request_id} به تکنسین {technician_id} محول شد")

                return {
                    'success': True,
                    'work_order_id': work_order.id,
                    'message': 'درخواست محول شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در محول کردن درخواست: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def start_work(self, work_order_id: int, technician_id: int) -> Dict[str, Any]:
        """شروع کار تعمیرات"""
        try:
            from app.models.reception.maintenance_models import MaintenanceWorkOrder, MaintenanceRequest

            with db_session() as session:
                work_order = session.query(MaintenanceWorkOrder).filter(
                    MaintenanceWorkOrder.id == work_order_id,
                    MaintenanceWorkOrder.assigned_to == technician_id
                ).first()

                if not work_order:
                    return {
                        'success': False,
                        'error': 'دستورکار یافت نشد'
                    }

                work_order.status = MaintenanceStatus.IN_PROGRESS.value
                work_order.actual_start = datetime.now()

                # به‌روزرسانی وضعیت درخواست
                request = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.id == work_order.request_id
                ).first()
                if request:
                    request.status = MaintenanceStatus.IN_PROGRESS.value

                session.commit()

                logger.info(f"▶️ کار تعمیرات {work_order_id} شروع شد")

                return {
                    'success': True,
                    'message': 'کار تعمیرات شروع شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در شروع کار تعمیرات: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def complete_work(self, work_order_id: int, technician_id: int,
                     work_performed: str, parts_used: List[Dict],
                     labor_hours: float) -> Dict[str, Any]:
        """اتمام کار تعمیرات"""
        try:
            from app.models.reception.maintenance_models import MaintenanceWorkOrder, MaintenanceRequest

            with db_session() as session:
                work_order = session.query(MaintenanceWorkOrder).filter(
                    MaintenanceWorkOrder.id == work_order_id,
                    MaintenanceWorkOrder.assigned_to == technician_id
                ).first()

                if not work_order:
                    return {
                        'success': False,
                        'error': 'دستورکار یافت نشد'
                    }

                work_order.status = MaintenanceStatus.COMPLETED.value
                work_order.actual_end = datetime.now()
                work_order.work_performed = work_performed
                # اصلاح این خط - تبدیل به JSON اگر نیاز است
                work_order.parts_used = str(parts_used) if parts_used else None
                work_order.labor_hours = labor_hours

                # به‌روزرسانی وضعیت درخواست
                request = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.id == work_order.request_id
                ).first()
                if request:
                    request.status = MaintenanceStatus.COMPLETED.value
                    request.completed_at = datetime.now()

                    # محاسبه هزینه نهایی
                    request.actual_cost = self._calculate_total_cost(parts_used, labor_hours)

                session.commit()

                # به‌روزرسانی وضعیت اتاق
                if request and request.room_id:
                    self._update_room_maintenance_status(request.room_id, 'maintenance_completed')

                logger.info(f"✅ کار تعمیرات {work_order_id} تکمیل شد")

                return {
                    'success': True,
                    'message': 'کار تعمیرات تکمیل شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در اتمام کار تعمیرات: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def verify_work(self, work_order_id: int, inspector_id: int,
                   verification_notes: str = None) -> Dict[str, Any]:
        """تأیید کار تعمیرات"""
        try:
            from app.models.reception.maintenance_models import MaintenanceWorkOrder, MaintenanceRequest

            with db_session() as session:
                work_order = session.query(MaintenanceWorkOrder).filter(
                    MaintenanceWorkOrder.id == work_order_id,
                    MaintenanceWorkOrder.status == MaintenanceStatus.COMPLETED.value
                ).first()

                if not work_order:
                    return {
                        'success': False,
                        'error': 'دستورکار یافت نشد یا هنوز تکمیل نشده است'
                    }

                work_order.verified_by = inspector_id
                work_order.verification_notes = verification_notes

                # به‌روزرسانی وضعیت درخواست
                request = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.id == work_order.request_id
                ).first()
                if request:
                    request.status = MaintenanceStatus.CLOSED.value

                session.commit()

                logger.info(f"🔍 کار تعمیرات {work_order_id} تأیید شد")

                return {
                    'success': True,
                    'message': 'کار تعمیرات تأیید شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در تأیید کار تعمیرات: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _get_required_parts(self, issue_type: str) -> List[str]:
        """دریافت قطعات مورد نیاز برای نوع مشکل"""
        category = self.categories.get(issue_type)
        return category.common_parts if category else []

    def _get_required_tools(self, issue_type: str) -> List[str]:
        """دریافت ابزار مورد نیاز"""
        tools = {
            'electrical': ['مولتی‌متر', 'انبر دست', 'پیچ‌گوشتی'],
            'plumbing': ['آچار فرانسه', 'انبر لوله', 'نوار تفلون'],
            'hvac': ['گاز مبرد', 'مانومتر', 'پیچ‌گوشتی'],
            'furniture': ['چکش', 'اره', 'دریل'],
            'appliances': ['مولتی‌متر', 'هویه', 'پیچ‌گوشتی']
        }
        return tools.get(issue_type, [])

    def _calculate_total_cost(self, parts_used: List[Dict], labor_hours: float) -> float:
        """محاسبه هزینه کل تعمیرات"""
        try:
            from app.models.reception.maintenance_models import MaintenanceInventory

            parts_cost = 0
            labor_rate = 50000  # نرخ ساعتی کارگر (تومان)

            with db_session() as session:
                for part in parts_used:
                    inventory_item = session.query(MaintenanceInventory).filter(
                        MaintenanceInventory.item_code == part['code']
                    ).first()
                    if inventory_item:
                        parts_cost += inventory_item.unit_cost * part['quantity']

            labor_cost = labor_hours * labor_rate
            return parts_cost + labor_cost

        except Exception as e:
            logger.error(f"❌ خطا در محاسبه هزینه: {e}")
            return 0

    def _update_room_maintenance_status(self, room_id: int, status: str):
        """به‌روزرسانی وضعیت تعمیرات اتاق"""
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

    def _send_new_request_notification(self, request):
        """ارسال notification برای درخواست جدید"""
        try:
            from app.core.notification_service import notification_service

            message = f"درخواست تعمیرات جدید برای اتاق {request.room_id}: {request.issue_description}"

            notification_service.send_to_department(
                department='maintenance',
                title='درخواست تعمیرات جدید',
                message=message,
                notification_type='info'
            )

        except Exception as e:
            logger.error(f"❌ خطا در ارسال notification: {e}")

    def _generate_daily_maintenance_report(self):
        """ایجاد گزارش روزانه تاسیسات"""
        try:
            from app.models.reception.maintenance_models import MaintenanceRequest

            today = datetime.now().date()

            with db_session() as session:
                # آمار درخواست‌های امروز
                total_requests = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.reported_at >= today
                ).count()

                completed_requests = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.reported_at >= today,
                    MaintenanceRequest.status.in_(['completed', 'closed'])
                ).count()

                urgent_requests = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.reported_at >= today,
                    MaintenanceRequest.priority.in_(['high', 'emergency'])
                ).count()

                completion_rate = (completed_requests / total_requests * 100) if total_requests > 0 else 0

                # ذخیره در Redis
                report_data = {
                    'date': today.isoformat(),
                    'total_requests': total_requests,
                    'completed_requests': completed_requests,
                    'urgent_requests': urgent_requests,
                    'completion_rate': round(completion_rate, 1),
                    'generated_at': datetime.now().isoformat()
                }

                self.redis.set(f'maintenance_report:{today}', str(report_data))

                logger.info(f"📊 گزارش روزانه تاسیسات ایجاد شد: {completion_rate}% تکمیل")

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد گزارش روزانه تاسیسات: {e}")

    def get_open_requests(self) -> List[Dict[str, Any]]:
        """دریافت درخواست‌های باز"""
        try:
            from app.models.reception.maintenance_models import MaintenanceRequest

            with db_session() as session:
                requests = session.query(MaintenanceRequest).filter(
                    MaintenanceRequest.status.in_(['open', 'assigned', 'in_progress'])
                ).order_by(
                    MaintenanceRequest.priority.desc(),
                    MaintenanceRequest.reported_at.asc()
                ).all()

                return [
                    {
                        'id': req.id,
                        'room_id': req.room_id,
                        'issue_type': req.issue_type,
                        'issue_description': req.issue_description,
                        'priority': req.priority,
                        'status': req.status,
                        'reported_at': req.reported_at.isoformat(),
                        'assigned_to': req.assigned_to,
                        'room_available': req.room_available
                    }
                    for req in requests
                ]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت درخواست‌های باز: {e}")
            return []

    def get_technician_performance(self, technician_id: int, days: int = 30) -> Dict[str, Any]:
        """دریافت عملکرد تکنسین"""
        try:
            from app.models.reception.maintenance_models import MaintenanceWorkOrder

            start_date = datetime.now().date() - timedelta(days=days)

            with db_session() as session:
                # آمار کلی
                total_work_orders = session.query(MaintenanceWorkOrder).filter(
                    MaintenanceWorkOrder.assigned_to == technician_id,
                    MaintenanceWorkOrder.scheduled_start >= start_date
                ).count()

                completed_work_orders = session.query(MaintenanceWorkOrder).filter(
                    MaintenanceWorkOrder.assigned_to == technician_id,
                    MaintenanceWorkOrder.scheduled_start >= start_date,
                    MaintenanceWorkOrder.status.in_(['completed', 'verified'])
                ).count()

                # میانگین زمان تکمیل
                completed_orders = session.query(MaintenanceWorkOrder).filter(
                    MaintenanceWorkOrder.assigned_to == technician_id,
                    MaintenanceWorkOrder.scheduled_start >= start_date,
                    MaintenanceWorkOrder.actual_end.isnot(None),
                    MaintenanceWorkOrder.actual_start.isnot(None)
                ).all()

                avg_completion_time = 0
                if completed_orders:
                    total_time = sum(
                        (order.actual_end - order.actual_start).total_seconds()
                        for order in completed_orders
                    )
                    avg_completion_time = total_time / len(completed_orders) / 60  # به دقیقه

                return {
                    'technician_id': technician_id,
                    'period_days': days,
                    'total_work_orders': total_work_orders,
                    'completed_work_orders': completed_work_orders,
                    'completion_rate': (completed_work_orders / total_work_orders * 100) if total_work_orders > 0 else 0,
                    'average_completion_time': round(avg_completion_time, 1),
                    'performance_rating': self._calculate_tech_performance_rating(completed_work_orders, avg_completion_time)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت عملکرد تکنسین: {e}")
            return {}

    def _calculate_tech_performance_rating(self, completed_orders: int, avg_time: float) -> str:
        """محاسبه رتبه عملکرد تکنسین"""
        if completed_orders >= 15 and avg_time <= 90:
            return "عالی"
        elif completed_orders >= 10 and avg_time <= 120:
            return "خوب"
        elif completed_orders >= 5 and avg_time <= 150:
            return "متوسط"
        else:
            return "نیاز به بهبود"

# ایجاد instance جهانی
maintenance_manager = MaintenanceManager()
