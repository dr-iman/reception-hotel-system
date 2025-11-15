# app/services/sync/reservation_sync.py
"""
سرویس همگام‌سازی پیشرفته با سیستم رزرواسیون
"""

import logging
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.database import db_session, get_redis
from app.models.reception.guest_models import Guest, Stay, Companion
from app.models.reception.room_status_models import RoomAssignment
from app.models.reception.payment_models import GuestFolio
from config import config

logger = logging.getLogger(__name__)

class ReservationSyncService:
    """سرویس همگام‌سازی با سیستم رزرواسیون"""

    @staticmethod
    def sync_guest_arrivals(sync_date: date = None) -> Dict[str, Any]:
        """همگام‌سازی مهمانان ورودی"""
        try:
            target_date = sync_date or date.today()
            logger.info(f"🔄 شروع همگام‌سازی مهمانان ورودی برای تاریخ: {target_date}")

            # دریافت داده از API سیستم رزرواسیون
            arrivals_data = ReservationSyncService._fetch_arrivals_from_reservation_system(target_date)

            if not arrivals_data.get('success'):
                return arrivals_data

            processed_count = 0
            errors = []

            for arrival in arrivals_data.get('arrivals', []):
                try:
                    # ثبت مهمان در سیستم پذیرش
                    result = ReservationSyncService._process_single_arrival(arrival)
                    if result['success']:
                        processed_count += 1
                    else:
                        errors.append({
                            'reservation_id': arrival.get('reservation_id'),
                            'error': result.get('error')
                        })

                except Exception as e:
                    errors.append({
                        'reservation_id': arrival.get('reservation_id'),
                        'error': str(e)
                    })
                    logger.error(f"❌ خطا در پردازش رزرو {arrival.get('reservation_id')}: {e}")

            # ارسال گزارش همگام‌سازی
            ReservationSyncService._send_sync_report('arrivals', target_date, processed_count, errors)

            logger.info(f"✅ همگام‌سازی مهمانان ورودی انجام شد: {processed_count} رزرو پردازش شد")

            return {
                'success': True,
                'sync_type': 'guest_arrivals',
                'sync_date': target_date,
                'processed_count': processed_count,
                'error_count': len(errors),
                'errors': errors,
                'message': f'همگام‌سازی {processed_count} رزرو با {len(errors)} خطا انجام شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در همگام‌سازی مهمانان ورودی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'ARRIVALS_SYNC_ERROR'
            }

    @staticmethod
    def sync_guest_departures(sync_date: date = None) -> Dict[str, Any]:
        """همگام‌سازی مهمانان خروجی"""
        try:
            target_date = sync_date or date.today()
            logger.info(f"🔄 شروع همگام‌سازی مهمانان خروجی برای تاریخ: {target_date}")

            # دریافت داده از API سیستم رزرواسیون
            departures_data = ReservationSyncService._fetch_departures_from_reservation_system(target_date)

            if not departures_data.get('success'):
                return departures_data

            processed_count = 0
            errors = []

            for departure in departures_data.get('departures', []):
                try:
                    # به‌روزرسانی وضعیت خروج
                    result = ReservationSyncService._process_single_departure(departure)
                    if result['success']:
                        processed_count += 1
                    else:
                        errors.append({
                            'reservation_id': departure.get('reservation_id'),
                            'error': result.get('error')
                        })

                except Exception as e:
                    errors.append({
                        'reservation_id': departure.get('reservation_id'),
                        'error': str(e)
                    })
                    logger.error(f"❌ خطا در پردازش خروج {departure.get('reservation_id')}: {e}")

            logger.info(f"✅ همگام‌سازی مهمانان خروجی انجام شد: {processed_count} رزرو پردازش شد")

            return {
                'success': True,
                'sync_type': 'guest_departures',
                'sync_date': target_date,
                'processed_count': processed_count,
                'error_count': len(errors),
                'errors': errors,
                'message': f'همگام‌سازی {processed_count} خروج با {len(errors)} خطا انجام شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در همگام‌سازی مهمانان خروجی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'DEPARTURES_SYNC_ERROR'
            }

    @staticmethod
    def sync_room_status() -> Dict[str, Any]:
        """همگام‌سازی وضعیت اتاق‌ها"""
        try:
            logger.info("🔄 شروع همگام‌سازی وضعیت اتاق‌ها")

            # دریافت وضعیت اتاق‌ها از سیستم رزرواسیون
            room_status_data = ReservationSyncService._fetch_room_status_from_reservation_system()

            if not room_status_data.get('success'):
                return room_status_data

            updated_count = 0
            errors = []

            for room_status in room_status_data.get('rooms', []):
                try:
                    # به‌روزرسانی وضعیت اتاق
                    result = ReservationSyncService._update_room_status(room_status)
                    if result['success']:
                        updated_count += 1
                    else:
                        errors.append({
                            'room_id': room_status.get('room_id'),
                            'error': result.get('error')
                        })

                except Exception as e:
                    errors.append({
                        'room_id': room_status.get('room_id'),
                        'error': str(e)
                    })
                    logger.error(f"❌ خطا در به‌روزرسانی وضعیت اتاق {room_status.get('room_id')}: {e}")

            logger.info(f"✅ همگام‌سازی وضعیت اتاق‌ها انجام شد: {updated_count} اتاق به‌روزرسانی شد")

            return {
                'success': True,
                'sync_type': 'room_status',
                'updated_count': updated_count,
                'error_count': len(errors),
                'errors': errors,
                'message': f'همگام‌سازی {updated_count} اتاق با {len(errors)} خطا انجام شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در همگام‌سازی وضعیت اتاق‌ها: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'ROOM_STATUS_SYNC_ERROR'
            }

    @staticmethod
    def sync_reservation_changes(since: datetime = None) -> Dict[str, Any]:
        """همگام‌سازی تغییرات رزرو"""
        try:
            if not since:
                since = datetime.now() - timedelta(hours=24)

            logger.info(f"🔄 شروع همگام‌سازی تغییرات رزرو از: {since}")

            # دریافت تغییرات از سیستم رزرواسیون
            changes_data = ReservationSyncService._fetch_reservation_changes(since)

            if not changes_data.get('success'):
                return changes_data

            processed_count = 0
            errors = []

            for change in changes_data.get('changes', []):
                try:
                    # پردازش تغییر
                    result = ReservationSyncService._process_reservation_change(change)
                    if result['success']:
                        processed_count += 1
                    else:
                        errors.append({
                            'reservation_id': change.get('reservation_id'),
                            'change_type': change.get('change_type'),
                            'error': result.get('error')
                        })

                except Exception as e:
                    errors.append({
                        'reservation_id': change.get('reservation_id'),
                        'change_type': change.get('change_type'),
                        'error': str(e)
                    })
                    logger.error(f"❌ خطا در پردازش تغییر رزرو {change.get('reservation_id')}: {e}")

            logger.info(f"✅ همگام‌سازی تغییرات رزرو انجام شد: {processed_count} تغییر پردازش شد")

            return {
                'success': True,
                'sync_type': 'reservation_changes',
                'since': since,
                'processed_count': processed_count,
                'error_count': len(errors),
                'errors': errors,
                'message': f'همگام‌سازی {processed_count} تغییر با {len(errors)} خطا انجام شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در همگام‌سازی تغییرات رزرو: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'RESERVATION_CHANGES_SYNC_ERROR'
            }

    @staticmethod
    def get_sync_status() -> Dict[str, Any]:
        """دریافت وضعیت همگام‌سازی"""
        try:
            redis_client = get_redis()

            last_sync_times = {
                'arrivals': redis_client.get('last_sync_arrivals'),
                'departures': redis_client.get('last_sync_departures'),
                'room_status': redis_client.get('last_sync_room_status'),
                'reservation_changes': redis_client.get('last_sync_changes')
            }

            sync_stats = {
                'today_arrivals_synced': redis_client.get('today_arrivals_count') or 0,
                'today_departures_synced': redis_client.get('today_departures_count') or 0,
                'last_successful_sync': redis_client.get('last_successful_sync')
            }

            return {
                'success': True,
                'last_sync_times': last_sync_times,
                'sync_stats': sync_stats,
                'sync_config': {
                    'auto_sync_enabled': config.sync.auto_sync_enabled,
                    'sync_interval': config.sync.sync_interval,
                    'daily_sync_time': config.sync.daily_sync_time
                }
            }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت وضعیت همگام‌سازی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'SYNC_STATUS_ERROR'
            }

    # متدهای کمکی خصوصی
    @staticmethod
    def _fetch_arrivals_from_reservation_system(target_date: date) -> Dict[str, Any]:
        """دریافت مهمانان ورودی از سیستم رزرواسیون"""
        try:
            endpoint = config.api.reservation_endpoints['guest_arrivals']
            headers = config.api.get_headers('reservation')

            response = requests.get(
                f"{endpoint}?date={target_date}",
                headers=headers,
                timeout=config.api.reservation_timeout
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'arrivals': data.get('arrivals', [])
                }
            else:
                logger.error(f"❌ خطا در دریافت داده از سیستم رزرواسیون: {response.status_code}")
                return {
                    'success': False,
                    'error': f'خطای HTTP {response.status_code}',
                    'error_code': 'RESERVATION_API_ERROR'
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطای شبکه در ارتباط با سیستم رزرواسیون: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NETWORK_ERROR'
            }

    @staticmethod
    def _fetch_departures_from_reservation_system(target_date: date) -> Dict[str, Any]:
        """دریافت مهمانان خروجی از سیستم رزرواسیون"""
        try:
            endpoint = config.api.reservation_endpoints['guest_departures']
            headers = config.api.get_headers('reservation')

            response = requests.get(
                f"{endpoint}?date={target_date}",
                headers=headers,
                timeout=config.api.reservation_timeout
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'departures': data.get('departures', [])
                }
            else:
                logger.error(f"❌ خطا در دریافت داده از سیستم رزرواسیون: {response.status_code}")
                return {
                    'success': False,
                    'error': f'خطای HTTP {response.status_code}',
                    'error_code': 'RESERVATION_API_ERROR'
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطای شبکه در ارتباط با سیستم رزرواسیون: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NETWORK_ERROR'
            }

    @staticmethod
    def _fetch_room_status_from_reservation_system() -> Dict[str, Any]:
        """دریافت وضعیت اتاق‌ها از سیستم رزرواسیون"""
        try:
            endpoint = config.api.reservation_endpoints['room_status']
            headers = config.api.get_headers('reservation')

            response = requests.get(
                endpoint,
                headers=headers,
                timeout=config.api.reservation_timeout
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'rooms': data.get('rooms', [])
                }
            else:
                logger.error(f"❌ خطا در دریافت وضعیت اتاق‌ها: {response.status_code}")
                return {
                    'success': False,
                    'error': f'خطای HTTP {response.status_code}',
                    'error_code': 'RESERVATION_API_ERROR'
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطای شبکه در دریافت وضعیت اتاق‌ها: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NETWORK_ERROR'
            }

    @staticmethod
    def _fetch_reservation_changes(since: datetime) -> Dict[str, Any]:
        """دریافت تغییرات رزرو از سیستم رزرواسیون"""
        try:
            endpoint = f"{config.api.reservation_endpoints['reservation_details']}/changes"
            headers = config.api.get_headers('reservation')

            response = requests.get(
                f"{endpoint}?since={since.isoformat()}",
                headers=headers,
                timeout=config.api.reservation_timeout
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'changes': data.get('changes', [])
                }
            else:
                logger.error(f"❌ خطا در دریافت تغییرات رزرو: {response.status_code}")
                return {
                    'success': False,
                    'error': f'خطای HTTP {response.status_code}',
                    'error_code': 'RESERVATION_API_ERROR'
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ خطای شبکه در دریافت تغییرات رزرو: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'NETWORK_ERROR'
            }

    @staticmethod
    def _process_single_arrival(arrival_data: Dict) -> Dict[str, Any]:
        """پردازش یک رزرو ورودی"""
        from app.services.reception.guest_service import GuestService

        with db_session() as session:
            # بررسی وجود رزرو
            existing_stay = session.query(Stay).filter(
                Stay.reservation_id == arrival_data.get('reservation_id')
            ).first()

            if existing_stay:
                return {
                    'success': True,
                    'action': 'skipped',
                    'reason': 'رزرو قبلاً ثبت شده است'
                }

            # ثبت مهمان جدید
            guest_data = arrival_data.get('guest_data', {})
            reservation_data = arrival_data.get('reservation_data', {})

            result = GuestService.register_guest_from_reservation(guest_data, reservation_data)
            return result

    @staticmethod
    def _process_single_departure(departure_data: Dict) -> Dict[str, Any]:
        """پردازش یک رزرو خروجی"""
        from app.services.reception.guest_service import GuestService

        with db_session() as session:
            # یافتن اقامت مربوطه
            stay = session.query(Stay).filter(
                Stay.reservation_id == departure_data.get('reservation_id')
            ).first()

            if not stay:
                return {
                    'success': False,
                    'error': 'اقامت مربوطه یافت نشد',
                    'error_code': 'STAY_NOT_FOUND'
                }

            # به‌روزرسانی وضعیت خروج
            result = GuestService.update_guest_departure(
                departure_data.get('guest_data', {}),
                departure_data.get('stay_data', {})
            )
            return result

    @staticmethod
    def _update_room_status(room_status: Dict) -> Dict[str, Any]:
        """به‌روزرسانی وضعیت یک اتاق"""
        from app.services.reception.room_service import RoomService

        room_id = room_status.get('room_id')
        new_status = room_status.get('status')

        if not room_id or not new_status:
            return {
                'success': False,
                'error': 'داده‌های وضعیت اتاق ناقص است'
            }

        # به‌روزرسانی وضعیت اتاق
        result = RoomService.update_room_status(
            room_id=room_id,
            new_status=new_status,
            changed_by=0,  # سیستم
            reason='همگام‌سازی با سیستم رزرواسیون'
        )

        return result

    @staticmethod
    def _process_reservation_change(change_data: Dict) -> Dict[str, Any]:
        """پردازش یک تغییر رزرو"""
        change_type = change_data.get('change_type')

        if change_type == 'cancelled':
            return ReservationSyncService._handle_cancellation(change_data)
        elif change_type == 'modified':
            return ReservationSyncService._handle_modification(change_data)
        elif change_type == 'extended':
            return ReservationSyncService._handle_extension(change_data)
        else:
            return {
                'success': False,
                'error': f'نوع تغییر نامعتبر: {change_type}'
            }

    @staticmethod
    def _handle_cancellation(change_data: Dict) -> Dict[str, Any]:
        """مدیریت لغو رزرو"""
        with db_session() as session:
            stay = session.query(Stay).filter(
                Stay.reservation_id == change_data.get('reservation_id')
            ).first()

            if stay:
                stay.status = 'cancelled'
                session.commit()
                return {'success': True, 'action': 'cancelled'}
            else:
                return {'success': True, 'action': 'skipped', 'reason': 'رزرو یافت نشد'}

    @staticmethod
    def _handle_modification(change_data: Dict) -> Dict[str, Any]:
        """مدیریت تغییر رزرو"""
        with db_session() as session:
            stay = session.query(Stay).filter(
                Stay.reservation_id == change_data.get('reservation_id')
            ).first()

            if stay:
                # به‌روزرسانی تاریخ‌ها و اطلاعات
                new_data = change_data.get('new_data', {})
                if 'check_in_date' in new_data:
                    stay.planned_check_in = new_data['check_in_date']
                if 'check_out_date' in new_data:
                    stay.planned_check_out = new_data['check_out_date']
                if 'total_amount' in new_data:
                    stay.total_amount = Decimal(str(new_data['total_amount']))

                session.commit()
                return {'success': True, 'action': 'modified'}
            else:
                return {'success': False, 'error': 'رزرو برای تغییر یافت نشد'}

    @staticmethod
    def _handle_extension(change_data: Dict) -> Dict[str, Any]:
        """مدیریت تمدید رزرو"""
        with db_session() as session:
            stay = session.query(Stay).filter(
                Stay.reservation_id == change_data.get('reservation_id')
            ).first()

            if stay:
                new_check_out = change_data.get('new_check_out_date')
                if new_check_out:
                    stay.planned_check_out = new_check_out
                    session.commit()
                    return {'success': True, 'action': 'extended'}
                else:
                    return {'success': False, 'error': 'تاریخ خروج جدید ارائه نشده'}
            else:
                return {'success': False, 'error': 'رزرو برای تمدید یافت نشد'}

    @staticmethod
    def _send_sync_report(sync_type: str, sync_date: date, processed_count: int, errors: List):
        """ارسال گزارش همگام‌سازی"""
        try:
            redis_client = get_redis()

            report_data = {
                'sync_type': sync_type,
                'sync_date': sync_date.isoformat(),
                'processed_count': processed_count,
                'error_count': len(errors),
                'timestamp': datetime.now().isoformat()
            }

            # ذخیره در Redis برای دسترسی سریع
            redis_client.set(f'last_sync_{sync_type}', datetime.now().isoformat())

            # ارسال از طریق کانال Redis
            redis_client.publish(
                config.channels.system_alerts_channel,
                json.dumps({
                    'type': 'sync_report',
                    'data': report_data
                })
            )

        except Exception as e:
            logger.error(f"❌ خطا در ارسال گزارش همگام‌سازی: {e}")
