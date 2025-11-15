# app/services/reception/payment_service.py
"""
سرویس مدیریت پرداخت‌ها و صورت‌حساب‌ها
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload

from app.core.database import db_session
from app.models.reception.payment_models import Payment, GuestFolio, FolioTransaction, CashierShift
from app.models.reception.guest_models import Stay
from app.core.payment_processor import payment_processor
from config import config

logger = logging.getLogger(__name__)

class PaymentService:
    """سرویس مدیریت پرداخت‌ها و مالی"""

    @staticmethod
    def process_payment(stay_id: int, amount: Decimal, payment_method: str,
                       payment_data: Dict) -> Dict[str, Any]:
        """پردازش پرداخت مهمان"""
        try:
            with db_session() as session:
                # بررسی اقامت
                stay = session.query(Stay).filter(Stay.id == stay_id).first()
                if not stay:
                    return {
                        'success': False,
                        'error': 'اقامت یافت نشد',
                        'error_code': 'STAY_NOT_FOUND'
                    }

                # دریافت صورت‌حساب
                folio = session.query(GuestFolio).filter(GuestFolio.stay_id == stay_id).first()
                if not folio:
                    return {
                        'success': False,
                        'error': 'صورت‌حساب یافت نشد',
                        'error_code': 'FOLIO_NOT_FOUND'
                    }

                # پردازش پرداخت
                payment_result = payment_processor.process_payment({
                    'amount': amount,
                    'payment_method': payment_method,
                    'cash_received': payment_data.get('cash_received'),
                    'card_data': payment_data.get('card_data', {}),
                    'description': f'پرداخت اقامت مهمان {stay.guest.first_name} {stay.guest.last_name}'
                })

                if not payment_result['success']:
                    return payment_result

                # ایجاد رکورد پرداخت
                payment = Payment(
                    stay_id=stay_id,
                    amount=amount,
                    payment_method=payment_method,
                    payment_type=payment_data.get('payment_type', 'settlement'),
                    currency=config.payment.default_currency,
                    status='completed',
                    description=payment_data.get('description', 'پرداخت اقامت'),
                    receipt_number=PaymentService._generate_receipt_number(session)
                )

                # افزودن اطلاعات کارت‌خوان در صورت پرداخت کارتی
                if payment_method == 'pos' and 'transaction_id' in payment_result:
                    payment.pos_reference = payment_result.get('reference_number')
                    payment.card_number = payment_result.get('card_number')
                    payment.transaction_id = payment_result.get('transaction_id')

                session.add(payment)
                session.flush()  # گرفتن ID پرداخت

                # ایجاد تراکنش در صورت‌حساب
                folio_transaction = FolioTransaction(
                    folio_id=folio.id,
                    transaction_type='payment',
                    amount=amount,
                    description=f'پرداخت {payment_method} - {payment_data.get("description", "اقامت")}',
                    reference_id=payment.id,
                    category='payment',
                    subcategory=payment_method
                )
                session.add(folio_transaction)

                # به‌روزرسانی صورت‌حساب
                folio.total_payments += amount
                folio.current_balance = folio.total_charges - folio.total_payments

                # به‌روزرسانی اقامت
                stay.remaining_balance = folio.current_balance

                session.commit()

                logger.info(f"✅ پرداخت موفق: {amount} {config.payment.default_currency} برای اقامت {stay_id}")

                return {
                    'success': True,
                    'payment_id': payment.id,
                    'receipt_number': payment.receipt_number,
                    'amount': float(amount),
                    'payment_method': payment_method,
                    'remaining_balance': float(folio.current_balance),
                    'transaction_id': payment_result.get('transaction_id'),
                    'message': 'پرداخت با موفقیت انجام شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در پردازش پرداخت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'PAYMENT_PROCESSING_ERROR'
            }

    @staticmethod
    def get_guest_folio(stay_id: int) -> Dict[str, Any]:
        """دریافت صورت‌حساب مهمان"""
        try:
            with db_session() as session:
                folio = session.query(GuestFolio).filter(
                    GuestFolio.stay_id == stay_id
                ).first()

                if not folio:
                    return {
                        'success': False,
                        'error': 'صورت‌حساب یافت نشد',
                        'error_code': 'FOLIO_NOT_FOUND'
                    }

                # تراکنش‌های صورت‌حساب
                transactions = session.query(FolioTransaction).filter(
                    FolioTransaction.folio_id == folio.id
                ).order_by(FolioTransaction.created_at.desc()).all()

                # پرداخت‌ها
                payments = session.query(Payment).filter(
                    Payment.stay_id == stay_id
                ).order_by(Payment.created_at.desc()).all()

                folio_data = {
                    'folio_id': folio.id,
                    'stay_id': folio.stay_id,
                    'opening_balance': float(folio.opening_balance),
                    'total_charges': float(folio.total_charges),
                    'total_payments': float(folio.total_payments),
                    'current_balance': float(folio.current_balance),
                    'folio_status': folio.folio_status,
                    'last_updated': folio.last_updated,
                    'transactions': [
                        {
                            'id': trans.id,
                            'type': trans.transaction_type,
                            'amount': float(trans.amount),
                            'description': trans.description,
                            'category': trans.category,
                            'subcategory': trans.subcategory,
                            'created_at': trans.created_at
                        }
                        for trans in transactions
                    ],
                    'payments': [
                        {
                            'id': payment.id,
                            'amount': float(payment.amount),
                            'method': payment.payment_method,
                            'type': payment.payment_type,
                            'status': payment.status,
                            'receipt_number': payment.receipt_number,
                            'created_at': payment.created_at
                        }
                        for payment in payments
                    ]
                }

                return {
                    'success': True,
                    'folio': folio_data
                }

        except Exception as e:
            logger.error(f"❌ خطا در دریافت صورت‌حساب: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'FOLIO_RETRIEVAL_ERROR'
            }

    @staticmethod
    def add_folio_charge(stay_id: int, amount: Decimal, description: str,
                        category: str, subcategory: str = None) -> Dict[str, Any]:
        """افزودن هزینه به صورت‌حساب مهمان"""
        try:
            with db_session() as session:
                folio = session.query(GuestFolio).filter(
                    GuestFolio.stay_id == stay_id
                ).first()

                if not folio:
                    return {
                        'success': False,
                        'error': 'صورت‌حساب یافت نشد',
                        'error_code': 'FOLIO_NOT_FOUND'
                    }

                # ایجاد تراکنش هزینه
                transaction = FolioTransaction(
                    folio_id=folio.id,
                    transaction_type='charge',
                    amount=amount,
                    description=description,
                    category=category,
                    subcategory=subcategory
                )
                session.add(transaction)

                # به‌روزرسانی صورت‌حساب
                folio.total_charges += amount
                folio.current_balance = folio.total_charges - folio.total_payments

                # به‌روزرسانی اقامت
                stay = session.query(Stay).filter(Stay.id == stay_id).first()
                if stay:
                    stay.remaining_balance = folio.current_balance

                session.commit()

                logger.info(f"✅ هزینه به صورت‌حساب افزوده شد: {amount} - {description}")

                return {
                    'success': True,
                    'transaction_id': transaction.id,
                    'amount': float(amount),
                    'description': description,
                    'new_balance': float(folio.current_balance),
                    'message': 'هزینه با موفقیت افزوده شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در افزودن هزینه: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'ADD_CHARGE_ERROR'
            }

    @staticmethod
    def refund_payment(payment_id: int, refund_amount: Decimal = None) -> Dict[str, Any]:
        """عودت پرداخت"""
        try:
            with db_session() as session:
                payment = session.query(Payment).filter(Payment.id == payment_id).first()
                if not payment:
                    return {
                        'success': False,
                        'error': 'پرداخت یافت نشد',
                        'error_code': 'PAYMENT_NOT_FOUND'
                    }

                if payment.payment_method != 'pos':
                    return {
                        'success': False,
                        'error': 'عودت فقط برای پرداخت‌های کارتی امکان‌پذیر است',
                        'error_code': 'REFUND_METHOD_NOT_SUPPORTED'
                    }

                amount_to_refund = refund_amount or payment.amount

                # پردازش عودت
                refund_result = payment_processor.refund_payment(
                    payment.transaction_id,
                    amount_to_refund,
                    payment.payment_method
                )

                if not refund_result['success']:
                    return refund_result

                # ایجاد پرداخت عودت
                refund_payment = Payment(
                    stay_id=payment.stay_id,
                    amount=-amount_to_refund,  # مقدار منفی برای عودت
                    payment_method=payment.payment_method,
                    payment_type='refund',
                    currency=payment.currency,
                    status='completed',
                    description=f'عودت پرداخت - {payment.receipt_number}',
                    receipt_number=PaymentService._generate_receipt_number(session),
                    pos_reference=refund_result.get('refund_id'),
                    transaction_id=refund_result.get('refund_id')
                )
                session.add(refund_payment)
                session.flush()

                # به‌روزرسانی صورت‌حساب
                folio = session.query(GuestFolio).filter(
                    GuestFolio.stay_id == payment.stay_id
                ).first()

                if folio:
                    folio_transaction = FolioTransaction(
                        folio_id=folio.id,
                        transaction_type='payment',
                        amount=-amount_to_refund,
                        description=f'عودت پرداخت - {payment.receipt_number}',
                        reference_id=refund_payment.id,
                        category='refund',
                        subcategory=payment.payment_method
                    )
                    session.add(folio_transaction)

                    folio.total_payments -= amount_to_refund
                    folio.current_balance = folio.total_charges - folio.total_payments

                # به‌روزرسانی پرداخت اصلی
                payment.status = 'refunded'

                session.commit()

                logger.info(f"✅ عودت پرداخت انجام شد: {amount_to_refund} برای پرداخت {payment_id}")

                return {
                    'success': True,
                    'refund_id': refund_payment.id,
                    'refund_amount': float(amount_to_refund),
                    'original_payment_id': payment_id,
                    'message': 'عودت با موفقیت انجام شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در عودت پرداخت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REFUND_ERROR'
            }

    @staticmethod
    def open_cashier_shift(user_id: int, opening_balance: Decimal = Decimal('0')) -> Dict[str, Any]:
        """شروع شیفت صندوق‌دار"""
        try:
            with db_session() as session:
                # بررسی شیفت باز
                open_shift = session.query(CashierShift).filter(
                    CashierShift.user_id == user_id,
                    CashierShift.status == 'open'
                ).first()

                if open_shift:
                    return {
                        'success': False,
                        'error': 'شیفت باز دیگری برای این کاربر وجود دارد',
                        'error_code': 'OPEN_SHIFT_EXISTS'
                    }

                # ایجاد شیفت جدید
                shift = CashierShift(
                    user_id=user_id,
                    shift_start=datetime.now(),
                    opening_balance=opening_balance,
                    status='open'
                )
                session.add(shift)
                session.commit()

                logger.info(f"✅ شیفت صندوق‌دار شروع شد: User {user_id}, Shift {shift.id}")

                return {
                    'success': True,
                    'shift_id': shift.id,
                    'shift_start': shift.shift_start,
                    'opening_balance': float(opening_balance),
                    'message': 'شیفت صندوق‌دار شروع شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در شروع شیفت صندوق‌دار: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'OPEN_SHIFT_ERROR'
            }

    @staticmethod
    def close_cashier_shift(shift_id: int, actual_cash: Decimal) -> Dict[str, Any]:
        """بستن شیفت صندوق‌دار"""
        try:
            with db_session() as session:
                shift = session.query(CashierShift).filter(CashierShift.id == shift_id).first()
                if not shift:
                    return {
                        'success': False,
                        'error': 'شیفت یافت نشد',
                        'error_code': 'SHIFT_NOT_FOUND'
                    }

                if shift.status != 'open':
                    return {
                        'success': False,
                        'error': 'شیفت قبلاً بسته شده است',
                        'error_code': 'SHIFT_ALREADY_CLOSED'
                    }

                # محاسبات مالی
                total_cash_received = PaymentService._get_shift_cash_total(session, shift_id)
                expected_cash = shift.opening_balance + total_cash_received
                cash_difference = actual_cash - expected_cash

                # به‌روزرسانی شیفت
                shift.shift_end = datetime.now()
                shift.closing_balance = actual_cash
                shift.expected_cash = expected_cash
                shift.actual_cash = actual_cash
                shift.cash_difference = cash_difference
                shift.status = 'closed'

                # آمار تراکنش‌ها
                stats = PaymentService._get_shift_statistics(session, shift_id)
                shift.total_transactions = stats['total_transactions']
                shift.cash_transactions = stats['cash_transactions']
                shift.card_transactions = stats['card_transactions']
                shift.total_amount = stats['total_amount']

                session.commit()

                logger.info(f"✅ شیفت صندوق‌دار بسته شد: Shift {shift_id}")

                return {
                    'success': True,
                    'shift_id': shift_id,
                    'shift_end': shift.shift_end,
                    'expected_cash': float(expected_cash),
                    'actual_cash': float(actual_cash),
                    'cash_difference': float(cash_difference),
                    'statistics': stats,
                    'message': 'شیفت صندوق‌دار بسته شد'
                }

        except Exception as e:
            logger.error(f"❌ خطا در بستن شیفت صندوق‌دار: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'CLOSE_SHIFT_ERROR'
            }

    # متدهای کمکی خصوصی
    @staticmethod
    def _generate_receipt_number(session: Session) -> str:
        """تولید شماره رسید منحصربه‌فرد"""
        prefix = config.receipt.receipt_prefix
        length = config.receipt.receipt_number_length

        # دریافت آخرین شماره رسید
        last_receipt = session.query(Payment.receipt_number).filter(
            Payment.receipt_number.like(f"{prefix}-%")
        ).order_by(Payment.receipt_number.desc()).first()

        if last_receipt:
            last_number = int(last_receipt[0].split('-')[1])
            new_number = last_number + 1
        else:
            new_number = 1

        return f"{prefix}-{new_number:0{length}d}"

    @staticmethod
    def _get_shift_cash_total(session: Session, shift_id: int) -> Decimal:
        """محاسبه مجموع پرداخت‌های نقدی در شیفت"""
        shift = session.query(CashierShift).filter(CashierShift.id == shift_id).first()
        if not shift:
            return Decimal('0')

        cash_total = session.query(
            sqlalchemy.func.sum(Payment.amount)
        ).filter(
            Payment.created_at >= shift.shift_start,
            Payment.payment_method == 'cash',
            Payment.status == 'completed'
        ).scalar()

        return cash_total or Decimal('0')

    @staticmethod
    def _get_shift_statistics(session: Session, shift_id: int) -> Dict[str, Any]:
        """دریافت آمار تراکنش‌های شیفت"""
        shift = session.query(CashierShift).filter(CashierShift.id == shift_id).first()
        if not shift:
            return {}

        # آمار بر اساس نوع پرداخت
        stats_query = session.query(
            Payment.payment_method,
            sqlalchemy.func.count(Payment.id),
            sqlalchemy.func.sum(Payment.amount)
        ).filter(
            Payment.created_at >= shift.shift_start,
            Payment.status == 'completed'
        ).group_by(Payment.payment_method).all()

        total_transactions = 0
        cash_transactions = 0
        card_transactions = 0
        total_amount = Decimal('0')

        for method, count, amount in stats_query:
            total_transactions += count
            total_amount += amount or Decimal('0')

            if method == 'cash':
                cash_transactions = count
            elif method == 'pos':
                card_transactions = count

        return {
            'total_transactions': total_transactions,
            'cash_transactions': cash_transactions,
            'card_transactions': card_transactions,
            'total_amount': float(total_amount)
        }
