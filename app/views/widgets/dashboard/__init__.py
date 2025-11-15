# app/views/widgets/dashboard/__init__.py
"""
ویجت‌های دشبورد سیستم پذیرش
"""

from .main_dashboard import MainDashboard
from .room_status_widget import RoomStatusWidget
from .today_activities import TodayActivitiesWidget

__all__ = [
    'MainDashboard',
    'RoomStatusWidget',
    'TodayActivitiesWidget'
]
