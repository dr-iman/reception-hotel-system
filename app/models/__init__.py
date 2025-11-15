"""
ماژول مدل‌های داده سیستم پذیرش هتل
نسخه: 1.0
تاریخ: 1403/01/01
"""

# Import ماژول‌های مدل‌های بخش پذیرش
from app.models.reception import (
    guest_models,
    room_status_models,
    payment_models,
    housekeeping_models,
    maintenance_models,
    staff_models,
    notification_models,
    report_models
)

# Import کلاس‌های اصلی مدل‌های مهمانان
from app.models.reception.guest_models import Guest, Companion, Stay, CompanionStay

# Import کلاس‌های اصلی مدل‌های اتاق‌ها
from app.models.reception.room_status_models import RoomAssignment, RoomStatusChange, RoomStatusSnapshot

# Import کلاس‌های اصلی مدل‌های پرداخت
from app.models.reception.payment_models import Payment, GuestFolio, FolioTransaction, CashierShift

# Import کلاس‌های اصلی مدل‌های خانه‌داری
from app.models.reception.housekeeping_models import (
    HousekeepingTask,
    HousekeepingChecklist,
    HousekeepingSchedule,
    LostAndFound
)

# Import کلاس‌های اصلی مدل‌های تعمیرات
from app.models.reception.maintenance_models import (
    MaintenanceRequest,
    MaintenanceWorkOrder,
    MaintenanceInventory,
    PreventiveMaintenance
)

# Import کلاس‌های اصلی مدل‌های پرسنل
from app.models.reception.staff_models import Staff, User, UserActivityLog

# Import کلاس‌های اصلی مدل‌های اطلاع‌رسانی
from app.models.reception.notification_models import Notification, SyncRecord

# Import کلاس‌های اصلی مدل‌های گزارش‌گیری
from app.models.reception.report_models import DailyReport, DailyReportDetail

# لیست تمام کلاس‌های مدل برای export
__all__ = [
    # مدل‌های مهمانان و اقامت
    'Guest', 'Companion', 'Stay', 'CompanionStay',

    # مدل‌های مدیریت اتاق‌ها
    'RoomAssignment', 'RoomStatusChange', 'RoomStatusSnapshot',

    # مدل‌های مالی و پرداخت
    'Payment', 'GuestFolio', 'FolioTransaction', 'CashierShift',

    # مدل‌های خانه‌داری و نظافت
    'HousekeepingTask', 'HousekeepingChecklist', 'HousekeepingSchedule', 'LostAndFound',

    # مدل‌های تعمیرات و نگهداری
    'MaintenanceRequest', 'MaintenanceWorkOrder', 'MaintenanceInventory', 'PreventiveMaintenance',

    # مدل‌های مدیریت پرسنل
    'Staff', 'User', 'UserActivityLog',

    # مدل‌های اطلاع‌رسانی و همگام‌سازی
    'Notification', 'SyncRecord',

    # مدل‌های گزارش‌گیری و آمار
    'DailyReport', 'DailyReportDetail'
]

# گروه‌بندی مدل‌ها برای استفاده در migrations و ابزارهای توسعه
GUEST_MODELS = ['Guest', 'Companion', 'Stay', 'CompanionStay']
ROOM_MODELS = ['RoomAssignment', 'RoomStatusChange', 'RoomStatusSnapshot']
PAYMENT_MODELS = ['Payment', 'GuestFolio', 'FolioTransaction', 'CashierShift']
HOUSEKEEPING_MODELS = ['HousekeepingTask', 'HousekeepingChecklist', 'HousekeepingSchedule', 'LostAndFound']
MAINTENANCE_MODELS = ['MaintenanceRequest', 'MaintenanceWorkOrder', 'MaintenanceInventory', 'PreventiveMaintenance']
STAFF_MODELS = ['Staff', 'User', 'UserActivityLog']
NOTIFICATION_MODELS = ['Notification', 'SyncRecord']
REPORT_MODELS = ['DailyReport', 'DailyReportDetail']

# لیست کامل تمام مدل‌های سیستم
ALL_MODELS = (
    GUEST_MODELS + ROOM_MODELS + PAYMENT_MODELS +
    HOUSEKEEPING_MODELS + MAINTENANCE_MODELS +
    STAFF_MODELS + NOTIFICATION_MODELS + REPORT_MODELS
)

def get_model_classes():
    """
    دریافت دیکشنری از تمام کلاس‌های مدل

    Returns:
        dict: دیکشنری شامل نام کلاس و خود کلاس
    """
    return {
        'Guest': Guest,
        'Companion': Companion,
        'Stay': Stay,
        'CompanionStay': CompanionStay,
        'RoomAssignment': RoomAssignment,
        'RoomStatusChange': RoomStatusChange,
        'RoomStatusSnapshot': RoomStatusSnapshot,
        'Payment': Payment,
        'GuestFolio': GuestFolio,
        'FolioTransaction': FolioTransaction,
        'CashierShift': CashierShift,
        'HousekeepingTask': HousekeepingTask,
        'HousekeepingChecklist': HousekeepingChecklist,
        'HousekeepingSchedule': HousekeepingSchedule,
        'LostAndFound': LostAndFound,
        'MaintenanceRequest': MaintenanceRequest,
        'MaintenanceWorkOrder': MaintenanceWorkOrder,
        'MaintenanceInventory': MaintenanceInventory,
        'PreventiveMaintenance': PreventiveMaintenance,
        'Staff': Staff,
        'User': User,
        'UserActivityLog': UserActivityLog,
        'Notification': Notification,
        'SyncRecord': SyncRecord,
        'DailyReport': DailyReport,
        'DailyReportDetail': DailyReportDetail
    }

def get_model_by_name(model_name: str):
    """
    دریافت کلاس مدل بر اساس نام

    Args:
        model_name (str): نام کلاس مدل

    Returns:
        class: کلاس مدل مورد نظر

    Raises:
        ValueError: اگر مدل یافت نشد
    """
    model_classes = get_model_classes()
    if model_name in model_classes:
        return model_classes[model_name]
    else:
        raise ValueError(f"مدل '{model_name}' یافت نشد. مدل‌های موجود: {list(model_classes.keys())}")
