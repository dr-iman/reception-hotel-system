# app/core/__init__.py
"""
هسته سیستم مدیریت پذیرش هتل
"""

from .database import (
    Base, db_session, get_redis, get_database_status,
    init_db, init_redis, create_tables
)

from .sync_manager import SyncManager, sync_manager
from .payment_processor import PaymentProcessor, payment_processor
from .audit_trail import (
    AuditManager, AuditActionType, AuditSeverity,
    audit_manager, audit_log, log_audit_event
)

# ایمپورت سایر ماژول‌های core
#try:
    from .notification_service import NotificationService, notification_service
#    from .housekeeping_manager import HousekeepingManager, housekeeping_manager
#    from .maintenance_manager import MaintenanceManager, maintenance_manager
#except ImportError:
    # برای محیط‌های توسعه که این ماژول‌ها هنوز ایجاد نشده‌اند
#    pass

__all__ = [
    # Database
    'Base', 'db_session', 'get_redis', 'get_database_status',
    'init_db', 'init_redis', 'create_tables',

    # Sync
    'SyncManager', 'sync_manager',

    # Payment
    'PaymentProcessor', 'payment_processor',

    # Audit
    'AuditManager', 'AuditActionType', 'AuditSeverity',
    'audit_manager', 'audit_log', 'log_audit_event',

    # Other core modules
    'NotificationService', 'notification_service'
#    'HousekeepingManager', 'housekeeping_manager',
#    'MaintenanceManager', 'maintenance_manager'
]
