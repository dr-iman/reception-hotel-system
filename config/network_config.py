# config/network_config.py
"""
تنظیمات شبکه و API endpoints
"""

import os
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class APIConfig:
    """تنظیمات API endpoints"""

    # سیستم رزرواسیون
    reservation_base_url: str = os.getenv('RESERVATION_API_URL', 'https://reservation-api.hotel.com')
    reservation_timeout: int = int(os.getenv('RESERVATION_TIMEOUT', '30'))
    reservation_retry_attempts: int = int(os.getenv('RESERVATION_RETRY_ATTEMPTS', '3'))

    # سرویس‌های خارجی
    payment_gateway_url: str = os.getenv('PAYMENT_GATEWAY_URL', 'https://pos-api.example.com')
    sms_service_url: str = os.getenv('SMS_SERVICE_URL', 'https://sms-api.example.com')
    email_service_url: str = os.getenv('EMAIL_SERVICE_URL', 'https://email-api.example.com')

    # تنظیمات عمومی
    default_timeout: int = int(os.getenv('API_DEFAULT_TIMEOUT', '30'))
    enable_ssl_verify: bool = os.getenv('API_SSL_VERIFY', 'True').lower() == 'true'

    @property
    def reservation_endpoints(self) -> Dict[str, str]:
        """Endpointهای سیستم رزرواسیون"""
        return {
            'guest_arrivals': f"{self.reservation_base_url}/api/v1/arrivals",
            'guest_departures': f"{self.reservation_base_url}/api/v1/departures",
            'room_status': f"{self.reservation_base_url}/api/v1/rooms/status",
            'reservation_details': f"{self.reservation_base_url}/api/v1/reservations",
            'sync_status': f"{self.reservation_base_url}/api/v1/sync/status"
        }

    def get_headers(self, service: str = 'default') -> Dict[str, str]:
        """دریافت headers برای API calls"""
        base_headers = {
            'User-Agent': f'HotelReceptionSystem/{os.getenv("VERSION", "1.0.0")}',
            'Content-Type': 'application/json'
        }

        service_headers = {
            'reservation': {
                'X-API-Key': os.getenv('RESERVATION_API_KEY', ''),
                'X-Hotel-ID': os.getenv('HOTEL_ID', '1')
            },
            'payment': {
                'Authorization': f'Bearer {os.getenv("PAYMENT_API_TOKEN", "")}'
            }
        }

        base_headers.update(service_headers.get(service, {}))
        return base_headers

@dataclass
class NetworkConfig:
    """تنظیمات شبکه"""

    # تنظیمات اتصال
    max_connections: int = int(os.getenv('NETWORK_MAX_CONNECTIONS', '100'))
    keep_alive: bool = os.getenv('NETWORK_KEEP_ALIVE', 'True').lower() == 'true'
    retry_backoff_factor: float = float(os.getenv('NETWORK_BACKOFF_FACTOR', '0.5'))

    # تنظیمات امنیتی
    enable_firewall: bool = os.getenv('NETWORK_FIREWALL', 'True').lower() == 'true'
    allowed_ips: List[str] = os.getenv('ALLOWED_IPS', '127.0.0.1,::1').split(',')

    # تنظیمات monitoring
    connection_timeout: int = int(os.getenv('CONNECTION_TIMEOUT', '10'))
    read_timeout: int = int(os.getenv('READ_TIMEOUT', '30'))

    def is_ip_allowed(self, ip: str) -> bool:
        """بررسی مجاز بودن IP"""
        return ip in self.allowed_ips or '0.0.0.0' in self.allowed_ips

# ایجاد instance جهانی
api_config = APIConfig()
network_config = NetworkConfig()
