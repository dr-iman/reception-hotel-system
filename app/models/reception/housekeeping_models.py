# app/models/reception/housekeeping_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class HousekeepingTask(Base):
    """مدل وظایف خانه‌داری"""
    __tablename__ = 'reception_housekeeping_tasks'

    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('hotel_rooms.id'), nullable=False)
    assigned_to = Column(Integer, ForeignKey('reception_staff.id'))  # کارمند محول شده

    # اطلاعات وظیفه
    task_type = Column(String(20), nullable=False)  # cleaning, inspection, turndown, deep_clean
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    status = Column(String(20), default='pending')  # pending, assigned, in_progress, completed, verified

    # زمان‌بندی
    scheduled_time = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    verified_at = Column(DateTime)

    # جزئیات نظافت
    cleaning_notes = Column(Text)
    inspection_notes = Column(Text)
    quality_score = Column(Integer)  # امتیاز کیفیت (1-5)

    # منابع مورد نیاز
    required_supplies = Column(JSON, default=list)
    special_equipment = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    room = relationship("HotelRoom")
    staff = relationship("Staff")
    checklist_items = relationship("HousekeepingChecklist", back_populates="task")

class HousekeepingChecklist(Base):
    """مدل چک‌لیست نظافت اتاق"""
    __tablename__ = 'reception_housekeeping_checklists'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('reception_housekeeping_tasks.id'), nullable=False)

    # آیتم‌های چک‌لیست
    item_name = Column(String(100), nullable=False)
    category = Column(String(50))  # bathroom, bedroom, amenities, etc.
    status = Column(String(20), default='pending')  # pending, completed, failed
    notes = Column(Text)

    # تصاویر بازرسی
    before_image = Column(String(500))
    after_image = Column(String(500))

    completed_at = Column(DateTime)

    # روابط
    task = relationship("HousekeepingTask", back_populates="checklist_items")

class HousekeepingSchedule(Base):
    """مدل برنامه‌ریزی خانه‌داری"""
    __tablename__ = 'reception_housekeeping_schedules'

    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey('reception_staff.id'), nullable=False)

    # برنامه روزانه
    schedule_date = Column(Date, nullable=False)
    shift_type = Column(String(20), nullable=False)  # morning, evening, night
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # مناطق مسئولیت
    assigned_rooms = Column(JSON, default=list)  # لیست اتاق‌های محول شده
    assigned_floors = Column(JSON, default=list)  # لیست طبقات محول شده

    # وضعیت
    status = Column(String(20), default='scheduled')  # scheduled, in_progress, completed

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    staff = relationship("Staff")

class LostAndFound(Base):
    """مدل اشیاء گمشده و پیداشده"""
    __tablename__ = 'reception_lost_and_found'

    id = Column(Integer, primary_key=True)

    # اطلاعات شیء
    item_name = Column(String(200), nullable=False)
    item_description = Column(Text)
    item_category = Column(String(50))  # electronics, clothing, documents, jewelry, etc.
    item_value = Column(String(50))  # low, medium, high

    # اطلاعات پیدا شدن
    found_location = Column(String(200))
    found_date = Column(DateTime, nullable=False)
    found_by = Column(Integer)  # کارمند پیدا کننده

    # اطلاعات تحویل
    guest_id = Column(Integer, ForeignKey('reception_guests.id'))
    claimed_date = Column(DateTime)
    claimed_by = Column(String(100))  # نام شخص تحویل‌گیرنده

    # وضعیت
    status = Column(String(20), default='found')  # found, claimed, disposed

    # تصاویر
    item_images = Column(JSON, default=list)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    guest = relationship("Guest")
