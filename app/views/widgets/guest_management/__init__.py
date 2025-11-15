# app/views/widgets/guest_manager/__init__.py
"""
ویجت مدیریت مهمانان
"""
from .check_in_widget import CheckInWidget
from .check_out_widget import CheckOutWidget
from .guest_details_widget import GuestDetailsWidget
from .guest_list_widget import GuestListWidget

__all__ = [
 'CheckInWidget',
 'CheckOutWidget',
 'GuestDetailsWidget',
 'GuestListWidget'
]
