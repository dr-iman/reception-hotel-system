# app/views/widgets/financial/__init__.py
"""
ویجت‌های مالی و پرداخت سیستم پذیرش
"""

from .payment_processing import PaymentProcessingWidget
from .guest_folio import GuestFolioWidget

__all__ = [
    'PaymentProcessingWidget',
    'GuestFolioWidget'
]
