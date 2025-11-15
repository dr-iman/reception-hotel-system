# app/models/reception/payment_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Payment(Base):
    """مدل پرداخت‌های مهمانان"""
    __tablename__ = 'reception_payments'

    id = Column(Integer, primary_key=True)
    stay_id = Column(Integer, ForeignKey('reception_stays.id'), nullable=False)

    # اطلاعات پرداخت
    amount = Column(DECIMAL(15, 0), nullable=False)
    payment_method = Column(String(20), nullable=False)  # cash, card, bank_transfer, agency
    payment_type = Column(String(20), nullable=False)   # advance, settlement, refund, deposit
    currency = Column(String(10), default='IRR')

    # اطلاعات کارت‌خوان
    pos_reference = Column(String(100))  # شماره مرجع دستگاه کارت‌خوان
    card_number = Column(String(20))     # ۴ رقم آخر کارت
    transaction_id = Column(String(100)) # شماره تراکنش

    # وضعیت پرداخت
    status = Column(String(20), default='completed')  # pending, completed, failed, refunded
    verified_by = Column(Integer)  # کاربر تأییدکننده
    verified_at = Column(DateTime)

    # اطلاعات اضافی
    description = Column(Text)
    receipt_number = Column(String(50), unique=True)

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    stay = relationship("Stay", back_populates="payments")

class GuestFolio(Base):
    """مدل صورت�حساب مهمان"""
    __tablename__ = 'reception_guest_folios'

    id = Column(Integer, primary_key=True)
    stay_id = Column(Integer, ForeignKey('reception_stays.id'), nullable=False)

    # مانده حساب
    opening_balance = Column(DECIMAL(15, 0), default=0)
    total_charges = Column(DECIMAL(15, 0), default=0)
    total_payments = Column(DECIMAL(15, 0), default=0)
    current_balance = Column(DECIMAL(15, 0), default=0)

    # وضعیت
    folio_status = Column(String(20), default='open')  # open, settled, disputed
    last_updated = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    stay = relationship("Stay")
    transactions = relationship("FolioTransaction", back_populates="folio")

class FolioTransaction(Base):
    """مدل تراکنش‌های صورت‌حساب"""
    __tablename__ = 'reception_folio_transactions'

    id = Column(Integer, primary_key=True)
    folio_id = Column(Integer, ForeignKey('reception_guest_folios.id'), nullable=False)

    # اطلاعات تراکنش
    transaction_type = Column(String(20), nullable=False)  # charge, payment, adjustment
    amount = Column(DECIMAL(15, 0), nullable=False)
    description = Column(Text, nullable=False)
    reference_id = Column(Integer)  # ID سرویس یا پرداخت مرتبط

    # دسته‌بندی
    category = Column(String(50))  # room_charge, restaurant, minibar, telephone, etc.
    subcategory = Column(String(50))

    # اطلاعات مالی
    tax_amount = Column(DECIMAL(12, 0), default=0)
    service_charge = Column(DECIMAL(12, 0), default=0)

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    folio = relationship("GuestFolio", back_populates="transactions")

class CashierShift(Base):
    """مدل شیفت صندوق‌دار"""
    __tablename__ = 'reception_cashier_shifts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # کاربر صندوق‌دار

    # زمان‌بندی شیفت
    shift_start = Column(DateTime, nullable=False)
    shift_end = Column(DateTime)

    # موجودی نقدی
    opening_balance = Column(DECIMAL(15, 0), default=0)
    closing_balance = Column(DECIMAL(15, 0), default=0)
    expected_cash = Column(DECIMAL(15, 0), default=0)
    actual_cash = Column(DECIMAL(15, 0), default=0)
    cash_difference = Column(DECIMAL(15, 0), default=0)

    # آمار تراکنش‌ها
    total_transactions = Column(Integer, default=0)
    cash_transactions = Column(Integer, default=0)
    card_transactions = Column(Integer, default=0)
    total_amount = Column(DECIMAL(15, 0), default=0)

    # وضعیت
    status = Column(String(20), default='open')  # open, closed, audited

    created_at = Column(DateTime, default=datetime.now)
