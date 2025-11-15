# app/models/reception/guest_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON, Time
from sqlalchemy.orm import relationship
from datetime import datetime, date
from app.core.database import Base

class Guest(Base):
    """مدل اطلاعات کامل مهمان"""
    __tablename__ = 'reception_guests'

    id = Column(Integer, primary_key=True)

    # اطلاعات هویتی
    national_id = Column(String(20), unique=True, index=True)
    passport_number = Column(String(20))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(10))  # male, female
    date_of_birth = Column(Date)
    nationality = Column(String(50))

    # اطلاعات تماس
    phone = Column(String(15), nullable=False)
    email = Column(String(100))
    address = Column(Text)
    emergency_contact = Column(String(100))
    emergency_phone = Column(String(15))

    # اطلاعات شرکتی (برای مهمانان تجاری)
    company_name = Column(String(200))
    company_address = Column(Text)
    business_title = Column(String(100))

    # مدارک و اسناد
    id_card_image = Column(String(500))  # مسیر فایل تصویر کارت ملی
    passport_image = Column(String(500))  # مسیر فایل تصویر پاسپورت
    guest_photo = Column(String(500))     # تصویر مهمان

    # ترجیحات و اطلاعات ویژه
    preferences = Column(JSON, default=dict)  # ترجیحات مهمان
    special_requests = Column(Text)
    vip_status = Column(Boolean, default=False)
    blacklist_reason = Column(Text)  # در صورت وجود در لیست سیاه

    # اطلاعات سیستم
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    stays = relationship("Stay", back_populates="guest")
    companions = relationship("Companion", back_populates="guest")

class Companion(Base):
    """مدل همراهان مهمان"""
    __tablename__ = 'reception_companions'

    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey('reception_guests.id'), nullable=False)

    # اطلاعات همراه
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    relationship = Column(String(50))  # همسر, فرزند, همکار
    date_of_birth = Column(Date)
    national_id = Column(String(20))

    # اطلاعات تماس
    phone = Column(String(15))
    emergency_contact = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    guest = relationship("Guest", back_populates="companions")
    stay_assignments = relationship("CompanionStay", back_populates="companion")

class Stay(Base):
    """مدل اقامت مهمان"""
    __tablename__ = 'reception_stays'

    id = Column(Integer, primary_key=True)
    reservation_id = Column(Integer, ForeignKey('hotel_reservations.id'))  # ارتباط با سیستم رزرواسیون
    guest_id = Column(Integer, ForeignKey('reception_guests.id'), nullable=False)

    # تاریخ‌های اقامت
    planned_check_in = Column(DateTime, nullable=False)  # از سیستم رزرواسیون
    planned_check_out = Column(DateTime, nullable=False) # از سیستم رزرواسیون
    actual_check_in = Column(DateTime)  # زمان واقعی ورود
    actual_check_out = Column(DateTime) # زمان واقعی خروج

    # اطلاعات اقامت
    stay_purpose = Column(String(100))  # business, leisure, medical, etc.
    special_requirements = Column(Text)
    loyalty_number = Column(String(50))

    # وضعیت اقامت
    status = Column(String(20), default='confirmed')  # confirmed, checked_in, checked_out, no_show, cancelled
    early_check_in = Column(Boolean, default=False)
    late_check_out = Column(Boolean, default=False)

    # اطلاعات مالی
    total_amount = Column(DECIMAL(15, 0), default=0)
    advance_payment = Column(DECIMAL(15, 0), default=0)
    remaining_balance = Column(DECIMAL(15, 0), default=0)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    guest = relationship("Guest", back_populates="stays")
    reservation = relationship("HotelReservation")  # از سیستم رزرواسیون
    room_assignments = relationship("RoomAssignment", back_populates="stay")
    payments = relationship("Payment", back_populates="stay")
    companions = relationship("CompanionStay", back_populates="stay")

class CompanionStay(Base):
    """مدل ارتباط همراهان با اقامت"""
    __tablename__ = 'reception_companion_stays'

    id = Column(Integer, primary_key=True)
    companion_id = Column(Integer, ForeignKey('reception_companions.id'), nullable=False)
    stay_id = Column(Integer, ForeignKey('reception_stays.id'), nullable=False)

    # روابط
    companion = relationship("Companion", back_populates="stay_assignments")
    stay = relationship("Stay", back_populates="companions")
