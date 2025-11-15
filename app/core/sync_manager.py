# app/core/sync_manager.py
"""
مدیریت همگام‌سازی با سیستم رزرواسیون
"""

import threading
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from config import config, sync_config, channel_config
from app.core.database import get_redis

logger = logging.getLogger(__name__)

class SyncManager:
    """مدیریت پیشرفته همگام‌سازی با سیستم رزرواسیون"""

    def __init__(self):
        self.redis = get_redis()
        self.is_running = False
        self.sync_thread = None
        self.event_thread = None
        self.last_sync = None

    def start_sync(self):
        """شروع همگام‌سازی"""
        if self.is_running:
            return

        self.is_running = True

        # شروع همگام‌سازی دوره‌ای
        self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self.sync_thread.start()

        # شروع گوش دادن به رویدادها
        self.event_thread = threading.Thread(target=self._event_listener_worker, daemon=True)
        self.event_thread.start()

        # برنامه‌ریزی همگام‌سازی روزانه
        self._schedule_daily_sync()

        logger.info("🔄 سرویس همگام‌سازی با سیستم رزرواسیون شروع شد")

    def stop_sync(self):
        """توقف همگام‌سازی"""
        self.is_running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        if self.event_thread:
            self.event_thread.join(timeout=5)
        logger.info("⏹️ سرویس همگام‌سازی متوقف شد")

    def _sync_worker(self):
        """کارگر همگام‌سازی دوره‌ای"""
        while self.is_running:
            try:
                self.sync_guest_arrivals()
                self.sync_guest_departures()
                self.sync_room_status()
                self.sync_payment_data()

                self.last_sync = datetime.now()
                logger.debug("✅ همگام‌سازی دوره‌ای انجام شد")

                time.sleep(sync_config.sync_interval)

            except Exception as e:
                logger.error(f"❌ خطا در همگام‌سازی دوره‌ای: {e}")
                time.sleep(sync_config.sync_interval * 2)

    def _event_listener_worker(self):
        """گوش دادن به رویدادهای Real-time"""
        try:
            pubsub = self.redis.pubsub()

            # subscribe به کانال‌های مهم
            channels = [
                channel_config.reservation_updates_channel,
                channel_config.guest_arrivals_channel,
                channel_config.guest_departures_channel
            ]

            pubsub.subscribe(channels)

            for message in pubsub.listen():
                if not self.is_running:
                    break

                if message['type'] == 'message':
                    self._handle_sync_event(message)

        except Exception as e:
            logger.error(f"❌ خطا در گوش دادن به رویدادها: {e}")

    def _handle_sync_event(self, message):
        """مدیریت رویدادهای همگام‌سازی"""
        try:
            event_data = json.loads(message['data'])
            event_type = event_data.get('type')
            channel = message['channel']

            if channel == channel_config.guest_arrivals_channel:
                self._process_guest_arrival(event_data)
            elif channel == channel_config.guest_departures_channel:
                self._process_guest_departure(event_data)
            elif channel == channel_config.reservation_updates_channel:
                self._process_reservation_update(event_data)

        except Exception as e:
            logger.error(f"❌ خطا در مدیریت رویداد همگام‌سازی: {e}")

    def _process_guest_arrival(self, event_data):
        """پردازش اطلاعات مهمانان ورودی"""
        try:
            from app.services.reception.guest_service import GuestService

            guest_data = event_data.get('guest_data', {})
            reservation_data = event_data.get('reservation_data', {})

            # ثبت مهمان در سیستم پذیرش
            result = GuestService.register_guest_from_reservation(guest_data, reservation_data)

            if result['success']:
                logger.info(f"✅ مهمان جدید ثبت شد: {guest_data.get('full_name')}")

                # ارسال notification به پذیرش
                self._send_arrival_notification(guest_data, reservation_data)
            else:
                logger.error(f"❌ خطا در ثبت مهمان: {result['message']}")

        except Exception as e:
            logger.error(f"❌ خطا در پردازش اطلاعات مهمان ورودی: {e}")

    def _process_guest_departure(self, event_data):
        """پردازش اطلاعات مهمانان خروجی"""
        try:
            from app.services.reception.guest_service import GuestService

            guest_data = event_data.get('guest_data', {})
            stay_data = event_data.get('stay_data', {})

            # به‌روزرسانی وضعیت مهمان
            result = GuestService.update_guest_departure(guest_data, stay_data)

            if result['success']:
                logger.info(f"✅ وضعیت خروج مهمان به‌روزرسانی شد: {guest_data.get('full_name')}")

                # ایجاد وظیفه نظافت
                self._create_cleaning_task(stay_data)
            else:
                logger.error(f"❌ خطا در به‌روزرسانی وضعیت خروج: {result['message']}")

        except Exception as e:
            logger.error(f"❌ خطا در پردازش اطلاعات مهمان خروجی: {e}")

    def _process_reservation_update(self, event_data):
        """پردازش بروزرسانی رزرو"""
        try:
            update_type = event_data.get('update_type')
            reservation_data = event_data.get('reservation_data', {})

            if update_type == 'cancelled':
                self._handle_reservation_cancellation(reservation_data)
            elif update_type == 'modified':
                self._handle_reservation_modification(reservation_data)

        except Exception as e:
            logger.error(f"❌ خطا در پردازش بروزرسانی رزرو: {e}")

    def _send_arrival_notification(self, guest_data, reservation_data):
        """ارسال notification ورود مهمان"""
        try:
            notification_data = {
                'type': 'guest_arrival',
                'title': 'ورود مهمان جدید',
                'message': f"مهمان {guest_data.get('full_name')} برای تاریخ {reservation_data.get('check_in_date')} رزرو شده است",
                'guest_data': guest_data,
                'reservation_data': reservation_data,
                'timestamp': datetime.now().isoformat()
            }

            self.redis.publish(channel_config.notifications, json.dumps(notification_data))

        except Exception as e:
            logger.error(f"❌ خطا در ارسال notification: {e}")

    def _create_cleaning_task(self, stay_data):
        """ایجاد وظیفه نظافت پس از خروج مهمان"""
        try:
            from app.services.reception.housekeeping_service import HousekeepingService

            room_id = stay_data.get('room_id')
            check_out_date = stay_data.get('check_out_date')

            if room_id and check_out_date:
                HousekeepingService.create_cleaning_task(
                    room_id=room_id,
                    task_type='checkout_cleaning',
                    scheduled_time=datetime.now() + timedelta(minutes=30),  # 30 دقیقه بعد
                    priority='high'
                )
                logger.info(f"🧹 وظیفه نظافت برای اتاق {room_id} ایجاد شد")

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد وظیفه نظافت: {e}")

    def _schedule_daily_sync(self):
        """برنامه‌ریزی همگام‌سازی روزانه"""
        try:
            # محاسبه زمان تا ساعت ۱۲ شب
            now = datetime.now()
            target_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if now >= target_time:
                target_time += timedelta(days=1)

            delay = (target_time - now).total_seconds()

            # ایجاد تایمر برای همگام‌سازی روزانه
            daily_timer = threading.Timer(delay, self._perform_daily_sync)
            daily_timer.daemon = True
            daily_timer.start()

            logger.info(f"⏰ همگام‌سازی روزانه برای ساعت ۱۲ شب برنامه‌ریزی شد")

        except Exception as e:
            logger.error(f"❌ خطا در برنامه‌ریزی همگام‌سازی روزانه: {e}")

    def _perform_daily_sync(self):
        """انجام همگام‌سازی روزانه"""
        try:
            logger.info("🔄 شروع همگام‌سازی روزانه با سیستم رزرواسیون")

            # همگام‌سازی مهمانان فردا
            self.sync_tomorrows_guests()

            # برنامه‌ریزی مجدد برای فردا
            self._schedule_daily_sync()

            logger.info("✅ همگام‌سازی روزانه انجام شد")

        except Exception as e:
            logger.error(f"❌ خطا در همگام‌سازی روزانه: {e}")

    def sync_guest_arrivals(self):
        """همگام‌سازی مهمانان ورودی"""
        # پیاده‌سازی همگام‌سازی با API سیستم رزرواسیون
        pass

    def sync_guest_departures(self):
        """همگام‌سازی مهمانان خروجی"""
        # پیاده‌سازی همگام‌سازی با API سیستم رزرواسیون
        pass

    def sync_room_status(self):
        """همگام‌سازی وضعیت اتاق‌ها"""
        # پیاده‌سازی همگام‌سازی وضعیت اتاق‌ها
        pass

    def sync_payment_data(self):
        """همگام‌سازی داده‌های پرداخت"""
        # پیاده‌سازی همگام‌سازی پرداخت‌ها
        pass

    def sync_tomorrows_guests(self):
        """همگام‌سازی مهمانان فردا"""
        try:
            from app.services.reception.guest_service import GuestService

            tomorrow = datetime.now() + timedelta(days=1)
            result = GuestService.sync_tomorrows_arrivals(tomorrow.date())

            if result['success']:
                logger.info(f"✅ همگام‌سازی {result['count']} مهمان فردا انجام شد")
            else:
                logger.error(f"❌ خطا در همگام‌سازی مهمانان فردا: {result['message']}")

        except Exception as e:
            logger.error(f"❌ خطا در همگام‌سازی مهمانان فردا: {e}")

    def get_sync_status(self) -> Dict[str, Any]:
        """دریافت وضعیت همگام‌سازی"""
        return {
            'is_running': self.is_running,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'channels_subscribed': [
                channel_config.reservation_updates_channel,
                channel_config.guest_arrivals_channel,
                channel_config.guest_departures_channel
            ]
        }

# ایجاد instance جهانی
sync_manager = SyncManager()
