# app/views/widgets/room_management/__init__.py
"""
ویجت‌های مدیریت اتاق‌ها
"""

from .room_list_widget import RoomListWidget
from .room_assignment import RoomAssignmentWidget
from .room_status_manager import RoomStatusManager

__all__ = [
    'RoomListWidget',
    'RoomAssignmentWidget',
    'RoomStatusManager'
]
