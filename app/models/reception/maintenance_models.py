# app/models/reception/maintenance_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class MaintenanceRequest(Base):
    """مدل درخواست‌های تعمیرات"""
    __tablename__ = 'reception_maintenance_requests'

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('hotel_rooms.id'), nullable=False)
    reported_by = Column(Integer, nullable=False)  # کاربر گزارش دهنده

    # اطلاعات درخواست
    issue_type = Column(String(50), nullable=False)  # electrical, plumbing, hvac, furniture, etc.
    issue_description = Column(Text, nullable=False)
    priority = Column(String(20), default='normal')  # low, normal, high, emergency

    # وضعیت
    status = Column(String(20), default='open')  # open, assigned, in_progress, completed, closed
    assigned_to = Column(Integer, ForeignKey('reception_staff.id'))  # تکنسین محول شده

    # زمان‌بندی
    reported_at = Column(DateTime, default=datetime.now)
    scheduled_date = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # تأثیر بر اتاق
    room_available = Column(Boolean, default=True)  # آیا اتاق قابل استفاده است؟
    estimated_downtime = Column(Integer)  # مدت زمان تخمینی تعمیر (ساعت)

    # هزینه‌ها
    estimated_cost = Column(DECIMAL(12, 0), default=0)
    actual_cost = Column(DECIMAL(12, 0), default=0)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    room = relationship("HotelRoom")
    technician = relationship("Staff", foreign_keys=[assigned_to])
    work_orders = relationship("MaintenanceWorkOrder", back_populates="request")

class MaintenanceWorkOrder(Base):
    """مدل دستورکار تعمیرات"""
    __tablename__ = 'reception_maintenance_work_orders'

    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('reception_maintenance_requests.id'), nullable=False)
    assigned_to = Column(Integer, ForeignKey('reception_staff.id'), nullable=False)

    # اطلاعات کار
    work_description = Column(Text, nullable=False)
    required_parts = Column(JSON, default=list)
    tools_needed = Column(JSON, default=list)
    safety_precautions = Column(Text)

    # زمان‌بندی
    scheduled_start = Column(DateTime, nullable=False)
    scheduled_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)

    # نتایج
    work_performed = Column(Text)
    parts_used = Column(JSON, default=list)
    labor_hours = Column(DECIMAL(5, 2), default=0)

    # تأییدیه
    verified_by = Column(Integer)  # کاربر تأییدکننده
    verification_notes = Column(Text)

    status = Column(String(20), default='scheduled')  # scheduled, in_progress, completed, verified

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    request = relationship("MaintenanceRequest", back_populates="work_orders")
    technician = relationship("Staff")

class MaintenanceInventory(Base):
    """مدل موجودی قطعات و مواد تاسیسات"""
    __tablename__ = 'reception_maintenance_inventory'

    id = Column(Integer, primary_key=True)

    # اطلاعات قطعه
    item_name = Column(String(200), nullable=False)
    item_code = Column(String(50), unique=True)
    category = Column(String(50), nullable=False)  # electrical, plumbing, hardware, etc.
    description = Column(Text)
    unit = Column(String(20), default='piece')  # piece, meter, liter, etc.

    # موجودی
    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=0)
    maximum_stock = Column(Integer, default=100)
    reorder_point = Column(Integer, default=10)

    # قیمت‌ها
    unit_cost = Column(DECIMAL(12, 0), default=0)
    selling_price = Column(DECIMAL(12, 0), default=0)

    # تأمین کننده
    supplier = Column(String(200))
    supplier_contact = Column(String(100))

    # وضعیت
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PreventiveMaintenance(Base):
    """مدل تعمیرات پیشگیرانه"""
    __tablename__ = 'reception_preventive_maintenance'

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('hotel_rooms.id'))
    equipment_id = Column(Integer, ForeignKey('reception_equipment.id'))

    # اطلاعات برنامه
    maintenance_type = Column(String(50), nullable=False)
    frequency = Column(String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    description = Column(Text)
    checklist = Column(JSON, default=list)

    # زمان‌بندی
    last_performed = Column(DateTime)
    next_due = Column(DateTime, nullable=False)

    # وضعیت
    status = Column(String(20), default='scheduled')  # scheduled, overdue, completed

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    room = relationship("HotelRoom")
    equipment = relationship("Equipment")
