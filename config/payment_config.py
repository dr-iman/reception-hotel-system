# config/payment_config.py
"""
تنظیمات درگاه‌های پرداخت و مالی
"""

import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

@dataclass
class PaymentConfig:
    """تنظیمات پرداخت و مالی"""

    # تنظیمات عمومی
    default_currency: str = os.getenv('DEFAULT_CURRENCY', 'IRR')
    test_mode: bool = os.getenv('PAYMENT_TEST_MODE', 'True').lower() == 'true'

    # نرخ‌های مالی
    tax_rate: Decimal = Decimal(os.getenv('TAX_RATE', '0.09'))  # 9%
    commission_rate: Decimal = Decimal(os.getenv('COMMISSION_RATE', '0.01'))  # 1%
    service_charge_rate: Decimal = Decimal(os.getenv('SERVICE_CHARGE_RATE', '0.05'))  # 5%

    # تنظیمات کارت‌خوان
    pos_enabled: bool = os.getenv('POS_ENABLED', 'True').lower() == 'true'
    pos_terminal_id: str = os.getenv('POS_TERMINAL_ID', 'TEST_TERMINAL_001')
    pos_merchant_id: str = os.getenv('POS_MERCHANT_ID', 'TEST_MERCHANT_001')
    pos_base_url: str = os.getenv('POS_BASE_URL', 'https://test-pos-api.example.com')

    # محدودیت‌های پرداخت
    min_payment_amount: Decimal = Decimal(os.getenv('MIN_PAYMENT_AMOUNT', '10000'))
    max_payment_amount: Decimal = Decimal(os.getenv('MAX_PAYMENT_AMOUNT', '100000000'))
    daily_cash_limit: Decimal = Decimal(os.getenv('DAILY_CASH_LIMIT', '50000000'))

    # تنظیمات امنیتی پرداخت
    require_approval_amount: Decimal = Decimal(os.getenv('REQUIRE_APPROVAL_AMOUNT', '10000000'))
    auto_refund_enabled: bool = os.getenv('AUTO_REFUND_ENABLED', 'False').lower() == 'true'
    refund_timeout_hours: int = int(os.getenv('REFUND_TIMEOUT_HOURS', '24'))

    @property
    def available_payment_methods(self) -> List[Dict[str, str]]:
        """روش‌های پرداخت قابل استفاده"""
        methods = [
            {
                'code': 'cash',
                'name': 'نقدی',
                'description': 'پرداخت نقدی در پذیرش',
                'enabled': True
            },
            {
                'code': 'pos',
                'name': 'کارت‌خوان',
                'description': 'پرداخت با کارت بانکی',
                'enabled': self.pos_enabled
            },
            {
                'code': 'bank_transfer',
                'name': 'حواله بانکی',
                'description': 'پرداخت از طریق حواله بانکی',
                'enabled': True
            },
            {
                'code': 'agency',
                'name': 'آژانس',
                'description': 'پرداخت از طریق آژانس مسافرتی',
                'enabled': True
            }
        ]
        return [method for method in methods if method['enabled']]

    def get_payment_method(self, method_code: str) -> Dict[str, str]:
        """دریافت اطلاعات روش پرداخت"""
        for method in self.available_payment_methods:
            if method['code'] == method_code:
                return method
        return {}

    def validate_payment_amount(self, amount: Decimal) -> Dict[str, bool]:
        """اعتبارسنجی مبلغ پرداخت"""
        return {
            'is_valid': self.min_payment_amount <= amount <= self.max_payment_amount,
            'is_below_min': amount < self.min_payment_amount,
            'is_above_max': amount > self.max_payment_amount,
            'requires_approval': amount >= self.require_approval_amount
        }

@dataclass
class ReceiptConfig:
    """تنظیمات فاکتور و رسید"""

    company_name: str = os.getenv('RECEIPT_COMPANY_NAME', 'هتل بین‌المللی')
    company_address: str = os.getenv('RECEIPT_COMPANY_ADDRESS', 'تهران، خیابان نمونه')
    company_phone: str = os.getenv('RECEIPT_COMPANY_PHONE', '+982112345678')
    tax_id: str = os.getenv('RECEIPT_TAX_ID', '1234567890')

    # قالب رسید
    receipt_header: str = os.getenv('RECEIPT_HEADER', 'رسید پرداخت هتل')
    include_tax_details: bool = os.getenv('RECEIPT_INCLUDE_TAX', 'True').lower() == 'true'
    print_company_logo: bool = os.getenv('RECEIPT_PRINT_LOGO', 'True').lower() == 'true'

    # شماره‌گذاری
    receipt_prefix: str = os.getenv('RECEIPT_PREFIX', 'REC')
    receipt_number_length: int = int(os.getenv('RECEIPT_NUMBER_LENGTH', '6'))

# ایجاد instance جهانی
payment_config = PaymentConfig()
receipt_config = ReceiptConfig()
