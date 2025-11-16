"""
ماژول مدل‌های بخش پذیرش هتل
شامل تمام مدل‌های مربوط به مدیریت مهمانان، اتاق‌ها، پرداخت‌ها و عملیات روزانه

ویژگی‌ها:
• مدل‌های مدیریت مهمانان و اقامت
• مدل‌های وضعیت اتاق‌ها
• مدل‌های مالی و پرداخت
• مدل‌های خانه‌داری و نظافت
• مدل‌های تعمیرات و نگهداری
• مدل‌های پرسنل و کاربران
• مدل‌های اطلاع‌رسانی
• مدل‌های گزارش‌گیری

نسخه: 1.0
تاریخ: 1403/01/01
"""

# Import کلاس‌های مدل از ماژول‌های مختلف
from .app.core.database import Base
from .guest_models import Guest, Companion, Stay, CompanionStay
from .room_status_models import RoomAssignment, RoomStatusChange, RoomStatusSnapshot
from .payment_models import Payment, GuestFolio, FolioTransaction, CashierShift
#from .housekeeping_models import HousekeepingTask, HousekeepingChecklist, HousekeepingSchedule, LostAndFound
#from .maintenance_models import MaintenanceRequest, MaintenanceWorkOrder, MaintenanceInventory, PreventiveMaintenance
from .staff_models import Staff, User, UserActivityLog
from .notification_models import Notification, SyncRecord
from .report_models import DailyReport, DailyReportDetail

# لیست export برای import *
__all__ = [
    # مدل‌های مهمانان
    'Guest', 'Companion', 'Stay', 'CompanionStay',

    # مدل‌های اتاق‌ها
    'RoomAssignment', 'RoomStatusChange', 'RoomStatusSnapshot',

    # مدل‌های مالی
    'Payment', 'GuestFolio', 'FolioTransaction', 'CashierShift',

    # مدل‌های خانه‌داری
#    'HousekeepingTask', 'HousekeepingChecklist', 'HousekeepingSchedule', 'LostAndFound',

    # مدل‌های تعمیرات
#    'MaintenanceRequest', 'MaintenanceWorkOrder', 'MaintenanceInventory', 'PreventiveMaintenance',

    # مدل‌های پرسنل
    'Staff', 'User', 'UserActivityLog',

    # مدل‌های اطلاع‌رسانی
    'Notification', 'SyncRecord',

    # مدل‌های گزارش
    'DailyReport', 'DailyReportDetail'
]

# گروه‌بندی مدل‌ها برای استفاده در سرویس‌ها و ابزارها

## مدل‌های مدیریت مهمانان
GUEST_MANAGEMENT_MODELS = [
    Guest,           # اطلاعات مهمانان
    Companion,       # همراهان مهمان
    Stay,            # اطلاعات اقامت
    CompanionStay    # ارتباط همراهان با اقامت
]

## مدل‌های مدیریت اتاق‌ها
ROOM_MANAGEMENT_MODELS = [
    RoomAssignment,      # تخصیص اتاق به مهمانان
    RoomStatusChange,    # تاریخچه تغییر وضعیت اتاق‌ها
    RoomStatusSnapshot   # اسنپ‌شوت وضعیت اتاق‌ها
]

## مدل‌های مالی و پرداخت
FINANCIAL_MODELS = [
    Payment,           # پرداخت‌های مهمانان
    GuestFolio,        # صورت‌حساب مهمان
    FolioTransaction,  # تراکنش‌های صورت‌حساب
    CashierShift       # شیفت‌های صندوق‌دار
]

## مدل‌های خانه‌داری
#HOUSEKEEPING_MODELS = [
#    HousekeepingTask,       # وظایف نظافت
#    HousekeepingChecklist,  # چک‌لیست‌های نظافت
#    HousekeepingSchedule,   # برنامه‌ریزی نظافت
#    LostAndFound           # اشیای گمشده
#]

