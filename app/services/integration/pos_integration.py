# app/services/integration/pos_integration.py
"""
سرویس یکپارچه‌سازی با دستگاه‌های کارت‌خوان (POS)
"""

import logging
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from app.core.payment_processor import POSPaymentGateway
from config import config

logger = logging.getLogger(__name__)

class POSIntegrationService:
    """سرویس یکپارچه‌سازی با دستگاه‌های کارت‌خوان"""

    @staticmethod
    def process_pos_payment(amount: Decimal, card_data: Dict,
                          description: str = "پرداخت هتل") -> Dict[str, Any]:
        """پردازش پرداخت از طریق کارت‌خوان"""
        try:
            logger.info(f"💳 شروع پردازش پرداخت POS: {amount} تومان")

            # استفاده از پردازشگر پرداخت اصلی
            pos_gateway = POSPaymentGateway()
            result = pos_gateway.process_payment(amount, card_data, description)

            if result['success']:
                logger.info(f"✅ پرداخت POS موفق: {result.get('transaction_id')}")

                # ذخیره لاگ پرداخت
                POSIntegrationService._log_pos_transaction(result, 'success')
            else:
                logger.error(f"❌ پرداخت POS ناموفق: {result.get('error')}")
                POSIntegrationService._log_pos_transaction(result, 'failed')

            return result

        except Exception as e:
            logger.error(f"❌ خطا در پردازش پرداخت POS: {e}")

            error_result = {
                'success': False,
                'error': str(e),
                'error_code': 'POS_PROCESSING_ERROR'
            }

            POSIntegrationService._log_pos_transaction(error_result, 'error')
            return error_result

    @staticmethod
    def refund_pos_payment(transaction_id: str, amount: Decimal) -> Dict[str, Any]:
        """عودت پرداخت از طریق کارت‌خوان"""
        try:
            logger.info(f"🔄 شروع عودت پرداخت POS: {transaction_id} - {amount} تومان")

            pos_gateway = POSPaymentGateway()
            result = pos_gateway.refund_payment(transaction_id, amount)

            if result['success']:
                logger.info(f"✅ عودت POS موفق: {result.get('refund_id')}")
                POSIntegrationService._log_pos_transaction(result, 'refund_success')
            else:
                logger.error(f"❌ عودت POS ناموفق: {result.get('error')}")
                POSIntegrationService._log_pos_transaction(result, 'refund_failed')

            return result

        except Exception as e:
            logger.error(f"❌ خطا در عودت پرداخت POS: {e}")

            error_result = {
                'success': False,
                'error': str(e),
                'error_code': 'POS_REFUND_ERROR'
            }

            POSIntegrationService._log_pos_transaction(error_result, 'refund_error')
            return error_result

    @staticmethod
    def get_pos_status() -> Dict[str, Any]:
        """بررسی وضعیت اتصال به دستگاه کارت‌خوان"""
        try:
            pos_gateway = POSPaymentGateway()

            # تست اتصال
            test_result = pos_gateway.verify_payment("test_connection")

            status_info = {
                'terminal_id': pos_gateway.terminal_id,
                'merchant_id': pos_gateway.merchant_id,
                'test_mode': pos_gateway.test_mode,
                'connection_status': 'connected' if test_result['success'] else 'disconnected',
                'last_check': datetime.now().isoformat()
            }

            return {
                'success': True,
                'status': status_info
            }

        except Exception as e:
            logger.error(f"❌ خطا در بررسی وضعیت POS: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'POS_STATUS_ERROR'
            }

    @staticmethod
    def get_pos_transactions(start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """دریافت تاریخچه تراکنش‌های POS"""
        try:
            # در نسخه واقعی، اینجا با API دستگاه کارت‌خوان ارتباط برقرار می‌شود
            # این یک پیاده‌سازی نمونه است

            if not start_date:
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.now()

            # شبیه‌سازی داده‌های نمونه
            sample_transactions = [
                {
                    'transaction_id': 'TXN_001',
                    'amount': 1500000.0,
                    'card_number': '****1234',
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'sale'
                },
                {
                    'transaction_id': 'TXN_002',
                    'amount': 2500000.0,
                    'card_number': '****5678',
                    'status': 'completed',
                    'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
                    'type': 'sale'
                }
            ]

            return {
                'success': True,
                'transactions': sample_transactions,
                'count': len(sample_transactions),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت تاریخچه تراکنش‌ها: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'POS_TRANSACTIONS_ERROR'
            }

    @staticmethod
    def reconfigure_pos_terminal(new_config: Dict) -> Dict[str, Any]:
        """پیکربندی مجدد ترمینال POS"""
        try:
            logger.info("⚙️ شروع پیکربندی مجدد ترمینال POS")

            # اعتبارسنجی تنظیمات
            validation_result = POSIntegrationService._validate_pos_config(new_config)
            if not validation_result['success']:
                return validation_result

            # در نسخه واقعی، اینجا تنظیمات به دستگاه POS ارسال می‌شود
            # این یک پیاده‌سازی نمونه است

            config_update = {
                'terminal_id': new_config.get('terminal_id'),
                'merchant_id': new_config.get('merchant_id'),
                'base_url': new_config.get('base_url'),
                'timeout': new_config.get('timeout', 30),
                'updated_at': datetime.now().isoformat()
            }

            logger.info("✅ پیکربندی ترمینال POS به‌روزرسانی شد")

            return {
                'success': True,
                'config': config_update,
                'message': 'پیکربندی ترمینال با موفقیت به‌روزرسانی شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در پیکربندی مجدد ترمینال: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'POS_RECONFIGURATION_ERROR'
            }

    # متدهای کمکی خصوصی
    @staticmethod
    def _log_pos_transaction(transaction_data: Dict, transaction_type: str):
        """ذخیره لاگ تراکنش POS"""
        try:
            # در نسخه واقعی، اینجا لاگ در دیتابیس ذخیره می‌شود
            log_entry = {
                'type': transaction_type,
                'data': transaction_data,
                'timestamp': datetime.now().isoformat(),
                'terminal_id': getattr(POSPaymentGateway(), 'terminal_id', 'unknown')
            }

            # ذخیره در Redis برای دسترسی سریع
            redis_client = get_redis()
            redis_client.lpush('pos_transaction_logs', json.dumps(log_entry))
            redis_client.ltrim('pos_transaction_logs', 0, 999)  # نگهداری 1000 لاگ آخر

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره لاگ تراکنش POS: {e}")

    @staticmethod
    def _validate_pos_config(config_data: Dict) -> Dict[str, Any]:
        """اعتبارسنجی تنظیمات POS"""
        required_fields = ['terminal_id', 'merchant_id', 'base_url']

        for field in required_fields:
            if not config_data.get(field):
                return {
                    'success': False,
                    'error': f'فیلد اجباری {field} ارائه نشده است',
                    'error_code': 'MISSING_REQUIRED_FIELD'
                }

        # اعتبارسنجی فرمت
        if not config_data['base_url'].startswith(('http://', 'https://')):
            return {
                'success': False,
                'error': 'آدرس پایه باید با http:// یا https:// شروع شود',
                'error_code': 'INVALID_BASE_URL'
            }

        return {'success': True}
