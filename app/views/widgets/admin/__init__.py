# app/views/widgets/admin/__init__.py
"""
ویجت‌های مدیریت و پیکربندی سیستم
"""

from .user_management import UserManagementWidget
from .system_settings import SystemSettingsWidget
from .backup_restore import BackupRestoreWidget
from .log_viewer import LogViewerWidget

__all__ = [
    'UserManagementWidget',
    'SystemSettingsWidget',
    'BackupRestoreWidget',
    'LogViewerWidget'
]
