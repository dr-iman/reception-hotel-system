# app/views/widgets/__init__.py
"""
ویجت‌های سیستم پذیرش
"""
from .admin.backup_restore import BackupRestoreWidget
from .admin.log_viewer import LogViewerWidget
from .admin.system_setting import SystemSettingsWidget
from .admin.user_management import UserManagementWidget
from .dashboard.main_dashboard import MainDashboard
from .dashboard.room_status_widget import RoomStatusWidget
from .dashboard.todat_activities import TodayActivitiesWidget
from .guest_management.guest_list_widget import GuestListWidget
from .guest_management.guest_details_widget import GuestDetailsWidget
from .guest_management.check_in_widget import CheckInWidget
from .guest_management.check_out_widget import CheckOutWidget
from .room_management.room_list_widget import RoomListWidget
from .room_management.room_assignment import RoomAssignmentWidget
from .room_management.room_status_manager import RoomStatusManager
from .financial.guest_folio import GuestFolioWidget
from .financial.payment_processing import PaymentProcessingWidget
from .shared.base_widget import BaseWidget, BaseDialog
from .shared.custom_table import CustomTableWidget, TableModel
from .shared.search_bar import SearchWidget
from .shared.date_range_selector import DateRangeSelector
from .shared.loading_widget import LoadingWidget
from .shared.message_box import CustomMessageBox
from .shared.toolbar import ToolBarWidget


__all__ = [
    'BackupRestoreWidget',
    'LogViewerWidget',
    'SystemSettingsWidget',
    'UserManagementWidget',
    'MainDashboard',
    'RoomStatusWidget',
    'TodayActivitiesWidget',
    'GuestListWidget',
    'GuestDetailsWidget',
    'CheckInWidget',
    'CheckOutWidget',
    'RoomListWidget',
    'RoomAssignmentWidget',
    'RoomStatusManager',
    'GuestFolioWidget',
    'PaymentProcessingWidget',
    'BaseWidget',
    'BaseDialog',
    'CustomTableWidget',
    'TableModel',
    'SearchWidget',
    'DateRangeSelector',
    'LoadingWidget',
    'CustomMessageBox',
    'ToolBarWidget'
]
