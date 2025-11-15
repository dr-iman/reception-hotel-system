# config/sync_config.py
"""
پیکربندی همگام‌سازی با سیستم رزرواسیون
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class SyncChannelConfig:
    """پیکربندی کانال‌های همگام‌سازی Redis"""

    channels: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.channels:
            self.channels = {
                'reservation_updates': 'reservation_updates_channel',
                'guest_arrivals': 'guest_arrivals_channel',
                'guest_departures': 'guest_departures_channel',
                'room_status': 'room_status_channel',
                'payment_sync': 'payment_sync_channel',
                'notifications': 'notification_channel',
                'system_alerts': 'system_alerts_channel'
            }

    @property
    def reservation_updates_channel(self) -> str:
        return self.channels['reservation_updates']

    @property
    def guest_arrivals_channel(self) -> str:
        return self.channels['guest_arrivals']

    @property
    def guest_departures_channel(self) -> str:
        return self.channels['guest_departures']

    @property
    def room_status_channel(self) -> str:
        return self.channels['room_status']

    @property
    def payment_sync_channel(self) -> str:
        return self.channels['payment_sync']

    @property
    def notification_channel(self) -> str:
        return self.channels['notifications']

    @property
    def system_alerts_channel(self) -> str:
        return self.channels['system_alerts']

@dataclass
class DataSyncConfig:
    """پیکربندی همگام‌سازی داده‌ها"""

    # تنظیمات همگام‌سازی خودکار
    auto_sync_enabled: bool = os.getenv('AUTO_SYNC_ENABLED', 'True').lower() == 'true'
    sync_interval: int = int(os.getenv('SYNC_INTERVAL', '300'))  # 5 minutes
    daily_sync_time: str = os.getenv('DAILY_SYNC_TIME', '00:00')  # ساعت 12 شب

    # انواع داده‌های قابل همگام‌سازی
    sync_data_types: List[str] = field(default_factory=list)

    # تنظیمات بازیابی
    retry_on_failure: bool = os.getenv('SYNC_RETRY_ON_FAILURE', 'True').lower() == 'true'
    max_retry_attempts: int = int(os.getenv('SYNC_MAX_RETRIES', '3'))
    retry_backoff_factor: float = float(os.getenv('SYNC_BACKOFF_FACTOR', '1.5'))

    # تنظیمات کیفیت سرویس
    enable_compression: bool = os.getenv('SYNC_COMPRESSION', 'True').lower() == 'true'
    batch_size: int = int(os.getenv('SYNC_BATCH_SIZE', '100'))

    def __post_init__(self):
        if not self.sync_data_types:
            self.sync_data_types = [
                'guest_arrivals',
                'guest_departures',
                'room_assignments',
                'payment_status',
                'guest_profiles',
                'reservation_changes',
                'rate_updates'
            ]

    def should_sync(self, data_type: str) -> bool:
        """بررسی是否需要 همگام‌سازی نوع داده"""
        return data_type in self.sync_data_types

    def get_sync_priority(self, data_type: str) -> int:
        """دریافت اولویت همگام‌سازی برای نوع داده"""
        priority_map = {
            'guest_arrivals': 1,
            'guest_departures': 1,
            'reservation_changes': 2,
            'payment_status': 2,
            'room_assignments': 3,
            'guest_profiles': 4,
            'rate_updates': 5
        }
        return priority_map.get(data_type, 10)

# ایجاد instance جهانی
sync_config = DataSyncConfig()
channel_config = SyncChannelConfig()
