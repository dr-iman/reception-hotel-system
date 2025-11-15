"""
پکیج تست‌های سیستم پذیرش هتل
نسخه: 1.0
"""

__version__ = "1.0.0"
__author__ = "سیستم پذیرش هتل آراد"
__description__ = "تست‌های جامع سیستم مدیریت پذیرش هتل"

# Import ماژول‌های تست برای دسترسی آسان
from tests.test_core import TestDatabase, TestPaymentProcessor, TestSyncManager
from tests.test_models import TestGuestModels, TestPaymentModels, TestRoomModels
from tests.test_services import TestGuestService, TestPaymentService, TestReportService

__all__ = [
    'TestDatabase',
    'TestPaymentProcessor',
    'TestSyncManager',
    'TestGuestModels',
    'TestPaymentModels',
    'TestRoomModels',
    'TestGuestService',
    'TestPaymentService',
    'TestReportService'
]
