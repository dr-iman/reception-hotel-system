# app/models/reception/staff_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Staff(Base):
    """مدل پرسنل هتل"""
    __tablename__ = 'reception_staff'

    id = Column(Integer, primary_key=True)

    # اطلاعات شخصی
    national_id = Column(String(20), unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(10))
    date_of_birth = Column(Date)

    # اطلاعات تماس
    phone = Column(String(15), nullable=False)
    email = Column(String(100))
    address = Column(Text)
    emergency_contact = Column(String(100))
    emergency_phone = Column(String(15))

    # اطلاعات شغلی
    employee_id = Column(String(20), unique=True)
    department = Column(String(50), nullable=False)  # reception, housekeeping, maintenance, etc.
    position = Column(String(100), nullable=False)
    employment_type = Column(String(20), default='full_time')  # full_time, part_time, contract
    hire_date = Column(Date, nullable=False)

    # وضعیت
    is_active = Column(Boolean, default=True)
    termination_date = Column(Date)
    termination_reason = Column(Text)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    user_account = relationship("User", back_populates="staff", uselist=False)
    housekeeping_tasks = relationship("HousekeepingTask", back_populates="staff")
    maintenance_work = relationship("MaintenanceWorkOrder", back_populates="technician")

class User(Base):
    """مدل کاربران سیستم"""
    __tablename__ = 'reception_users'

    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey('reception_staff.id'), unique=True)

    # اطلاعات ورود
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    # سطوح دسترسی
    role = Column(String(50), nullable=False)  # receptionist, housekeeping, maintenance, manager, admin
    permissions = Column(JSON, default=list)

    # وضعیت
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)

    # تنظیمات
    preferences = Column(JSON, default=dict)
    language = Column(String(10), default='fa')

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # روابط
    staff = relationship("Staff", back_populates="user_account")
    activity_logs = relationship("UserActivityLog", back_populates="user")

class UserActivityLog(Base):
    """مدل لاگ فعالیت‌های کاربران"""
    __tablename__ = 'reception_user_activity_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('reception_users.id'), nullable=False)

    # اطلاعات فعالیت
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    details = Column(JSON)

    # اطلاعات سیستم
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(100))

    created_at = Column(DateTime, default=datetime.now, index=True)

    # روابط
    user = relationship("User", back_populates="activity_logs")
