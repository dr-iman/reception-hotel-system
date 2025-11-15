# app/services/integration/sms_service.py
"""
سرویس ارسال پیامک به مهمانان و پرسنل
"""

import logging
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import db_session, get_redis
from app.models.reception.guest_models import Guest, Stay
from config import config

logger = logging.getLogger(__name__)

class SMSService:
    """سرویس ارسال پیامک"""

    @staticmethod
    def send_guest_welcome_sms(stay_id: int) -> Dict[str, Any]:
        """ارسال پیامک خوش‌آمدگویی به مهمان"""
        try:
            with db_session() as session:
                stay = session.query(Stay).options(
                    joinedload(Stay.guest)
                ).filter(Stay.id == stay_id).first()

                if not stay or not stay.guest:
                    return {
                        'success': False,
                        'error': 'اطلاعات اقامت یا مهمان یافت نشد',
                        'error_code': 'STAY_NOT_FOUND'
                    }

                guest = stay.guest
                phone_number = guest.phone

                if not phone_number:
                    return {
                        'success': False,
                        'error': 'شماره تلفن مهمان موجود نیست',
                        'error_code': 'PHONE_NUMBER_MISSING'
                    }

                # ایجاد متن پیامک
                message = SMSService._create_welcome_message(guest, stay)

                # ارسال پیامک
                result = SMSService._send_sms(phone_number, message, 'welcome')

                if result['success']:
                    logger.info(f"📱 پیامک خوش‌آمدگویی برای مهمان {guest.first_name} {guest.last_name} ارسال شد")

                    # ذخیره لاگ ارسال
                    SMSService._log_sms_activity(
                        phone_number=phone_number,
                        message_type='welcome',
                        message=message,
                        guest_id=guest.id,
                        stay_id=stay_id,
                        status='sent'
                    )
                else:
                    logger.error(f"❌ خطا در ارسال پیامک خوش‌آمدگویی: {result.get('error')}")
                    SMSService._log_sms_activity(
                        phone_number=phone_number,
                        message_type='welcome',
                        message=message,
                        guest_id=guest.id,
                        stay_id=stay_id,
                        status='failed',
                        error=result.get('error')
                    )

                return result

        except Exception as e:
            logger.error(f"❌ خطا در ارسال پیامک خوش‌آمدگویی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'WELCOME_SMS_ERROR'
            }

    @staticmethod
    def send_checkout_reminder_sms(stay_id: int) -> Dict[str, Any]:
        """ارسال پیامک یادآوری خروج"""
        try:
            with db_session() as session:
                stay = session.query(Stay).options(
                    joinedload(Stay.guest)
                ).filter(Stay.id == stay_id).first()

                if not stay or not stay.guest:
                    return {
                        'success': False,
                        'error': 'اطلاعات اقامت یا مهمان یافت نشد',
                        'error_code': 'STAY_NOT_FOUND'
                    }

                guest = stay.guest
                phone_number = guest.phone

                if not phone_number:
                    return {
                        'success': False,
                        'error': 'شماره تلفن مهمان موجود نیست',
                        'error_code': 'PHONE_NUMBER_MISSING'
                    }

                # ایجاد متن پیامک
                message = SMSService._create_checkout_reminder_message(guest, stay)

                # ارسال پیامک
                result = SMSService._send_sms(phone_number, message, 'checkout_reminder')

                if result['success']:
                    logger.info(f"📱 پیامک یادآوری خروج برای مهمان {guest.first_name} {guest.last_name} ارسال شد")

                    SMSService._log_sms_activity(
                        phone_number=phone_number,
                        message_type='checkout_reminder',
                        message=message,
                        guest_id=guest.id,
                        stay_id=stay_id,
                        status='sent'
                    )
                else:
                    logger.error(f"❌ خطا در ارسال پیامک یادآوری خروج: {result.get('error')}")
                    SMSService._log_sms_activity(
                        phone_number=phone_number,
                        message_type='checkout_reminder',
                        message=message,
                        guest_id=guest.id,
                        stay_id=stay_id,
                        status='failed',
                        error=result.get('error')
                    )

                return result

        except Exception as e:
            logger.error(f"❌ خطا در ارسال پیامک یادآوری خروج: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CHECKOUT_REMINDER_SMS_ERROR'
            }

    @staticmethod
    def send_custom_sms(phone_numbers: List[str], message: str,
                       message_type: str = 'custom') -> Dict[str, Any]:
        """ارسال پیامک سفارشی"""
        try:
            if not phone_numbers:
                return {
                    'success': False,
                    'error': 'لیست شماره تلفن‌ها خالی است',
                    'error_code': 'EMPTY_PHONE_LIST'
                }

            if not message.strip():
                return {
                    'success': False,
                    'error': 'متن پیامک نمی‌تواند خالی باشد',
                    'error_code': 'EMPTY_MESSAGE'
                }

            results = []
            successful_sends = 0

            for phone in phone_numbers:
                # اعتبارسنجی شماره تلفن
                if not SMSService._validate_phone_number(phone):
                    results.append({
                        'phone': phone,
                        'success': False,
                        'error': 'شماره تلفن نامعتبر'
                    })
                    continue

                # ارسال پیامک
                result = SMSService._send_sms(phone, message, message_type)

                if result['success']:
                    successful_sends += 1
                    SMSService._log_sms_activity(
                        phone_number=phone,
                        message_type=message_type,
                        message=message,
                        status='sent'
                    )
                else:
                    SMSService._log_sms_activity(
                        phone_number=phone,
                        message_type=message_type,
                        message=message,
                        status='failed',
                        error=result.get('error')
                    )

                results.append({
                    'phone': phone,
                    'success': result['success'],
                    'message_id': result.get('message_id'),
                    'error': result.get('error')
                })

            logger.info(f"📱 ارسال پیامک سفارشی: {successful_sends}/{len(phone_numbers)} موفق")

            return {
                'success': True,
                'total_recipients': len(phone_numbers),
                'successful_sends': successful_sends,
                'failed_sends': len(phone_numbers) - successful_sends,
                'results': results,
                'message': f'پیامک به {successful_sends} از {len(phone_numbers)} شماره ارسال شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال پیامک سفارشی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CUSTOM_SMS_ERROR'
            }

    @staticmethod
    def get_sms_balance() -> Dict[str, Any]:
        """دریافت موجودی سرویس پیامک"""
        try:
            # در نسخه واقعی، اینجا با API سرویس پیامک ارتباط برقرار می‌شود
            # این یک پیاده‌سازی نمونه است

            # شبیه‌سازی دریافت موجودی
            balance_data = {
                'balance': 1000,  # تعداد پیامک باقیمانده
                'currency': 'IRR',
                'unit_price': 100,  # قیمت هر پیامک
                'last_updated': datetime.now().isoformat()
            }

            return {
                'success': True,
                'balance': balance_data
            }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت موجودی پیامک: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SMS_BALANCE_ERROR'
            }

    @staticmethod
    def get_sms_statistics(start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """دریافت آمار ارسال پیامک"""
        try:
            if not start_date:
                start_date = datetime.now().replace(day=1)  # اول ماه جاری
            if not end_date:
                end_date = datetime.now()

            # در نسخه واقعی، اینجا آمار از دیتابیس خوانده می‌شود
            # این یک پیاده‌سازی نمونه است

            statistics = {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_sent': 150,
                'successful': 142,
                'failed': 8,
                'by_type': {
                    'welcome': 45,
                    'checkout_reminder': 38,
                    'custom': 59
                },
                'success_rate': 94.67
            }

            return {
                'success': True,
                'statistics': statistics
            }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت آمار پیامک: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SMS_STATISTICS_ERROR'
            }

    # متدهای کمکی خصوصی
    @staticmethod
    def _send_sms(phone_number: str, message: str, message_type: str) -> Dict[str, Any]:
        """ارسال پیامک از طریق سرویس پیامک"""
        try:
            # در نسخه واقعی، اینجا با API سرویس پیامک ارتباط برقرار می‌شود
            # این یک پیاده‌سازی نمونه است

            # شبیه‌سازی ارسال پیامک
            if config.environment.get('DEBUG', False):
                logger.info(f"📱 [TEST] پیامک به {phone_number}: {message}")
                return {
                    'success': True,
                    'message_id': f"MSG_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'phone_number': phone_number,
                    'test_mode': True
                }

            # ارسال واقعی
            payload = {
                'phone_number': phone_number,
                'message': message,
                'message_type': message_type,
                'sender': config.app.company_name,
                'api_key': config.sms_api_key  # باید در config تعریف شود
            }

            response = requests.post(
                config.api.sms_service_url,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'message_id': data.get('message_id'),
                    'phone_number': phone_number
                }
            else:
                return {
                    'success': False,
                    'error': f'خطای HTTP {response.status_code}',
                    'error_code': 'SMS_API_ERROR'
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SMS_NETWORK_ERROR'
            }

    @staticmethod
    def _create_welcome_message(guest: Guest, stay: Stay) -> str:
        """ایجاد متن پیامک خوش‌آمدگویی"""
        guest_name = f"{guest.first_name} {guest.last_name}"
        check_in_date = stay.planned_check_in.strftime("%Y/%m/%d")
        check_out_date = stay.planned_check_out.strftime("%Y/%m/%d")

        message = f"""
        مهمان گرامی {guest_name}
        به {config.app.company_name} خوش آمدید!

        تاریخ اقامت: {check_in_date} تا {check_out_date}
        شماره رزرو: {stay.reservation_id}

        برای اطلاعات بیشتر با پذیرش تماس بگیرید.
        {config.app.support_phone}

        با تشکر
        """

        return message.strip()

    @staticmethod
    def _create_checkout_reminder_message(guest: Guest, stay: Stay) -> str:
        """ایجاد متن پیامک یادآوری خروج"""
        guest_name = f"{guest.first_name} {guest.last_name}"
        checkout_time = stay.planned_check_out.strftime("%Y/%m/%d ساعت %H:%M")

        message = f"""
        مهمان گرامی {guest_name}

        یادآوری می‌شود زمان خروج شما:
        {checkout_time}

        لطفاً تا ساعت 12 ظهر اتاق را تخلیه فرمایید.
        برای تمدید اقامت با پذیرش تماس بگیرید.

        {config.app.support_phone}

        با تشکر
        """

        return message.strip()

    @staticmethod
    def _validate_phone_number(phone: str) -> bool:
        """اعتبارسنجی شماره تلفن"""
        # حذف فاصله و کاراکترهای غیرعددی
        cleaned_phone = ''.join(filter(str.isdigit, phone))

        # بررسی فرمت شماره ایران
        if cleaned_phone.startswith('98') and len(cleaned_phone) == 12:
            return True
        elif cleaned_phone.startswith('0') and len(cleaned_phone) == 11:
            return True
        elif cleaned_phone.startswith('+98') and len(cleaned_phone) == 13:
            return True
        else:
            return False

    @staticmethod
    def _log_sms_activity(phone_number: str, message_type: str, message: str,
                         status: str, guest_id: int = None, stay_id: int = None,
                         error: str = None):
        """ذخیره لاگ فعالیت پیامک"""
        try:
            log_entry = {
                'phone_number': phone_number,
                'message_type': message_type,
                'message': message,
                'status': status,
                'guest_id': guest_id,
                'stay_id': stay_id,
                'error': error,
                'timestamp': datetime.now().isoformat()
            }

            # ذخیره در Redis
            redis_client = get_redis()
            redis_client.lpush('sms_activity_logs', json.dumps(log_entry))
            redis_client.ltrim('sms_activity_logs', 0, 999)  # نگهداری 1000 لاگ آخر

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره لاگ پیامک: {e}")
