# app/core/payment_processor.py
"""
پردازشگر پیشرفته پرداخت‌ها و اتصال به کارت‌خوان
"""

import logging
import time
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
import requests
from config import config

logger = logging.getLogger(__name__)

class PaymentGateway(ABC):
    """اینترفیس پایه برای درگاه‌های پرداخت"""

    @abstractmethod
    def process_payment(self, amount: Decimal, card_data: Dict, description: str) -> Dict[str, Any]:
        """پردازش پرداخت"""
        pass

    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: Decimal) -> Dict[str, Any]:
        """عودت پرداخت"""
        pass

    @abstractmethod
    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """بررسی وضعیت پرداخت"""
        pass

class POSPaymentGateway(PaymentGateway):
    """درگاه پرداخت دستگاه کارت‌خوان"""

    def __init__(self):
        self.terminal_id = config.payment.pos_terminal_id
        self.merchant_id = config.payment.pos_merchant_id
        self.test_mode = config.payment.test_mode
        self.base_url = "https://pos-api.example.com" if not self.test_mode else "https://test-pos-api.example.com"

    def process_payment(self, amount: Decimal, card_data: Dict, description: str) -> Dict[str, Any]:
        """پردازش پرداخت از طریق کارت‌خوان"""
        try:
            logger.info(f"💳 شروع پردازش پرداخت: {amount} تومان")

            # شبیه‌سازی ارتباط با دستگاه کارت‌خوان
            if self.test_mode:
                return self._simulate_payment(amount, card_data, description)

            # در نسخه واقعی، اینجا با API دستگاه کارت‌خوان ارتباط برقرار می‌شود
            payload = {
                'terminal_id': self.terminal_id,
                'merchant_id': self.merchant_id,
                'amount': int(amount * 10),  # تبدیل به ریال
                'card_number': card_data.get('card_number'),
                'expiry_date': card_data.get('expiry_date'),
                'cvv2': card_data.get('cvv2'),
                'description': description
            }

            response = requests.post(
                f"{self.base_url}/payment/process",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'transaction_id': result.get('transaction_id'),
                    'reference_number': result.get('reference_number'),
                    'card_number': card_data.get('card_number')[-4:],
                    'amount': amount,
                    'timestamp': datetime.now()
                }
            else:
                return {
                    'success': False,
                    'error': f"خطا در ارتباط با دستگاه کارت‌خوان: {response.status_code}",
                    'error_code': 'POS_CONNECTION_ERROR'
                }

        except Exception as e:
            logger.error(f"❌ خطا در پردازش پرداخت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'PROCESSING_ERROR'
            }

    def refund_payment(self, transaction_id: str, amount: Decimal) -> Dict[str, Any]:
        """عودت پرداخت"""
        try:
            logger.info(f"🔄 شروع عودت پرداخت: {transaction_id} - {amount} تومان")

            if self.test_mode:
                return self._simulate_refund(transaction_id, amount)

            payload = {
                'terminal_id': self.terminal_id,
                'transaction_id': transaction_id,
                'amount': int(amount * 10)  # تبدیل به ریال
            }

            response = requests.post(
                f"{self.base_url}/payment/refund",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'refund_id': response.json().get('refund_id'),
                    'amount': amount,
                    'timestamp': datetime.now()
                }
            else:
                return {
                    'success': False,
                    'error': f"خطا در عودت پرداخت: {response.status_code}",
                    'error_code': 'REFUND_ERROR'
                }

        except Exception as e:
            logger.error(f"❌ خطا در عودت پرداخت: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_code': 'REFUND_PROCESSING_ERROR'
            }

    def verify_payment(self, transaction_id: str) -> Dict[str, Any]:
        """بررسی وضعیت پرداخت"""
        try:
            if self.test_mode:
                return {'success': True, 'status': 'completed'}

            response = requests.get(
                f"{self.base_url}/payment/verify/{transaction_id}",
                timeout=15
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'status': response.json().get('status', 'unknown')
                }
            else:
                return {
                    'success': False,
                    'error': 'عدم توانایی در بررسی وضعیت پرداخت'
                }

        except Exception as e:
            logger.error(f"❌ خطا در بررسی وضعیت پرداخت: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _simulate_payment(self, amount: Decimal, card_data: Dict, description: str) -> Dict[str, Any]:
        """شبیه‌سازی پرداخت در حالت تست"""
        time.sleep(2)  # شبیه‌سازی تاخیر پردازش

        # بررسی شماره کارت تست
        test_card = card_data.get('card_number', '')[-4:]
        if test_card == '1111':
            return {
                'success': False,
                'error': 'موجودی کافی نیست',
                'error_code': 'INSUFFICIENT_FUNDS'
            }
        elif test_card == '2222':
            return {
                'success': False,
                'error': 'کارت مسدود شده است',
                'error_code': 'CARD_BLOCKED'
            }

        # پرداخت موفق
        return {
            'success': True,
            'transaction_id': f"TXN_{int(time.time())}",
            'reference_number': f"REF_{int(time.time())}",
            'card_number': test_card,
            'amount': amount,
            'timestamp': datetime.now(),
            'test_mode': True
        }

    def _simulate_refund(self, transaction_id: str, amount: Decimal) -> Dict[str, Any]:
        """شبیه‌سازی عودت در حالت تست"""
        time.sleep(1)
        return {
            'success': True,
            'refund_id': f"REFUND_{int(time.time())}",
            'amount': amount,
            'timestamp': datetime.now(),
            'test_mode': True
        }

class CashPayment:
    """پرداخت نقدی"""

    @staticmethod
    def process_payment(amount: Decimal, cash_received: Decimal) -> Dict[str, Any]:
        """پردازش پرداخت نقدی"""
        try:
            change = cash_received - amount

            if change < 0:
                return {
                    'success': False,
                    'error': 'مبلغ پرداختی کمتر از مبلغ قابل پرداخت است',
                    'error_code': 'INSUFFICIENT_CASH'
                }

            return {
                'success': True,
                'amount': amount,
                'cash_received': cash_received,
                'change': change,
                'payment_method': 'cash',
                'timestamp': datetime.now()
            }

        except Exception as e:
            logger.error(f"❌ خطا در پردازش پرداخت نقدی: {e}")
            return {
                'success': False,
                'error': str(e)
            }

class PaymentProcessor:
    """پردازشگر اصلی پرداخت‌ها"""

    def __init__(self):
        self.gateways = {
            'pos': POSPaymentGateway(),
            'cash': CashPayment()
        }
        self.commission_rate = Decimal(str(config.payment.commission_rate))
        self.tax_rate = Decimal(str(config.payment.tax_rate))

    def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """پردازش پرداخت"""
        try:
            payment_method = payment_data.get('payment_method')
            amount = Decimal(str(payment_data.get('amount', 0)))

            if payment_method not in self.gateways:
                return {
                    'success': False,
                    'error': f'روش پرداخت {payment_method} پشتیبانی نمی‌شود'
                }

            # محاسبه کارمزد و مالیات
            net_amount, commission, tax = self._calculate_net_amount(amount)

            if payment_method == 'pos':
                result = self.gateways['pos'].process_payment(
                    amount=net_amount,
                    card_data=payment_data.get('card_data', {}),
                    description=payment_data.get('description', 'پرداخت هتل')
                )
            elif payment_method == 'cash':
                cash_received = Decimal(str(payment_data.get('cash_received', 0)))
                result = self.gateways['cash'].process_payment(net_amount, cash_received)
            else:
                return {
                    'success': False,
                    'error': 'روش پرداخت نامعتبر'
                }

            # افزودن اطلاعات مالی به نتیجه
            if result['success']:
                result.update({
                    'net_amount': float(net_amount),
                    'commission': float(commission),
                    'tax': float(tax),
                    'gross_amount': float(amount),
                    'payment_method': payment_method
                })

                logger.info(f"✅ پرداخت موفق: {amount} تومان - روش: {payment_method}")
            else:
                logger.error(f"❌ پرداخت ناموفق: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"❌ خطا در پردازشگر پرداخت: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_net_amount(self, gross_amount: Decimal) -> Tuple[Decimal, Decimal, Decimal]:
        """محاسبه مبلغ خالص، کارمزد و مالیات"""
        commission = gross_amount * self.commission_rate
        taxable_amount = gross_amount - commission
        tax = taxable_amount * self.tax_rate
        net_amount = gross_amount - commission - tax

        return net_amount, commission, tax

    def refund_payment(self, transaction_id: str, amount: Decimal, payment_method: str) -> Dict[str, Any]:
        """عودت پرداخت"""
        try:
            if payment_method == 'pos':
                return self.gateways['pos'].refund_payment(transaction_id, amount)
            else:
                return {
                    'success': False,
                    'error': 'عودت فقط برای پرداخت‌های کارتی امکان‌پذیر است'
                }

        except Exception as e:
            logger.error(f"❌ خطا در عودت پرداخت: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_payment_methods(self) -> Dict[str, Any]:
        """دریافت روش‌های پرداخت قابل استفاده"""
        methods = {
            'cash': {
                'name': 'نقدی',
                'enabled': True,
                'description': 'پرداخت نقدی در پذیرش'
            },
            'pos': {
                'name': 'کارت‌خوان',
                'enabled': config.payment.pos_enabled,
                'description': 'پرداخت با کارت بانکی'
            }
        }

        return methods

# ایجاد instance جهانی
payment_processor = PaymentProcessor()
