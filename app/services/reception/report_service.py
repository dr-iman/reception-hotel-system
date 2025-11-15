# app/services/reception/report_service.py
"""
سرویس گزارش‌گیری جامع و پیشرفته سیستم پذیرش
"""

import logging
import csv
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import func, and_, or_, extract, case
from sqlalchemy.orm import Session, joinedload

from app.core.database import db_session
from app.models.reception.guest_models import Guest, Stay, Companion
from app.models.reception.room_status_models import RoomAssignment, RoomStatusSnapshot
from app.models.reception.payment_models import Payment, GuestFolio, FolioTransaction, CashierShift
from app.models.reception.housekeeping_models import HousekeepingTask
from app.models.reception.maintenance_models import MaintenanceRequest
from config import config
import os

logger = logging.getLogger(__name__)

class ReportService:
    """سرویس گزارش‌گیری جامع سیستم پذیرش"""

    @staticmethod
    def generate_daily_occupancy_report(report_date: date = None) -> Dict[str, Any]:
        """گزارش روزانه اشغال اتاق‌ها"""
        try:
            with db_session() as session:
                target_date = report_date or date.today()

                # آمار کلی
                total_rooms = ReportService._get_total_rooms(session)
                occupied_rooms = ReportService._get_occupied_rooms_count(session, target_date)
                available_rooms = total_rooms - occupied_rooms
                occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0

                # مهمانان امروز
                arrivals_today = session.query(Stay).filter(
                    func.date(Stay.planned_check_in) == target_date,
                    Stay.status.in_(['confirmed', 'checked_in'])
                ).count()

                departures_today = session.query(Stay).filter(
                    func.date(Stay.planned_check_out) == target_date,
                    Stay.status.in_(['checked_in', 'checked_out'])
                ).count()

                # درآمد امروز
                revenue_today = session.query(func.sum(Payment.amount)).filter(
                    func.date(Payment.created_at) == target_date,
                    Payment.status == 'completed'
                ).scalar() or Decimal('0')

                # اتاق‌ها بر اساس نوع
                room_type_stats = ReportService._get_room_type_statistics(session, target_date)

                report_data = {
                    'report_date': target_date,
                    'generated_at': datetime.now(),
                    'summary': {
                        'total_rooms': total_rooms,
                        'occupied_rooms': occupied_rooms,
                        'available_rooms': available_rooms,
                        'occupancy_rate': round(occupancy_rate, 2),
                        'arrivals_today': arrivals_today,
                        'departures_today': departures_today,
                        'revenue_today': float(revenue_today)
                    },
                    'room_type_statistics': room_type_stats,
                    'details': {
                        'arrivals': ReportService._get_todays_arrivals(session, target_date),
                        'departures': ReportService._get_todays_departures(session, target_date),
                        'current_guests': ReportService._get_current_guests(session, target_date)
                    }
                }

                logger.info(f"📊 گزارش روزانه اشغال برای {target_date} ایجاد شد")

                return {
                    'success': True,
                    'report': report_data,
                    'report_type': 'daily_occupancy'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد گزارش روزانه اشغال: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'DAILY_OCCUPANCY_REPORT_ERROR'
            }

    @staticmethod
    def generate_financial_report(start_date: date, end_date: date) -> Dict[str, Any]:
        """گزارش مالی دوره‌ای"""
        try:
            with db_session() as session:
                # درآمد کلی
                total_revenue = session.query(func.sum(Payment.amount)).filter(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                    Payment.status == 'completed'
                ).scalar() or Decimal('0')

                # درآمد بر اساس روش پرداخت
                revenue_by_method = session.query(
                    Payment.payment_method,
                    func.count(Payment.id),
                    func.sum(Payment.amount)
                ).filter(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                    Payment.status == 'completed'
                ).group_by(Payment.payment_method).all()

                # درآمد بر اساس نوع پرداخت
                revenue_by_type = session.query(
                    Payment.payment_type,
                    func.count(Payment.id),
                    func.sum(Payment.amount)
                ).filter(
                    Payment.created_at >= start_date,
                    Payment.created_at <= end_date,
                    Payment.status == 'completed'
                ).group_by(Payment.payment_type).all()

                # تراکنش‌های صورت‌حساب
                folio_transactions = session.query(
                    FolioTransaction.transaction_type,
                    FolioTransaction.category,
                    func.count(FolioTransaction.id),
                    func.sum(FolioTransaction.amount)
                ).filter(
                    FolioTransaction.created_at >= start_date,
                    FolioTransaction.created_at <= end_date
                ).group_by(
                    FolioTransaction.transaction_type,
                    FolioTransaction.category
                ).all()

                # آمار شیفت‌های صندوق
                cashier_shifts = session.query(CashierShift).filter(
                    CashierShift.shift_start >= start_date,
                    CashierShift.shift_start <= end_date,
                    CashierShift.status == 'closed'
                ).all()

                report_data = {
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'generated_at': datetime.now(),
                    'financial_summary': {
                        'total_revenue': float(total_revenue),
                        'total_transactions': sum(count for _, count, _ in revenue_by_method),
                        'average_transaction': float(total_revenue / sum(count for _, count, _ in revenue_by_method)) if revenue_by_method else 0
                    },
                    'revenue_by_payment_method': [
                        {
                            'method': method,
                            'count': count,
                            'amount': float(amount),
                            'percentage': float(amount / total_revenue * 100) if total_revenue > 0 else 0
                        }
                        for method, count, amount in revenue_by_method
                    ],
                    'revenue_by_payment_type': [
                        {
                            'type': payment_type,
                            'count': count,
                            'amount': float(amount)
                        }
                        for payment_type, count, amount in revenue_by_type
                    ],
                    'folio_analysis': [
                        {
                            'transaction_type': trans_type,
                            'category': category,
                            'count': count,
                            'amount': float(amount)
                        }
                        for trans_type, category, count, amount in folio_transactions
                    ],
                    'cashier_performance': [
                        {
                            'shift_id': shift.id,
                            'user_id': shift.user_id,
                            'shift_date': shift.shift_start.date(),
                            'total_amount': float(shift.total_amount),
                            'cash_difference': float(shift.cash_difference),
                            'transaction_count': shift.total_transactions
                        }
                        for shift in cashier_shifts
                    ]
                }

                logger.info(f"💰 گزارش مالی برای دوره {start_date} تا {end_date} ایجاد شد")

                return {
                    'success': True,
                    'report': report_data,
                    'report_type': 'financial'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد گزارش مالی: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'FINANCIAL_REPORT_ERROR'
            }

    @staticmethod
    def generate_guest_analysis_report(period: str = 'month') -> Dict[str, Any]:
        """گزارش تحلیل مهمانان"""
        try:
            with db_session() as session:
                if period == 'month':
                    start_date = date.today().replace(day=1)
                    end_date = date.today()
                elif period == 'quarter':
                    today = date.today()
                    quarter = (today.month - 1) // 3 + 1
                    start_date = date(today.year, 3 * quarter - 2, 1)
                    end_date = today
                else:  # year
                    start_date = date.today().replace(month=1, day=1)
                    end_date = date.today()

                # آمار مهمانان
                total_guests = session.query(Stay).filter(
                    Stay.created_at >= start_date,
                    Stay.created_at <= end_date
                ).count()

                unique_guests = session.query(Stay.guest_id).filter(
                    Stay.created_at >= start_date,
                    Stay.created_at <= end_date
                ).distinct().count()

                # ملیت مهمانان
                guest_nationalities = session.query(
                    Guest.nationality,
                    func.count(Stay.id)
                ).join(Stay, Stay.guest_id == Guest.id).filter(
                    Stay.created_at >= start_date,
                    Stay.created_at <= end_date
                ).group_by(Guest.nationality).all()

                # نوع اقامت
                stay_purposes = session.query(
                    Stay.stay_purpose,
                    func.count(Stay.id)
                ).filter(
                    Stay.created_at >= start_date,
                    Stay.created_at <= end_date
                ).group_by(Stay.stay_purpose).all()

                # مهمانان VIP
                vip_guests = session.query(Stay).join(Guest).filter(
                    Stay.created_at >= start_date,
                    Stay.created_at <= end_date,
                    Guest.vip_status == True
                ).count()

                # طول اقامت
                stay_durations = session.query(
                    func.avg(
                        func.extract('day', Stay.planned_check_out - Stay.planned_check_in)
                    )
                ).filter(
                    Stay.created_at >= start_date,
                    Stay.created_at <= end_date,
                    Stay.actual_check_in.isnot(None)
                ).scalar() or 0

                # مهمانان بازگشتی
                returning_guests = session.query(
                    Stay.guest_id,
                    func.count(Stay.id)
                ).filter(
                    Stay.created_at >= start_date,
                    Stay.created_at <= end_date
                ).group_by(Stay.guest_id).having(func.count(Stay.id) > 1).count()

                report_data = {
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date,
                        'period_type': period
                    },
                    'generated_at': datetime.now(),
                    'guest_statistics': {
                        'total_stays': total_guests,
                        'unique_guests': unique_guests,
                        'vip_guests': vip_guests,
                        'returning_guests': returning_guests,
                        'average_stay_duration': round(stay_durations, 1)
                    },
                    'nationality_breakdown': [
                        {
                            'nationality': nationality or 'نامشخص',
                            'count': count,
                            'percentage': round(count / total_guests * 100, 2) if total_guests > 0 else 0
                        }
                        for nationality, count in guest_nationalities
                    ],
                    'purpose_breakdown': [
                        {
                            'purpose': purpose or 'نامشخص',
                            'count': count,
                            'percentage': round(count / total_guests * 100, 2) if total_guests > 0 else 0
                        }
                        for purpose, count in stay_purposes
                    ],
                    'top_guests': ReportService._get_top_guests(session, start_date, end_date)
                }

                logger.info(f"👥 گزارش تحلیل مهمانان برای دوره {period} ایجاد شد")

                return {
                    'success': True,
                    'report': report_data,
                    'report_type': 'guest_analysis'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد گزارش تحلیل مهمانان: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'GUEST_ANALYSIS_REPORT_ERROR'
            }

    @staticmethod
    def generate_housekeeping_report(start_date: date, end_date: date) -> Dict[str, Any]:
        """گزارش عملکرد خانه‌داری"""
        try:
            with db_session() as session:
                # آمار وظایف
                total_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.created_at >= start_date,
                    HousekeepingTask.created_at <= end_date
                ).count()

                completed_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.created_at >= start_date,
                    HousekeepingTask.created_at <= end_date,
                    HousekeepingTask.status == 'completed'
                ).count()

                in_progress_tasks = session.query(HousekeepingTask).filter(
                    HousekeepingTask.created_at >= start_date,
                    HousekeepingTask.created_at <= end_date,
                    HousekeepingTask.status == 'in_progress'
                ).count()

                # عملکرد کارکنان
                staff_performance = session.query(
                    HousekeepingTask.assigned_to,
                    func.count(HousekeepingTask.id),
                    func.avg(
                        func.extract('epoch', HousekeepingTask.completed_at - HousekeepingTask.assigned_at) / 60
                    ).label('avg_completion_time')
                ).filter(
                    HousekeepingTask.created_at >= start_date,
                    HousekeepingTask.created_at <= end_date,
                    HousekeepingTask.status == 'completed'
                ).group_by(HousekeepingTask.assigned_to).all()

                # وظایف بر اساس نوع
                tasks_by_type = session.query(
                    HousekeepingTask.task_type,
                    func.count(HousekeepingTask.id)
                ).filter(
                    HousekeepingTask.created_at >= start_date,
                    HousekeepingTask.created_at <= end_date
                ).group_by(HousekeepingTask.task_type).all()

                # کیفیت کار
                quality_ratings = session.query(
                    HousekeepingTask.quality_rating,
                    func.count(HousekeepingTask.id)
                ).filter(
                    HousekeepingTask.created_at >= start_date,
                    HousekeepingTask.created_at <= end_date,
                    HousekeepingTask.quality_rating.isnot(None)
                ).group_by(HousekeepingTask.quality_rating).all()

                report_data = {
                    'period': {
                        'start_date': start_date,
                        'end_date': end_date
                    },
                    'generated_at': datetime.now(),
                    'performance_summary': {
                        'total_tasks': total_tasks,
                        'completed_tasks': completed_tasks,
                        'in_progress_tasks': in_progress_tasks,
                        'completion_rate': round(completed_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0,
                        'average_completion_time': round(
                            sum(avg_time or 0 for _, _, avg_time in staff_performance) / len(staff_performance) if staff_performance else 0,
                            1
                        )
                    },
                    'staff_performance': [
                        {
                            'staff_id': staff_id,
                            'tasks_completed': count,
                            'average_completion_time': round(avg_time or 0, 1) if avg_time else 0
                        }
                        for staff_id, count, avg_time in staff_performance
                    ],
                    'tasks_by_type': [
                        {
                            'task_type': task_type,
                            'count': count
                        }
                        for task_type, count in tasks_by_type
                    ],
                    'quality_analysis': [
                        {
                            'rating': rating,
                            'count': count,
                            'percentage': round(count / sum(c for _, c in quality_ratings) * 100, 2) if quality_ratings else 0
                        }
                        for rating, count in quality_ratings
                    ]
                }

                logger.info(f"🧹 گزارش خانه‌داری برای دوره {start_date} تا {end_date} ایجاد شد")

                return {
                    'success': True,
                    'report': report_data,
                    'report_type': 'housekeeping'
                }

        except Exception as e:
            logger.error(f"❌ خطا در ایجاد گزارش خانه‌داری: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'HOUSEKEEPING_REPORT_ERROR'
            }

    @staticmethod
    def export_report_to_csv(report_data: Dict[str, Any], report_type: str) -> Dict[str, Any]:
        """خروجی گزارش به فایل CSV"""
        try:
            export_dir = config.app.export_dir
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_type}_{timestamp}.csv"
            filepath = export_dir / filename

            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if report_type == 'daily_occupancy':
                    ReportService._export_daily_occupancy_csv(csvfile, report_data)
                elif report_type == 'financial':
                    ReportService._export_financial_csv(csvfile, report_data)
                elif report_type == 'guest_analysis':
                    ReportService._export_guest_analysis_csv(csvfile, report_data)
                elif report_type == 'housekeeping':
                    ReportService._export_housekeeping_csv(csvfile, report_data)

            logger.info(f"📁 گزارش به فایل CSV صادر شد: {filename}")

            return {
                'success': True,
                'filepath': str(filepath),
                'filename': filename,
                'message': 'گزارش با موفقیت به CSV صادر شد'
            }

        except Exception as e:
            logger.error(f"❌ خطا در صدور گزارش به CSV: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CSV_EXPORT_ERROR'
            }

    @staticmethod
    def get_available_reports() -> Dict[str, Any]:
        """دریافت لیست گزارش‌های موجود"""
        reports = {
            'daily_occupancy': {
                'name': 'گزارش روزانه اشغال',
                'description': 'وضعیت اشغال اتاق‌ها و مهمانان روز جاری',
                'parameters': ['report_date (اختیاری)']
            },
            'financial': {
                'name': 'گزارش مالی',
                'description': 'گزارش درآمد و تراکنش‌های مالی',
                'parameters': ['start_date', 'end_date']
            },
            'guest_analysis': {
                'name': 'تحلیل مهمانان',
                'description': 'آمار و تحلیل مهمانان در دوره‌های مختلف',
                'parameters': ['period (month/quarter/year)']
            },
            'housekeeping': {
                'name': 'گزارش خانه‌داری',
                'description': 'عملکرد و آمار بخش خانه‌داری',
                'parameters': ['start_date', 'end_date']
            }
        }

        return {
            'success': True,
            'reports': reports
        }

    # متدهای کمکی خصوصی
    @staticmethod
    def _get_total_rooms(session: Session) -> int:
        """دریافت تعداد کل اتاق‌ها"""
        from app.models.shared.hotel_models import HotelRoom
        return session.query(HotelRoom).filter(HotelRoom.is_active == True).count()

    @staticmethod
    def _get_occupied_rooms_count(session: Session, target_date: date) -> int:
        """دریافت تعداد اتاق‌های اشغال شده در تاریخ مشخص"""
        return session.query(RoomAssignment).filter(
            RoomAssignment.assignment_date <= target_date,
            RoomAssignment.expected_check_out >= target_date,
            RoomAssignment.actual_check_out.is_(None)
        ).count()

    @staticmethod
    def _get_room_type_statistics(session: Session, target_date: date) -> List[Dict[str, Any]]:
        """آمار اتاق‌ها بر اساس نوع"""
        from app.models.shared.hotel_models import HotelRoom

        # این بخش نیاز به پیاده‌سازی دقیق‌تر دارد
        # در این نسخه ساده شده است
        return []

    @staticmethod
    def _get_todays_arrivals(session: Session, target_date: date) -> List[Dict[str, Any]]:
        """دریافت مهمانان ورودی امروز"""
        arrivals = session.query(Stay).options(
            joinedload(Stay.guest)
        ).filter(
            func.date(Stay.planned_check_in) == target_date,
            Stay.status.in_(['confirmed', 'checked_in'])
        ).all()

        return [
            {
                'guest_name': f"{stay.guest.first_name} {stay.guest.last_name}",
                'check_in_time': stay.planned_check_in,
                'status': stay.status,
                'room_number': 'تعیین نشده'  # نیاز به پیاده‌سازی
            }
            for stay in arrivals
        ]

    @staticmethod
    def _get_todays_departures(session: Session, target_date: date) -> List[Dict[str, Any]]:
        """دریافت مهمانان خروجی امروز"""
        departures = session.query(Stay).options(
            joinedload(Stay.guest)
        ).filter(
            func.date(Stay.planned_check_out) == target_date,
            Stay.status.in_(['checked_in', 'checked_out'])
        ).all()

        return [
            {
                'guest_name': f"{stay.guest.first_name} {stay.guest.last_name}",
                'check_out_time': stay.planned_check_out,
                'status': stay.status,
                'room_number': 'تعیین نشده'  # نیاز به پیاده‌سازی
            }
            for stay in departures
        ]

    @staticmethod
    def _get_current_guests(session: Session, target_date: date) -> List[Dict[str, Any]]:
        """دریافت مهمانان حاضر"""
        current_guests = session.query(Stay).options(
            joinedload(Stay.guest)
        ).filter(
            Stay.actual_check_in <= target_date,
            Stay.actual_check_out.is_(None),
            Stay.status == 'checked_in'
        ).all()

        return [
            {
                'guest_name': f"{stay.guest.first_name} {stay.guest.last_name}",
                'check_in_date': stay.actual_check_in.date(),
                'planned_check_out': stay.planned_check_out.date(),
                'room_number': 'تعیین نشده'  # نیاز به پیاده‌سازی
            }
            for stay in current_guests
        ]

    @staticmethod
    def _get_top_guests(session: Session, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """دریافت مهمانان برتر"""
        top_guests = session.query(
            Guest.id,
            Guest.first_name,
            Guest.last_name,
            func.count(Stay.id).label('stay_count'),
            func.sum(Stay.total_amount).label('total_spent')
        ).join(Stay, Stay.guest_id == Guest.id).filter(
            Stay.created_at >= start_date,
            Stay.created_at <= end_date
        ).group_by(
            Guest.id, Guest.first_name, Guest.last_name
        ).order_by(
            func.sum(Stay.total_amount).desc()
        ).limit(10).all()

        return [
            {
                'guest_id': guest_id,
                'full_name': f"{first_name} {last_name}",
                'stay_count': stay_count,
                'total_spent': float(total_spent or 0)
            }
            for guest_id, first_name, last_name, stay_count, total_spent in top_guests
        ]

    @staticmethod
    def _export_daily_occupancy_csv(csvfile, report_data):
        """صدور گزارش روزانه به CSV"""
        writer = csv.writer(csvfile)
        writer.writerow(['گزارش روزانه اشغال اتاق‌ها'])
        writer.writerow(['تاریخ گزارش', report_data['report_date']])
        writer.writerow(['تاریخ ایجاد', report_data['generated_at']])
        writer.writerow([])

        # خلاصه
        writer.writerow(['خلاصه'])
        summary = report_data['summary']
        writer.writerow(['کل اتاق‌ها', summary['total_rooms']])
        writer.writerow(['اتاق‌های اشغال شده', summary['occupied_rooms']])
        writer.writerow(['اتاق‌های خالی', summary['available_rooms']])
        writer.writerow(['نرخ اشغال', f"{summary['occupancy_rate']}%"])
        writer.writerow([])

    @staticmethod
    def _export_financial_csv(csvfile, report_data):
        """صدور گزارش مالی به CSV"""
        writer = csv.writer(csvfile)
        # پیاده‌سازی مشابه بالا
        pass

    @staticmethod
    def _export_guest_analysis_csv(csvfile, report_data):
        """صدور گزارش تحلیل مهمانان به CSV"""
        writer = csv.writer(csvfile)
        # پیاده‌سازی مشابه بالا
        pass

    @staticmethod
    def _export_housekeeping_csv(csvfile, report_data):
        """صدور گزارش خانه‌داری به CSV"""
        writer = csv.writer(csvfile)
        # پیاده‌سازی مشابه بالا
        pass
