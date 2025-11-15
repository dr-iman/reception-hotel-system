# config/database_config.py
"""
تنظیمات اتصال به دیتابیس
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """تنظیمات دیتابیس PostgreSQL"""

    # تنظیمات اصلی
    host: str = os.getenv('DB_HOST', 'localhost')
    port: int = int(os.getenv('DB_PORT', '5432'))
    name: str = os.getenv('DB_NAME', 'hotel_reception_dev')
    username: str = os.getenv('DB_USERNAME', 'hotel_user')
    password: str = os.getenv('DB_PASSWORD', 'hotel_pass')

    # تنظیمات connection pool
    pool_size: int = int(os.getenv('DB_POOL_SIZE', '20'))
    max_overflow: int = int(os.getenv('DB_MAX_OVERFLOW', '30'))
    pool_timeout: int = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    pool_recycle: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))

    # تنظیمات پیشرفته
    echo: bool = os.getenv('DB_ECHO', 'False').lower() == 'true'
    connect_timeout: int = int(os.getenv('DB_CONNECT_TIMEOUT', '10'))
    statement_timeout: int = int(os.getenv('DB_STATEMENT_TIMEOUT', '30000'))

    @property
    def url(self) -> str:
        """ساخت URL اتصال به دیتابیس"""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"

    def get_connection_params(self) -> dict:
        """دریافت پارامترهای اتصال"""
        return {
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'echo': self.echo,
            'connect_args': {
                'connect_timeout': self.connect_timeout,
                'application_name': f'hotel_reception_{os.getenv("VERSION", "1.0.0")}',
                'options': f'-c statement_timeout={self.statement_timeout}'
            }
        }

@dataclass
class RedisConfig:
    """تنظیمات Redis"""

    host: str = os.getenv('REDIS_HOST', 'localhost')
    port: int = int(os.getenv('REDIS_PORT', '6379'))
    db: int = int(os.getenv('REDIS_DB', '0'))
    password: Optional[str] = os.getenv('REDIS_PASSWORD')

    # تنظیمات اتصال
    socket_connect_timeout: int = int(os.getenv('REDIS_CONNECT_TIMEOUT', '5'))
    socket_timeout: int = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
    retry_on_timeout: bool = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'True').lower() == 'true'
    health_check_interval: int = int(os.getenv('REDIS_HEALTH_CHECK', '30'))

    # تنظیمات pub/sub
    pubsub_timeout: int = int(os.getenv('REDIS_PUBSUB_TIMEOUT', '1'))

    def get_connection_params(self) -> dict:
        """دریافت پارامترهای اتصال Redis"""
        return {
            'host': self.host,
            'port': self.port,
            'db': self.db,
            'password': self.password,
            'socket_connect_timeout': self.socket_connect_timeout,
            'socket_timeout': self.socket_timeout,
            'retry_on_timeout': self.retry_on_timeout,
            'health_check_interval': self.health_check_interval,
            'decode_responses': True
        }

# ایجاد instance جهانی
database_config = DatabaseConfig()
redis_config = RedisConfig()
