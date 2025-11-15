# app/models/reception/room_status_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class RoomAssignment(Base):
    """مدل تخصیص اتاق به مهمان"""
    __tablename__ = 'reception_room_assignments'

    id = Column(Integer, primary_key=True)
    stay_id = Column(Integer, ForeignKey('reception_stays.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('hotel_rooms.id'), nullable=False)  # از سیستم مشترک

    # تاریخ‌های تخصیص
    assignment_date = Column(Date, nullable=False)
    expected_check_out = Column(Date, nullable=False)
    actual_check_out = Column(Date)

    # اطلاعات تخصیص
    assignment_type = Column(String(20), default='primary')  # primary, transfer, extra
    transfer_reason = Column(Text)  # در صورت جابجایی اتاق

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    stay = relationship("Stay", back_populates="room_assignments")
    room = relationship("HotelRoom")  # از سیستم مشترک
    status_changes = relationship("RoomStatusChange", back_populates="room_assignment")

class RoomStatusChange(Base):
    """مدل تغییرات وضعیت اتاق"""
    __tablename__ = 'reception_room_status_changes'

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('hotel_rooms.id'), nullable=False)
    room_assignment_id = Column(Integer, ForeignKey('reception_room_assignments.id'))

    # وضعیت‌ها
    previous_status = Column(String(20))
    new_status = Column(String(20), nullable=False)  # vacant, occupied, cleaning, inspection, out_of_order, maintenance
    status_reason = Column(Text)

    # اطلاعات تغییر
    changed_by = Column(Integer, nullable=False)  # کاربر تغییر دهنده
    change_type = Column(String(20))  # manual, automatic, housekeeping, maintenance

    # زمان‌بندی
    estimated_completion = Column(DateTime)  # زمان تخمینی اتمام وضعیت
    actual_completion = Column(DateTime)     # زمان واقعی اتمام

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    room = relationship("HotelRoom")
    room_assignment = relationship("RoomAssignment", back_populates="status_changes")

class RoomStatusSnapshot(Base):
    """اسنپ‌شوت وضعیت اتاق‌ها برای گزارش‌گیری"""
    __tablename__ = 'reception_room_status_snapshots'

    id = Column(Integer, primary_key=True)
    snapshot_date = Column(Date, nullable=False)
    snapshot_time = Column(DateTime, nullable=False)

    # آمار وضعیت‌ها
    total_rooms = Column(Integer, default=0)
    vacant_rooms = Column(Integer, default=0)
    occupied_rooms = Column(Integer, default=0)
    cleaning_rooms = Column(Integer, default=0)
    maintenance_rooms = Column(Integer, default=0)
    out_of_order_rooms = Column(Integer, default=0)

    # آمار مهمانان
    total_guests = Column(Integer, default=0)
    checked_in_guests = Column(Integer, default=0)
    expected_arrivals = Column(Integer, default=0)
    expected_departures = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.now)
