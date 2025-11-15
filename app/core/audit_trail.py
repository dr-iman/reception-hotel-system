# app/core/audit_trail.py
"""
سیستم ردیابی و Audit جامع برای تمام فعالیت‌های سیستم پذیرش هتل
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum

from app.core.database import Base, db_session
from config import config

logger = logging.getLogger(__name__)

class AuditActionType(Enum):
    """انواع فعالیت‌های قابل ردیابی"""

    # مدیریت مهمانان
    GUEST_CREATE = "guest_create"
    GUEST_UPDATE = "guest_update"
    GUEST_DELETE = "guest_delete"
    GUEST_CHECK_IN = "guest_check_in"
    GUEST_CHECK_OUT = "guest_check_out"

    # مدیریت اتاق‌ها
    ROOM_ASSIGN = "room_assign"
    ROOM_STATUS_CHANGE = "room_status_change"
    ROOM_TRANSFER = "room_transfer"

    # پرداخت‌ها
    PAYMENT_PROCESS = "payment_process"
    PAYMENT_REFUND = "payment_refund"
    PAYMENT_VOID = "payment_void"

    # مالی
    FOLIO_CHARGE = "folio_charge"
    FOLIO_ADJUSTMENT = "folio_adjustment"

    # نظافت
    CLEANING_TASK_CREATE = "cleaning_task_create"
    CLEANING_TASK_COMPLETE = "cleaning_task_complete"
    CLEANING_TASK_CANCEL = "cleaning_task_cancel"

    # تعمیرات
    MAINTENANCE_REQUEST = "maintenance_request"
    MAINTENANCE_COMPLETE = "maintenance_complete"

    # سیستم
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"

    # تنظیمات
    SETTINGS_UPDATE = "settings_update"

    # پشتیبان‌گیری
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    BACKUP_DELETE = "backup_delete"

    # امنیت
    PERMISSION_CHANGE = "permission_change"
    ROLE_CHANGE = "role_change"

class AuditSeverity(Enum):
    """سطوح شدت رویدادهای Audit"""

    LOW = "low"          # فعالیت‌های عادی
    MEDIUM = "medium"    # تغییرات مهم
    HIGH = "high"        # تغییرات حساس
    CRITICAL = "critical" # فعالیت‌های بحرانی

class AuditTrail(Base):
    """مدل ذخیره‌سازی رکوردهای Audit"""

    __tablename__ = 'system_audit_trail'

    id = Column(Integer, primary_key=True)

    # اطلاعات پایه
    timestamp = Column(DateTime, nullable=False, default=datetime.now)
    action_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default=AuditSeverity.LOW.value)

    # اطلاعات کاربر
    user_id = Column(Integer, nullable=False)  # ID کاربر انجام دهنده
    user_name = Column(String(100))            # نام کاربر برای نمایش
    user_role = Column(String(50))             # نقش کاربر

    # اطلاعات موجودیت
    entity_type = Column(String(50))           # نوع موجودیت (guest, room, payment, etc.)
    entity_id = Column(Integer)                # ID موجودیت
    entity_name = Column(String(200))          # نام موجودیت برای نمایش

    # اطلاعات تغییرات
    old_values = Column(JSON)                  # مقادیر قبلی (برای تغییرات)
    new_values = Column(JSON)                  # مقادیر جدید (برای تغییرات)
    changes = Column(JSON)                     # لیست تغییرات انجام شده

    # اطلاعات اضافی
    description = Column(Text)                 # شرح فعالیت
    ip_address = Column(String(45))            # آدرس IP کاربر
    user_agent = Column(Text)                  # User Agent مرورگر
    session_id = Column(String(100))           # ID Session

    # وضعیت
    status = Column(String(20), default='success')  # success, failed, pending
    error_message = Column(Text)               # پیغام خطا در صورت عدم موفقیت

    # اطلاعات سیستمی
    module = Column(String(100))               # ماژول مربوطه
    feature = Column(String(100))              # ویژگی مربوطه
    correlation_id = Column(String(100))       # ID برای ردیابی زنجیره‌ای

    # ایندکس‌ها برای جستجوی سریع
    __table_args__ = (
        {'schema': 'system'}
    )

class AuditManager:
    """مدیریت پیشرفته سیستم Audit"""

    def __init__(self):
        self.enabled = config.security.audit_log_enabled
        self.retention_days = 365  # مدت نگهداری رکوردها
        self.batch_size = 100      # سایز بچ برای پردازش دسته‌ای

    def log_activity(self,
                    action_type: AuditActionType,
                    user_id: int,
                    user_name: str,
                    user_role: str,
                    entity_type: str = None,
                    entity_id: int = None,
                    entity_name: str = None,
                    old_values: Dict[str, Any] = None,
                    new_values: Dict[str, Any] = None,
                    description: str = None,
                    ip_address: str = None,
                    user_agent: str = None,
                    session_id: str = None,
                    severity: AuditSeverity = AuditSeverity.LOW,
                    module: str = None,
                    feature: str = None,
                    correlation_id: str = None) -> bool:
        """
        ثبت فعالیت جدید در سیستم Audit

        Args:
            action_type: نوع فعالیت
            user_id: ID کاربر انجام دهنده
            user_name: نام کاربر
            user_role: نقش کاربر
            entity_type: نوع موجودیت (اختیاری)
            entity_id: ID موجودیت (اختیاری)
            entity_name: نام موجودیت (اختیاری)
            old_values: مقادیر قبلی (برای تغییرات)
            new_values: مقادیر جدید (برای تغییرات)
            description: شرح فعالیت
            ip_address: آدرس IP
            user_agent: User Agent مرورگر
            session_id: ID Session
            severity: سطح شدت
            module: ماژول مربوطه
            feature: ویژگی مربوطه
            correlation_id: ID برای ردیابی زنجیره‌ای

        Returns:
            bool: موفقیت آمیز بودن ثبت
        """

        if not self.enabled:
            return True

        try:
            # محاسبه تغییرات
            changes = self._calculate_changes(old_values, new_values)

            # ایجاد رکورد Audit
            audit_record = AuditTrail(
                action_type=action_type.value,
                severity=severity.value,
                user_id=user_id,
                user_name=user_name,
                user_role=user_role,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                old_values=old_values,
                new_values=new_values,
                changes=changes,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                module=module,
                feature=feature,
                correlation_id=correlation_id,
                status='success'
            )

            # ذخیره در دیتابیس
            with db_session() as session:
                session.add(audit_record)
                session.commit()

            logger.debug(f"فعالیت Audit ثبت شد: {action_type.value} توسط {user_name}")
            return True

        except Exception as e:
            logger.error(f"خطا در ثبت فعالیت Audit: {e}")
            return False

    def _calculate_changes(self, old_values: Dict[str, Any], new_values: Dict[str, Any]) -> List[Dict[str, Any]]:
        """محاسبه تغییرات بین مقادیر قدیم و جدید"""

        if not old_values or not new_values:
            return []

        changes = []

        for key in set(old_values.keys()) | set(new_values.keys()):
            old_val = old_values.get(key)
            new_val = new_values.get(key)

            # بررسی تغییر
            if old_val != new_val:
                change = {
                    'field': key,
                    'old_value': old_val,
                    'new_value': new_val,
                    'change_type': 'modified'
                }

                if old_val is None:
                    change['change_type'] = 'added'
                elif new_val is None:
                    change['change_type'] = 'removed'

                changes.append(change)

        return changes

    def get_audit_logs(self,
                      start_date: datetime = None,
                      end_date: datetime = None,
                      user_id: int = None,
                      action_type: AuditActionType = None,
                      entity_type: str = None,
                      entity_id: int = None,
                      severity: AuditSeverity = None,
                      module: str = None,
                      limit: int = 100,
                      offset: int = 0) -> List[Dict[str, Any]]:
        """
        دریافت لاگ‌های Audit با فیلترهای مختلف

        Args:
            start_date: تاریخ شروع
            end_date: تاریخ پایان
            user_id: فیلتر بر اساس کاربر
            action_type: فیلتر بر اساس نوع فعالیت
            entity_type: فیلتر بر اساس نوع موجودیت
            entity_id: فیلتر بر اساس ID موجودیت
            severity: فیلتر بر اساس سطح شدت
            module: فیلتر بر اساس ماژول
            limit: تعداد رکوردها
            offset: آفست برای صفحه‌بندی

        Returns:
            List[Dict]: لیست رکوردهای Audit
        """

        try:
            with db_session() as session:
                query = session.query(AuditTrail)

                # اعمال فیلترها
                if start_date:
                    query = query.filter(AuditTrail.timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditTrail.timestamp <= end_date)
                if user_id:
                    query = query.filter(AuditTrail.user_id == user_id)
                if action_type:
                    query = query.filter(AuditTrail.action_type == action_type.value)
                if entity_type:
                    query = query.filter(AuditTrail.entity_type == entity_type)
                if entity_id:
                    query = query.filter(AuditTrail.entity_id == entity_id)
                if severity:
                    query = query.filter(AuditTrail.severity == severity.value)
                if module:
                    query = query.filter(AuditTrail.module == module)

                # مرتب‌سازی و محدودیت
                query = query.order_by(AuditTrail.timestamp.desc())
                query = query.offset(offset).limit(limit)

                results = query.all()

                # تبدیل به دیکشنری
                audit_logs = []
                for record in results:
                    audit_logs.append(self._serialize_audit_record(record))

                return audit_logs

        except Exception as e:
            logger.error(f"خطا در دریافت لاگ‌های Audit: {e}")
            return []

    def _serialize_audit_record(self, record: AuditTrail) -> Dict[str, Any]:
        """سریالایز کردن رکورد Audit"""

        return {
            'id': record.id,
            'timestamp': record.timestamp.isoformat(),
            'action_type': record.action_type,
            'severity': record.severity,
            'user_id': record.user_id,
            'user_name': record.user_name,
            'user_role': record.user_role,
            'entity_type': record.entity_type,
            'entity_id': record.entity_id,
            'entity_name': record.entity_name,
            'old_values': record.old_values,
            'new_values': record.new_values,
            'changes': record.changes,
            'description': record.description,
            'ip_address': record.ip_address,
            'user_agent': record.user_agent,
            'session_id': record.session_id,
            'module': record.module,
            'feature': record.feature,
            'correlation_id': record.correlation_id,
            'status': record.status,
            'error_message': record.error_message
        }

    def get_audit_statistics(self,
                           start_date: datetime = None,
                           end_date: datetime = None) -> Dict[str, Any]:
        """
        دریافت آمار و گزارش از فعالیت‌های Audit

        Args:
            start_date: تاریخ شروع
            end_date: تاریخ پایان

        Returns:
            Dict: آمار فعالیت‌ها
        """

        try:
            with db_session() as session:
                # پایه query
                query = session.query(AuditTrail)

                if start_date:
                    query = query.filter(AuditTrail.timestamp >= start_date)
                if end_date:
                    query = query.filter(AuditTrail.timestamp <= end_date)

                # آمار کلی
                total_activities = query.count()

                # آمار بر اساس نوع فعالیت
                activity_stats = session.query(
                    AuditTrail.action_type,
                    AuditTrail.severity,
                    AuditTrail.user_role
                ).filter(
                    AuditTrail.timestamp >= start_date if start_date else True,
                    AuditTrail.timestamp <= end_date if end_date else True
                ).all()

                # گروه‌بندی آمار
                stats = {
                    'total_activities': total_activities,
                    'by_action_type': {},
                    'by_severity': {},
                    'by_user_role': {},
                    'by_hour': {},
                    'success_rate': 0
                }

                # محاسبه آمار
                success_count = 0
                for record in activity_stats:
                    # بر اساس نوع فعالیت
                    action_type = record.action_type
                    stats['by_action_type'][action_type] = stats['by_action_type'].get(action_type, 0) + 1

                    # بر اساس سطح شدت
                    severity = record.severity
                    stats['by_severity'][severity] = stats['by_severity'].get(severity, 0) + 1

                    # بر اساس نقش کاربر
                    user_role = record.user_role
                    stats['by_user_role'][user_role] = stats['by_user_role'].get(user_role, 0) + 1

                    # نرخ موفقیت
                    if record.status == 'success':
                        success_count += 1

                # محاسبه نرخ موفقیت
                if total_activities > 0:
                    stats['success_rate'] = (success_count / total_activities) * 100

                return stats

        except Exception as e:
            logger.error(f"خطا در محاسبه آمار Audit: {e}")
            return {}

    def cleanup_old_records(self) -> int:
        """
        پاک کردن رکوردهای قدیمی بر اساس retention policy

        Returns:
            int: تعداد رکوردهای پاک شده
        """

        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            with db_session() as session:
                # شمارش رکوردهای قدیمی
                old_records_count = session.query(AuditTrail).filter(
                    AuditTrail.timestamp < cutoff_date
                ).count()

                # حذف رکوردهای قدیمی
                deleted_count = session.query(AuditTrail).filter(
                    AuditTrail.timestamp < cutoff_date
                ).delete()

                session.commit()

                logger.info(f"تعداد {deleted_count} رکورد Audit قدیمی پاک شد")
                return deleted_count

        except Exception as e:
            logger.error(f"خطا در پاک کردن رکوردهای قدیمی Audit: {e}")
            return 0

    def export_audit_logs(self,
                         start_date: datetime,
                         end_date: datetime,
                         export_format: str = 'json') -> Optional[str]:
        """
        خروجی گرفتن از لاگ‌های Audit

        Args:
            start_date: تاریخ شروع
            end_date: تاریخ پایان
            export_format: فرمت خروجی (json, csv)

        Returns:
            str: مسیر فایل خروجی یا None در صورت خطا
        """

        try:
            # دریافت لاگ‌ها
            audit_logs = self.get_audit_logs(start_date=start_date, end_date=end_date, limit=10000)

            if not audit_logs:
                return None

            # ایجاد فایل خروجی
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_export_{timestamp}.{export_format}"
            filepath = os.path.join(config.data_dir, 'exports', filename)

            # ایجاد پوشه اگر وجود ندارد
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            if export_format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(audit_logs, f, ensure_ascii=False, indent=2)

            elif export_format == 'csv':
                import csv
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    if audit_logs:
                        fieldnames = audit_logs[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(audit_logs)

            logger.info(f"لاگ‌های Audit با موفقیت export شدند: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"خطا در export لاگ‌های Audit: {e}")
            return None

# دکوراتور برای ثبت خودکار فعالیت‌ها
def audit_log(action_type: AuditActionType,
              severity: AuditSeverity = AuditSeverity.LOW,
              entity_type: str = None,
              description: str = None):
    """
    دکوراتور برای ثبت خودکار فعالیت‌های تابع

    Usage:
        @audit_log(AuditActionType.USER_CREATE, AuditSeverity.MEDIUM, 'user')
        def create_user(user_data):
            ...
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # اجرای تابع اصلی
            result = func(*args, **kwargs)

            # ثبت فعالیت Audit
            try:
                # استخراج اطلاعات از آرگومان‌ها و نتیجه
                # این بخش نیاز به سفارشی‌سازی بر اساس هر تابع دارد
                user_id = kwargs.get('user_id') or getattr(args[0], 'current_user_id', None)
                user_name = kwargs.get('user_name') or 'System'
                user_role = kwargs.get('user_role') or 'system'

                # ثبت فعالیت
                audit_manager.log_activity(
                    action_type=action_type,
                    user_id=user_id,
                    user_name=user_name,
                    user_role=user_role,
                    entity_type=entity_type,
                    description=description or f"تابع {func.__name__} اجرا شد",
                    severity=severity,
                    module=func.__module__,
                    feature=func.__name__
                )

            except Exception as e:
                logger.error(f"خطا در ثبت خودکار Audit: {e}")

            return result
        return wrapper
    return decorator

# ایجاد instance جهانی
audit_manager = AuditManager()

# تابع کمکی برای استفاده آسان
def log_audit_event(action_type: AuditActionType,
                   user_id: int,
                   user_name: str,
                   user_role: str,
                   **kwargs):
    """
    تابع ساده برای ثبت رویدادهای Audit

    Args:
        action_type: نوع فعالیت
        user_id: ID کاربر
        user_name: نام کاربر
        user_role: نقش کاربر
        **kwargs: سایر پارامترها
    """

    return audit_manager.log_activity(
        action_type=action_type,
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        **kwargs
    )