## مدل‌های تعمیرات و نگهداری
#MAINTENANCE_MODELS = [
#    MaintenanceRequest,        # درخواست‌های تعمیرات
#    MaintenanceWorkOrder,      # دستورکارهای تعمیراتی
#    MaintenanceInventory,      # موجودی قطعات یدکی
#    PreventiveMaintenance      # نگهداری پیشگیرانه
#]

## مدل‌های مدیریت پرسنل
STAFF_MANAGEMENT_MODELS = [
    Staff,              # اطلاعات پرسنل
    User,               # کاربران سیستم
    UserActivityLog     # لاگ فعالیت‌های کاربران
]

## مدل‌های اطلاع‌رسانی
NOTIFICATION_MODELS = [
    Notification,   # اطلاعیه‌ها و اعلان‌ها
    SyncRecord      # رکوردهای همگام‌سازی
]

## مدل‌های گزارش‌گیری
REPORTING_MODELS = [
    DailyReport,        # گزارش روزانه
    DailyReportDetail   # جزئیات گزارش روزانه
]

# لیست کامل تمام مدل‌های بخش پذیرش
ALL_RECEPTION_MODELS = (
    GUEST_MANAGEMENT_MODELS + ROOM_MANAGEMENT_MODELS + FINANCIAL_MODELS +
    STAFF_MANAGEMENT_MODELS + NOTIFICATION_MODELS + REPORTING_MODELS
)

# دیکشنری نگاشت نام مدل به کلاس
MODEL_CLASSES = {cls.__name__: cls for cls in ALL_RECEPTION_MODELS}

def get_reception_models():
    """
    دریافت تمام مدل‌های بخش پذیرش

    Returns:
        list: لیست تمام کلاس‌های مدل بخش پذیرش
    """
    return ALL_RECEPTION_MODELS

def get_model_by_category(category: str):
    """
    دریافت مدل‌های یک دسته خاص

    Args:
        category (str): دسته مدل‌ها
            ['guest', 'room', 'financial', 'housekeeping',
             'maintenance', 'staff', 'notification', 'reporting']

    Returns:
        list: لیست مدل‌های دسته مورد نظر

    Raises:
        ValueError: اگر دسته نامعتبر باشد
    """
    category_map = {
        'guest': GUEST_MANAGEMENT_MODELS,
        'room': ROOM_MANAGEMENT_MODELS,
        'financial': FINANCIAL_MODELS,
#        'housekeeping': HOUSEKEEPING_MODELS,
#        'maintenance': MAINTENANCE_MODELS,
        'staff': STAFF_MANAGEMENT_MODELS,
        'notification': NOTIFICATION_MODELS,
        'reporting': REPORTING_MODELS
    }

    if category not in category_map:
        raise ValueError(f"دسته '{category}' نامعتبر است. دسته‌های مجاز: {list(category_map.keys())}")

    return category_map[category]

def initialize_models():
    """
    مقداردهی اولیه مدل‌ها
    این تابع می‌تواند برای ثبت مدل‌ها در سیستم استفاده شود
    """
    print(f"✅ مدل‌های بخش پذیرش مقداردهی شدند: {len(ALL_RECEPTION_MODELS)} مدل")

    # نمایش اطلاعات مدل‌ها
    for category, models in [
        ('مهمانان', GUEST_MANAGEMENT_MODELS),
        ('اتاق‌ها', ROOM_MANAGEMENT_MODELS),
        ('مالی', FINANCIAL_MODELS),
#        ('خانه‌داری', HOUSEKEEPING_MODELS),
#        ('تعمیرات', MAINTENANCE_MODELS),
        ('پرسنل', STAFF_MANAGEMENT_MODELS),
        ('اطلاع‌رسانی', NOTIFICATION_MODELS),
        ('گزارش‌گیری', REPORTING_MODELS)
    ]:
        print(f"   • {category}: {len(models)} مدل")

    return ALL_RECEPTION_MODELS

# مقداردهی اولیه هنگام import
if __name__ != "__main__":
    initialize_models()
