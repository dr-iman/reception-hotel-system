# app/models/reception/notification_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Notification(Base):
    """مدل اطلاع‌رسانی بین سیستم‌ها"""
    __tablename__ = 'reception_notifications'

    id = Column(Integer, primary_key=True)

    # اطلاعات پیام
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # info, warning, alert, system
    category = Column(String(50))  # reservation, guest, housekeeping, maintenance, financial

    # فرستنده و گیرنده
    from_system = Column(String(50), nullable=False)  # reservation, reception
    from_user_id = Column(Integer)  # کاربر فرستنده در سیستم مبدا
    to_user_id = Column(Integer)  # کاربر گیرنده در سیستم مقصد
    to_department = Column(String(50))  # در صورت ارسال به بخش

    # وضعیت
    status = Column(String(20), default='unread')  # unread, read, archived
    priority = Column(String(20), default='normal')  # low, normal, high

    # زمان‌ها
    sent_at = Column(DateTime, default=datetime.now)
    read_at = Column(DateTime)
    expires_at = Column(DateTime)

    # اقدامات
    action_required = Column(Boolean, default=False)
    action_url = Column(String(500))  # URL برای اقدام سریع
    action_label = Column(String(100))

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    sync_records = relationship("SyncRecord", back_populates="notification")

class SyncRecord(Base):
    """مدل رکوردهای همگام‌سازی با سیستم رزرواسیون"""
    __tablename__ = 'reception_sync_records'

    id = Column(Integer, primary_key=True)
    notification_id = Column(Integer, ForeignKey('reception_notifications.id'))

    # اطلاعات همگام‌سازی
    sync_type = Column(String(50), nullable=False)  # guest_arrival, guest_departure, room_status, payment
    source_system = Column(String(50), nullable=False)  # reservation, reception
    target_system = Column(String(50), nullable=False)

    # داده‌های همگام‌سازی
    data_payload = Column(JSON, nullable=False)
    sync_direction = Column(String(20), nullable=False)  # send, receive

    # وضعیت
    status = Column(String(20), default='pending')  # pending, processing, completed, failed
    retry_count = Column(Integer, default=0)
    error_message = Column(Text)

    # زمان‌ها
    sync_started = Column(DateTime)
    sync_completed = Column(DateTime)

    created_at = Column(DateTime, default=datetime.now)

    # روابط
    notification = relationship("Notification", back_populates="sync_records")
