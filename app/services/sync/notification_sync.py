# app/services/sync/notification_sync.py
"""
سرویس همگام‌سازی اطلاع‌رسانی‌ها بین سیستم‌ها
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import db_session, get_redis
from app.models.reception.notification_models import Notification
from config import config

logger = logging.getLogger(__name__)

class NotificationSyncService:
    """سرویس همگام‌سازی اطلاع‌رسانی"""

    @staticmethod
    def send_notification_to_reservation_system(notification_data: Dict) -> Dict[str, Any]:
        """ارسال اطلاع‌رسانی به سیستم رزرواسیون"""
        try:
            # ذخیره در دیتابیس
            with db_session() as session:
                notification = Notification(
                    title=notification_data.get('title', ''),
                    message=notification_data.get('message', ''),
                    notification_type=notification_data.get('type', 'info'),
                    recipient_type=notification_data.get('recipient_type', 'system'),
                    recipient_id=notification_data.get('recipient_id'),
                    sender_type='reception_system',
                    sender_id=0,  # سیستم
                    priority=notification_data.get('priority', 'medium'),
                    status='sent'
                )
                session.add(notification)
                session.flush()

                # ارسال از طریق Redis
                redis_client = get_redis()

                sync_notification = {
                    'id': notification.id,
                    'type': notification_data.get('type'),
                    'title': notification_data.get('title'),
                    'message': notification_data.get('message'),
                    'data': notification_data.get('data', {}),
                    'timestamp': datetime.now().isoformat(),
                    'source_system': 'reception'
                }

                redis_client.publish(
                    config.channels.notification_channel,
                    json.dumps(sync_notification)
                )

                session.commit()

                logger.info(f"📤 اطلاع‌رسانی به سیستم رزرواسیون ارسال شد: {notification.id}")

                return {
                    'success': True,
                    'notification_id': notification.id,
                    'message': 'اطلاع‌رسانی با موفقیت ارسال شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ارسال اطلاع‌رسانی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NOTIFICATION_SEND_ERROR'
            }

    @staticmethod
    def receive_notification_from_reservation_system(notification_data: Dict) -> Dict[str, Any]:
        """دریافت اطلاع‌رسانی از سیستم رزرواسیون"""
        try:
            with db_session() as session:
                notification = Notification(
                    title=notification_data.get('title', ''),
                    message=notification_data.get('message', ''),
                    notification_type=notification_data.get('type', 'info'),
                    recipient_type='reception_system',
                    recipient_id=notification_data.get('recipient_id'),
                    sender_type='reservation_system',
                    sender_id=notification_data.get('sender_id', 0),
                    priority=notification_data.get('priority', 'medium'),
                    status='received',
                    external_id=notification_data.get('id')
                )
                session.add(notification)
                session.commit()

                logger.info(f"📥 اطلاع‌رسانی از سیستم رزرواسیون دریافت شد: {notification.id}")

                # پردازش اطلاع‌رسانی بر اساس نوع
                NotificationSyncService._process_received_notification(notification_data)

                return {
                    'success': True,
                    'notification_id': notification.id,
                    'message': 'اطلاع‌رسانی با موفقیت دریافت و پردازش شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاع‌رسانی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NOTIFICATION_RECEIVE_ERROR'
            }

    @staticmethod
    def sync_notification_status(notification_id: int, new_status: str, read_by: int = None) -> Dict[str, Any]:
        """همگام‌سازی وضعیت اطلاع‌رسانی"""
        try:
            with db_session() as session:
                notification = session.query(Notification).filter(
                    Notification.id == notification_id
                ).first()

                if not notification:
                    return {
                        'success': False,
                        'error': 'اطلاع‌رسانی یافت نشد',
                        'error_code': 'NOTIFICATION_NOT_FOUND'
                    }

                # به‌روزرسانی وضعیت
                notification.status = new_status
                if read_by and new_status == 'read':
                    notification.read_by = read_by
                    notification.read_at = datetime.now()

                session.commit()

                # همگام‌سازی با سیستم رزرواسیون
                if notification.sender_type == 'reception_system':
                    redis_client = get_redis()

                    status_update = {
                        'notification_id': notification.external_id,
                        'new_status': new_status,
                        'read_by': read_by,
                        'timestamp': datetime.now().isoformat()
                    }

                    redis_client.publish(
                        config.channels.notification_channel,
                        json.dumps({
                            'type': 'notification_status_update',
                            'data': status_update
                        })
                    )

                logger.info(f"🔄 وضعیت اطلاع‌رسانی {notification_id} به {new_status} به‌روزرسانی شد")

                return {
                    'success': True,
                    'notification_id': notification_id,
                    'new_status': new_status,
                    'message': 'وضعیت اطلاع‌رسانی با موفقیت به‌روزرسانی شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در به‌روزرسانی وضعیت اطلاع‌رسانی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NOTIFICATION_STATUS_UPDATE_ERROR'
            }

    @staticmethod
    def get_pending_notifications(limit: int = 50) -> Dict[str, Any]:
        """دریافت اطلاع‌رسانی‌های pending"""
        try:
            with db_session() as session:
                notifications = session.query(Notification).filter(
                    Notification.status.in_(['sent', 'received'])
                ).order_by(
                    Notification.created_at.desc()
                ).limit(limit).all()

                notifications_data = [
                    {
                        'id': n.id,
                        'title': n.title,
                        'message': n.message,
                        'type': n.notification_type,
                        'sender_type': n.sender_type,
                        'recipient_type': n.recipient_type,
                        'priority': n.priority,
                        'status': n.status,
                        'created_at': n.created_at,
                        'read_at': n.read_at
                    }
                    for n in notifications
                ]

                return {
                    'success': True,
                    'notifications': notifications_data,
                    'count': len(notifications_data)
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت اطلاع‌رسانی‌ها: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NOTIFICATIONS_RETRIEVAL_ERROR'
            }

    # متدهای کمکی خصوصی
    @staticmethod
    def _process_received_notification(notification_data: Dict):
        """پردازش اطلاع‌رسانی دریافتی"""
        notification_type = notification_data.get('type')

        if notification_type == 'guest_arrival':
            NotificationSyncService._handle_guest_arrival_notification(notification_data)
        elif notification_type == 'guest_departure':
            NotificationSyncService._handle_guest_departure_notification(notification_data)
        elif notification_type == 'reservation_cancellation':
            NotificationSyncService._handle_reservation_cancellation_notification(notification_data)
        elif notification_type == 'system_alert':
            NotificationSyncService._handle_system_alert_notification(notification_data)
        else:
            logger.info(f"📨 اطلاع‌رسانی عمومی دریافت شد: {notification_type}")

    @staticmethod
    def _handle_guest_arrival_notification(notification_data: Dict):
        """مدیریت اطلاع‌رسانی ورود مهمان"""
        from app.services.reception.guest_service import GuestService

        guest_data = notification_data.get('data', {}).get('guest_data', {})
        reservation_data = notification_data.get('data', {}).get('reservation_data', {})

        if guest_data and reservation_data:
            GuestService.register_guest_from_reservation(guest_data, reservation_data)
            logger.info("👤 اطلاع‌رسانی ورود مهمان پردازش شد")

    @staticmethod
    def _handle_guest_departure_notification(notification_data: Dict):
        """مدیریت اطلاع‌رسانی خروج مهمان"""
        from app.services.reception.guest_service import GuestService

        guest_data = notification_data.get('data', {}).get('guest_data', {})
        stay_data = notification_data.get('data', {}).get('stay_data', {})

        if guest_data and stay_data:
            GuestService.update_guest_departure(guest_data, stay_data)
            logger.info("👋 اطلاع‌رسانی خروج مهمان پردازش شد")

    @staticmethod
    def _handle_reservation_cancellation_notification(notification_data: Dict):
        """مدیریت اطلاع‌رسانی لغو رزرو"""
        reservation_id = notification_data.get('data', {}).get('reservation_id')

        if reservation_id:
            with db_session() as session:
                stay = session.query(Stay).filter(
                    Stay.reservation_id == reservation_id
                ).first()

                if stay:
                    stay.status = 'cancelled'
                    session.commit()
                    logger.info(f"❌ رزرو {reservation_id} لغو شد")

    @staticmethod
    def _handle_system_alert_notification(notification_data: Dict):
        """مدیریت اطلاع‌رسانی هشدار سیستم"""
        alert_type = notification_data.get('data', {}).get('alert_type')
        message = notification_data.get('message', '')

        logger.warning(f"🚨 هشدار سیستم از رزرواسیون: {alert_type} - {message}")

        # ارسال به کانال هشدارها برای نمایش در UI
        redis_client = get_redis()
        redis_client.publish(
            config.channels.system_alerts_channel,
            json.dumps({
                'type': 'system_alert',
                'data': notification_data.get('data', {}),
                'message': message,
                'timestamp': datetime.now().isoformat()
            })
        )
