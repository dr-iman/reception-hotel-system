# app/core/housekeeping_manager.py
"""
مدیریت خانه‌داری - نسخه ساده شده برای فاز اول
"""

import logging

logger = logging.getLogger(__name__)

class HousekeepingManager:
    """مدیریت ساده خانه‌داری"""

    def __init__(self):
        logger.info("✅ مدیر خانه‌داری ساده شده راه‌اندازی شد")

    def create_cleaning_task(self, *args, **kwargs):
        """ایجاد وظیفه نظافت - نسخه ساده"""
        return {'success': True, 'message': 'سیستم خانه‌داری در حال توسعه'}

# ایجاد instance جهانی
housekeeping_manager = HousekeepingManager()
