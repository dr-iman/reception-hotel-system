# app/core/notification_service.py
"""
سرویس پیشرفته اطلاع‌رسانی و اعلان‌ها
"""

import logging
import smtplib
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.database import get_redis, db_session
from config import config

logger = logging.getLogger(__name__)

class NotificationService:
    """سرویس اطلاع‌رسانی یکپارچه"""

    def __init__(self):
        self.redis = get_redis()
        self.sms_enabled = config.notification.sms_enabled
        self.email_enabled = config.notification.email_enabled
        self.push_enabled = config.notification.push_enabled

    def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی"""
        try:
            notification_type = notification_data.get('type', 'info')
            priority = notification_data.get('priority', 'normal')
            channels = notification_data.get('channels', ['push'])

            # ذخیره در دیتابیس
            notification_id = self._save_to_database(notification_data)

            results = {}

            # ارسال از طریق کانال‌های مختلف
            if 'push' in channels and self.push_enabled:
                results['push'] = self._send_push_notification(notification_data)

            if 'sms' in channels and self.sms_enabled:
                results['sms'] = self._send_sms_notification(notification_data)

            if 'email' in channels and self.email_enabled:
                results['email'] = self._send_email_notification(notification_data)

            # ارسال از طریق Redis برای سیستم‌های دیگر
            self._publish_to_redis(notification_data)

            # به‌روزرسانی وضعیت در دیتابیس
            self._update_notification_status(notification_id, 'sent', results)

            logger.info(f"📢 اطلاع‌رسانی ارسال شد: {notification_data.get('title')}")

            return {
                'success': True,
                'notification_id': notification_id,
                'channels_sent': results
            }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال اطلاع‌رسانی: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_to_user(self, user_id: int, title: str, message: str,
                    notification_type: str = 'info',
                    channels: List[str] = None) -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی به کاربر خاص"""
        try:
            if channels is None:
                channels = ['push']

            # دریافت اطلاعات کاربر
            user_data = self._get_user_data(user_id)
            if not user_data:
                return {
                    'success': False,
                    'error': 'کاربر یافت نشد'
                }

            notification_data = {
                'title': title,
                'message': message,
                'type': notification_type,
                'priority': 'normal',
                'channels': channels,
                'target_user_id': user_id,
                'target_user_name': user_data.get('full_name'),
                'metadata': {
                    'user_department': user_data.get('department'),
                    'user_role': user_data.get('role')
                }
            }

            return self.send_notification(notification_data)

        except Exception as e:
            logger.error(f"❌ خطا در ارسال اطلاع‌رسانی به کاربر: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_to_department(self, department: str, title: str, message: str,
                          notification_type: str = 'info') -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی به یک بخش"""
        try:
            # دریافت کاربران بخش
            department_users = self._get_department_users(department)

            results = []
            for user in department_users:
                result = self.send_to_user(
                    user_id=user['id'],
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    channels=['push']
                )
                results.append(result)

            success_count = sum(1 for r in results if r['success'])

            return {
                'success': True,
                'sent_count': success_count,
                'total_count': len(results),
                'department': department
            }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال اطلاع‌رسانی به بخش: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def send_to_reservation_system(self, title: str, message: str,
                                  target_user_id: Optional[int] = None) -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی به سیستم رزرواسیون"""
        try:
            notification_data = {
                'title': title,
                'message': message,
                'type': 'info',
                'priority': 'normal',
                'from_system': 'reception',
                'target_system': 'reservation',
                'target_user_id': target_user_id,
                'timestamp': datetime.now().isoformat()
            }

            # ارسال از طریق Redis
            self.redis.publish('inter_system_notifications', str(notification_data))

            logger.info(f"🔄 اطلاع‌رسانی به سیستم رزرواسیون ارسال شد: {title}")

            return {
                'success': True,
                'message': 'اطلاع‌رسانی ارسال شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال اطلاع‌رسانی به سیستم رزرواسیون: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _send_push_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی push"""
        try:
            # در اینجا می‌توانید از سرویس‌های push مانند FCM استفاده کنید
            # برای نمونه، فقط در Redis ذخیره می‌شود

            push_data = {
                'title': notification_data.get('title'),
                'message': notification_data.get('message'),
                'type': notification_data.get('type'),
                'timestamp': datetime.now().isoformat(),
                'target_user_id': notification_data.get('target_user_id')
            }

            # ذخیره در Redis برای مصرف توسط کلاینت‌ها
            self.redis.lpush('push_notifications', str(push_data))

            return {
                'success': True,
                'channel': 'push',
                'sent_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال push: {e}")
            return {
                'success': False,
                'error': str(e),
                'channel': 'push'
            }

    def _send_sms_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی SMS"""
        try:
            if not config.notification.sms_api_key:
                return {
                    'success': False,
                    'error': 'SMS API key تنظیم نشده است',
                    'channel': 'sms'
                }

            # دریافت شماره تلفن کاربر
            user_id = notification_data.get('target_user_id')
            if not user_id:
                return {
                    'success': False,
                    'error': 'کاربر مشخص نشده است',
                    'channel': 'sms'
                }

            user_data = self._get_user_data(user_id)
            phone = user_data.get('phone')

            if not phone:
                return {
                    'success': False,
                    'error': 'شماره تلفن کاربر یافت نشد',
                    'channel': 'sms'
                }

            # ارسال SMS (شبیه‌سازی)
            message = f"{notification_data.get('title')}: {notification_data.get('message')}"

            # در نسخه واقعی، اینجا با API SMS ارتباط برقرار می‌شود
            logger.info(f"📱 SMS ارسال شد به {phone}: {message}")

            return {
                'success': True,
                'channel': 'sms',
                'phone': phone,
                'sent_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال SMS: {e}")
            return {
                'success': False,
                'error': str(e),
                'channel': 'sms'
            }

    def _send_email_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی ایمیل"""
        try:
            user_id = notification_data.get('target_user_id')
            if not user_id:
                return {
                    'success': False,
                    'error': 'کاربر مشخص نشده است',
                    'channel': 'email'
                }

            user_data = self._get_user_data(user_id)
            email = user_data.get('email')

            if not email:
                return {
                    'success': False,
                    'error': 'آدرس ایمیل کاربر یافت نشد',
                    'channel': 'email'
                }

            # ایجاد ایمیل
            msg = MIMEMultipart()
            msg['From'] = 'noreply@hotel.com'
            msg['To'] = email
            msg['Subject'] = notification_data.get('title')

            body = f"""
            {notification_data.get('message')}

            ---
            سیستم پذیرش هتل
            این ایمیل به صورت خودکار ارسال شده است.
            """

            msg.attach(MIMEText(body, 'plain'))

            # در نسخه واقعی، اینجا ایمیل ارسال می‌شود
            logger.info(f"📧 ایمیل ارسال شد به {email}: {notification_data.get('title')}")

            return {
                'success': True,
                'channel': 'email',
                'email': email,
                'sent_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال ایمیل: {e}")
            return {
                'success': False,
                'error': str(e),
                'channel': 'email'
            }

    def _publish_to_redis(self, notification_data: Dict[str, Any]):
        """انتشار اطلاع‌رسانی در Redis"""
        try:
            self.redis.publish('reception_notifications', str(notification_data))
        except Exception as e:
            logger.error(f"❌ خطا در انتشار Redis: {e}")

    def _save_to_database(self, notification_data: Dict[str, Any]) -> int:
        """ذخیره اطلاع‌رسانی در دیتابیس"""
        try:
            from app.models.reception.notification_models import Notification

            with db_session() as session:
                notification = Notification(
                    title=notification_data.get('title'),
                    message=notification_data.get('message'),
                    notification_type=notification_data.get('type', 'info'),
                    category=notification_data.get('category'),
                    from_system='reception',
                    from_user_id=notification_data.get('from_user_id'),
                    to_user_id=notification_data.get('target_user_id'),
                    to_department=notification_data.get('target_department'),
                    priority=notification_data.get('priority', 'normal'),
                    action_required=notification_data.get('action_required', False),
                    action_url=notification_data.get('action_url'),
                    action_label=notification_data.get('action_label')
                )

                session.add(notification)
                session.commit()

                return notification.id

        except Exception as e:
            logger.error(f"❌ خطا در ذخیره اطلاع‌رسانی در دیتابیس: {e}")
            return 0

    def _update_notification_status(self, notification_id: int, status: str, results: Dict):
        """به‌روزرسانی وضعیت اطلاع‌رسانی"""
        try:
            with db_session() as session:
                from app.models.reception.notification_models import Notification

                notification = session.query(Notification).filter(
                    Notification.id == notification_id
                ).first()

                if notification:
                    notification.status = status
                    notification.details = results
                    session.commit()

        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی وضعیت اطلاع‌رسانی: {e}")

    def _get_user_data(self, user_id: int) -> Dict[str, Any]:
        """دریافت اطلاعات کاربر"""
        try:
            with db_session() as session:
                from app.models.reception.staff_models import Staff, User

                user = session.query(User).filter(User.id == user_id).first()
                if user and user.staff:
                    return {
                        'id': user.id,
                        'full_name': f"{user.staff.first_name} {user.staff.last_name}",
                        'phone': user.staff.phone,
                        'email': user.staff.email,
                        'department': user.staff.department,
                        'role': user.role
                    }

                return {}

        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاعات کاربر: {e}")
            return {}

    def _get_department_users(self, department: str) -> List[Dict[str, Any]]:
        """دریافت کاربران یک بخش"""
        try:
            with db_session() as session:
                from app.models.reception.staff_models import Staff, User

                users = session.query(User).join(Staff).filter(
                    Staff.department == department,
                    User.is_active == True
                ).all()

                return [
                    {
                        'id': user.id,
                        'full_name': f"{user.staff.first_name} {user.staff.last_name}",
                        'phone': user.staff.phone,
                        'email': user.staff.email
                    }
                    for user in users
                ]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت کاربران بخش: {e}")
            return []

    def get_unread_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """دریافت اطلاع‌رسانی‌های خوانده نشده کاربر"""
        try:
            with db_session() as session:
                from app.models.reception.notification_models import Notification

                notifications = session.query(Notification).filter(
                    Notification.to_user_id == user_id,
                    Notification.status == 'unread'
                ).order_by(Notification.created_at.desc()).limit(50).all()

                return [
                    {
                        'id': n.id,
                        'title': n.title,
                        'message': n.message,
                        'type': n.notification_type,
                        'category': n.category,
                        'priority': n.priority,
                        'created_at': n.created_at.isoformat(),
                        'action_required': n.action_required,
                        'action_url': n.action_url,
                        'action_label': n.action_label
                    }
                    for n in notifications
                ]

        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاع‌رسانی‌های خوانده نشده: {e}")
            return []

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """علامت‌گذاری اطلاع‌رسانی به عنوان خوانده شده"""
        try:
            with db_session() as session:
                from app.models.reception.notification_models import Notification

                notification = session.query(Notification).filter(
                    Notification.id == notification_id,
                    Notification.to_user_id == user_id
                ).first()

                if notification:
                    notification.status = 'read'
                    notification.read_at = datetime.now()
                    session.commit()
                    return True

                return False

        except Exception as e:
            logger.error(f"❌ خطا در علامت‌گذاری اطلاع‌رسانی: {e}")
            return False

# ایجاد instance جهانی
notification_service = NotificationService()
