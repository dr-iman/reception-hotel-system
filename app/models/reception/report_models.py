# app/models/reception/report_models.py
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, DECIMAL, DateTime, Date, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class DailyReport(Base):
    """مدل گزارش روزانه پذیرش"""
    __tablename__ = 'reception_daily_reports'

    id = Column(Integer, primary_key=True)
    report_date = Column(Date, nullable=False, unique=True)
    generated_by = Column(Integer, nullable=False)

    # آمار مهمانان
    total_guests = Column(Integer, default=0)
    new_arrivals = Column(Integer, default=0)
    departures = Column(Integer, default=0)
    stayovers = Column(Integer, default=0)
    no_shows = Column(Integer, default=0)
    walkins = Column(Integer, default=0)

    # آمار اتاق‌ها
    total_rooms = Column(Integer, default=0)
    occupied_rooms = Column(Integer, default=0)
    vacant_rooms = Column(Integer, default=0)
    out_of_order_rooms = Column(Integer, default=0)
    occupancy_rate = Column(DECIMAL(5, 2), default=0)

    # آمار مالی
    total_revenue = Column(DECIMAL(15, 0), default=0)
    room_revenue = Column(DECIMAL(15, 0), default=0)
    other_revenue = Column(DECIMAL(15, 0), default=0)
    average_rate = Column(DECIMAL(12, 0), default=0)

    # آمار عملیاتی
    housekeeping_tasks = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    maintenance_requests = Column(Integer, default=0)
    resolved_requests = Column(Integer, default=0)

    # یادداشت‌ها
    manager_notes = Column(Text)
    issues_today = Column(Text)
    plans_tomorrow = Column(Text)

    generated_at = Column(DateTime, default=datetime.now)

    # روابط
    details = relationship("DailyReportDetail", back_populates="report")

class DailyReportDetail(Base):
    """مدل جزئیات گزارش روزانه"""
    __tablename__ = 'reception_daily_report_details'

    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reception_daily_reports.id'), nullable=False)

    # نوع جزئیات
    detail_type = Column(String(50), nullable=False)  # vip_guests, group_arrivals, special_events, etc.
    description = Column(Text, nullable=False)
    data = Column(JSON)

    # روابط
    report = relationship("DailyReport", back_populates="details")
