# config/app_config.py
"""
پیکربندی اصلی برنامه سیستم پذیرش هتل
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
from pathlib import Path

@dataclass
class AppConfig:
    """تنظیمات اصلی برنامه"""

    # اطلاعات برنامه
    app_name: str = "سیستم پذیرش هتل آراد"
    version: str = "1.0.0"
    company_name: str = "هتل آراد"

    # تنظیمات فایل‌ها
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    log_dir: Path = data_dir / "logs"
    backup_dir: Path = data_dir / "backups"
    export_dir: Path = data_dir / "exports"

    # تنظیمات UI
    language: str = "fa"
    theme: str = "default"
    enable_animations: bool = os.getenv('ENABLE_ANIMATIONS', 'True').lower() == 'true'
    auto_save_interval: int = int(os.getenv('AUTO_SAVE_INTERVAL', '300'))  # 5 minutes

    # تنظیمات امنیتی
    session_timeout: int = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hour
    max_login_attempts: int = int(os.getenv('MAX_LOGIN_ATTEMPTS', '3'))
    password_min_length: int = int(os.getenv('PASSWORD_MIN_LENGTH', '8'))

    # تنظیمات گزارش‌گیری
    auto_generate_reports: bool = os.getenv('AUTO_GENERATE_REPORTS', 'True').lower() == 'true'
    report_retention_days: int = int(os.getenv('REPORT_RETENTION_DAYS', '90'))

    def __post_init__(self):
        """ایجاد دایرکتوری‌های مورد نیاز"""
        self._create_directories()

    def _create_directories(self):
        """ایجاد دایرکتوری‌های ضروری"""
        directories = [self.data_dir, self.log_dir, self.backup_dir, self.export_dir]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            'app_name': self.app_name,
            'version': self.version,
            'company_name': self.company_name,
            'base_dir': str(self.base_dir),
            'language': self.language,
            'theme': self.theme
        }

# ایجاد instance جهانی
app_config = AppConfig()
