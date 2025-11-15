# app/utils/calculators.py
"""
ماژول محاسبات مالی و آماری سیستم پذیرش
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StayCalculationResult:
    """نتیجه محاسبات اقامت"""
    total_nights: int
    base_amount: Decimal
    tax_amount: Decimal
    service_charge: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    breakdown: List[Dict[str, Any]]

def calculate_stay_amount(check_in: date,
                         check_out: date,
                         room_rate: Decimal,
                         tax_rate: Decimal = Decimal('0.09'),
                         service_rate: Decimal = Decimal('0.01'),
                         discount_percent: Decimal = Decimal('0'),
                         extra_charges: List[Dict] = None) -> StayCalculationResult:
    """
    محاسبه هزینه اقامت

    Args:
        check_in: تاریخ ورود
        check_out: تاریخ خروج
        room_rate: نرخ شبانه اتاق
        tax_rate: نرخ مالیات (پیش‌فرض 9%)
        service_rate: نرخ کارمزد خدمات (پیش‌فرض 1%)
        discount_percent: درصد تخفیف
        extra_charges: هزینه‌های اضافی

    Returns:
        StayCalculationResult: نتیجه محاسبات
    """

    try:
        # محاسبه تعداد شب‌ها
        total_nights = (check_out - check_in).days
        if total_nights <= 0:
            total_nights = 1

        # مبلغ پایه
        base_amount = room_rate * total_nights

        # محاسبه تخفیف
        discount_amount = (base_amount * discount_percent / 100).quantize(Decimal('0.01'), ROUND_HALF_UP)

        # مبلغ پس از تخفیف
        amount_after_discount = base_amount - discount_amount

        # محاسبه مالیات
        tax_amount = (amount_after_discount * tax_rate).quantize(Decimal('0.01'), ROUND_HALF_UP)

        # محاسبه کارمزد خدمات
        service_charge = (amount_after_discount * service_rate).quantize(Decimal('0.01'), ROUND_HALF_UP)

        # جمع کل
        total_amount = amount_after_discount + tax_amount + service_charge

        # افزودن هزینه‌های اضافی
        extra_total = Decimal('0')
        if extra_charges:
            for charge in extra_charges:
                charge_amount = Decimal(str(charge.get('amount', 0)))
                extra_total += charge_amount
                total_amount += charge_amount

        # ایجاد breakdown
        breakdown = [
            {
                'description': f'اتاق ({total_nights} شب)',
                'amount': float(base_amount),
                'type': 'room_charge'
            }
        ]

        if discount_amount > 0:
            breakdown.append({
                'description': f'تخفیف ({discount_percent}%)',
                'amount': float(-discount_amount),
                'type': 'discount'
            })

        if tax_amount > 0:
            breakdown.append({
                'description': f'مالیات ({tax_rate * 100}%)',
                'amount': float(tax_amount),
                'type': 'tax'
            })

        if service_charge > 0:
            breakdown.append({
                'description': f'کارمزد خدمات ({service_rate * 100}%)',
                'amount': float(service_charge),
                'type': 'service_charge'
            })

        if extra_charges:
            for charge in extra_charges:
                breakdown.append({
                    'description': charge.get('description', 'هزینه اضافی'),
                    'amount': float(charge.get('amount', 0)),
                    'type': charge.get('type', 'extra')
                })

        return StayCalculationResult(
            total_nights=total_nights,
            base_amount=base_amount,
            tax_amount=tax_amount,
            service_charge=service_charge,
            discount_amount=discount_amount,
            total_amount=total_amount,
            breakdown=breakdown
        )

    except Exception as e:
        logger.error(f"خطا در محاسبه هزینه اقامت: {e}")
        # بازگشت نتیجه پیش‌فرض در صورت خطا
        return StayCalculationResult(
            total_nights=0,
            base_amount=Decimal('0'),
            tax_amount=Decimal('0'),
            service_charge=Decimal('0'),
            discount_amount=Decimal('0'),
            total_amount=Decimal('0'),
            breakdown=[]
        )

def calculate_tax(amount: Decimal, tax_rate: Decimal = Decimal('0.09')) -> Decimal:
    """
    محاسبه مالیات بر اساس مبلغ

    Args:
        amount: مبلغ پایه
        tax_rate: نرخ مالیات

    Returns:
        Decimal: مقدار مالیات
    """

    try:
        return (amount * tax_rate).quantize(Decimal('0.01'), ROUND_HALF_UP)
    except Exception as e:
        logger.error(f"خطا در محاسبه مالیات: {e}")
        return Decimal('0')

def calculate_discount(amount: Decimal, discount_percent: Decimal) -> Decimal:
    """
    محاسبه مقدار تخفیف

    Args:
        amount: مبلغ پایه
        discount_percent: درصد تخفیف

    Returns:
        Decimal: مقدار تخفیف
    """

    try:
        return (amount * discount_percent / 100).quantize(Decimal('0.01'), ROUND_HALF_UP)
    except Exception as e:
        logger.error(f"خطا در محاسبه تخفیف: {e}")
        return Decimal('0')

def calculate_occupancy_rate(occupied_rooms: int, total_rooms: int) -> float:
    """
    محاسبه نرخ اشغال

    Args:
        occupied_rooms: تعداد اتاق‌های اشغال شده
        total_rooms: تعداد کل اتاق‌ها

    Returns:
        float: نرخ اشغال (بین 0-100)
    """

    try:
        if total_rooms == 0:
            return 0.0

        occupancy = (occupied_rooms / total_rooms) * 100
        return round(occupancy, 2)

    except Exception as e:
        logger.error(f"خطا در محاسبه نرخ اشغال: {e}")
        return 0.0

def calculate_average_daily_rate(total_revenue: Decimal, occupied_rooms: int) -> Decimal:
    """
    محاسبه میانگین نرخ روزانه (ADR)

    Args:
        total_revenue: درآمد کل
        occupied_rooms: تعداد اتاق‌های اشغال شده

    Returns:
        Decimal: میانگین نرخ روزانه
    """

    try:
        if occupied_rooms == 0:
            return Decimal('0')

        adr = total_revenue / occupied_rooms
        return adr.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه ADR: {e}")
        return Decimal('0')

def calculate_revpar(total_revenue: Decimal, total_rooms: int) -> Decimal:
    """
    محاسبه درآمد به ازای هر اتاق موجود (RevPAR)

    Args:
        total_revenue: درآمد کل
        total_rooms: تعداد کل اتاق‌ها

    Returns:
        Decimal: RevPAR
    """

    try:
        if total_rooms == 0:
            return Decimal('0')

        revpar = total_revenue / total_rooms
        return revpar.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه RevPAR: {e}")
        return Decimal('0')

def calculate_room_revenue(room_rates: List[Decimal], occupancy_rates: List[float]) -> Decimal:
    """
    محاسبه درآمد پیش‌بینی شده اتاق‌ها

    Args:
        room_rates: لیست نرخ اتاق‌ها
        occupancy_rates: لیست نرخ اشغال

    Returns:
        Decimal: درآمد پیش‌بینی شده
    """

    try:
        if len(room_rates) != len(occupancy_rates):
            raise ValueError("طول لیست نرخ‌ها و اشغال باید برابر باشد")

        total_revenue = Decimal('0')
        for rate, occupancy in zip(room_rates, occupancy_rates):
            revenue = rate * Decimal(str(occupancy / 100))
            total_revenue += revenue

        return total_revenue.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه درآمد اتاق‌ها: {e}")
        return Decimal('0')

def calculate_early_checkin_charge(check_in_time: datetime,
                                  standard_checkin: datetime,
                                  hourly_rate: Decimal) -> Decimal:
    """
    محاسبه هزینه چک‌این زودتر از موعد

    Args:
        check_in_time: زمان چک‌این واقعی
        standard_checkin: زمان چک‌این استاندارد
        hourly_rate: نرخ ساعتی

    Returns:
        Decimal: هزینه چک‌این زودهنگام
    """

    try:
        if check_in_time >= standard_checkin:
            return Decimal('0')

        # محاسبه اختلاف زمان به ساعت
        time_diff = standard_checkin - check_in_time
        hours_early = time_diff.total_seconds() / 3600

        # محاسبه هزینه (حداقل 1 ساعت)
        hours_charged = max(1, int(hours_early))
        charge = hourly_rate * hours_charged

        return charge.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه هزینه چک‌این زودهنگام: {e}")
        return Decimal('0')

def calculate_late_checkout_charge(check_out_time: datetime,
                                  standard_checkout: datetime,
                                  hourly_rate: Decimal) -> Decimal:
    """
    محاسبه هزینه چک‌اوت دیرتر از موعد

    Args:
        check_out_time: زمان چک‌اوت واقعی
        standard_checkout: زمان چک‌اوت استاندارد
        hourly_rate: نرخ ساعتی

    Returns:
        Decimal: هزینه چک‌اوت دیرهنگام
    """

    try:
        if check_out_time <= standard_checkout:
            return Decimal('0')

        # محاسبه اختلاف زمان به ساعت
        time_diff = check_out_time - standard_checkout
        hours_late = time_diff.total_seconds() / 3600

        # محاسبه هزینه (حداقل 1 ساعت)
        hours_charged = max(1, int(hours_late))
        charge = hourly_rate * hours_charged

        return charge.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه هزینه چک‌اوت دیرهنگام: {e}")
        return Decimal('0')

def calculate_minibar_charges(items: List[Dict]) -> Decimal:
    """
    محاسبه هزینه‌های مینی‌بار

    Args:
        items: لیست آیتم‌های مصرف شده

    Returns:
        Decimal: جمع هزینه مینی‌بار
    """

    try:
        total = Decimal('0')
        for item in items:
            quantity = Decimal(str(item.get('quantity', 0)))
            price = Decimal(str(item.get('price', 0)))
            total += quantity * price

        return total.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه هزینه مینی‌بار: {e}")
        return Decimal('0')

def calculate_meal_plan_charges(guests: int,
                               nights: int,
                               meal_plan_rate: Decimal) -> Decimal:
    """
    محاسبه هزینه پنشن غذایی

    Args:
        guests: تعداد مهمانان
        nights: تعداد شب‌ها
        meal_plan_rate: نرخ پنشن به ازای هر نفر در شب

    Returns:
        Decimal: جمع هزینه پنشن
    """

    try:
        total = guests * nights * meal_plan_rate
        return total.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه هزینه پنشن: {e}")
        return Decimal('0')

def calculate_commission(amount: Decimal, commission_rate: Decimal) -> Tuple[Decimal, Decimal]:
    """
    محاسبه کارمزد و مبلغ خالص

    Args:
        amount: مبلغ کل
        commission_rate: نرخ کارمزد

    Returns:
        Tuple[Decimal, Decimal]: (کارمزد, مبلغ خالص)
    """

    try:
        commission = (amount * commission_rate).quantize(Decimal('0.01'), ROUND_HALF_UP)
        net_amount = amount - commission

        return commission, net_amount

    except Exception as e:
        logger.error(f"خطا در محاسبه کارمزد: {e}")
        return Decimal('0'), Decimal('0')

def calculate_occupancy_forecast(historical_data: List[Dict],
                               forecast_days: int = 30) -> List[Dict]:
    """
    پیش‌بینی نرخ اشغال بر اساس داده‌های تاریخی

    Args:
        historical_data: داده‌های تاریخی اشغال
        forecast_days: تعداد روزهای پیش‌بینی

    Returns:
        List[Dict]: پیش‌بینی نرخ اشغال
    """

    try:
        if not historical_data:
            return []

        # محاسبه میانگین اشغال برای هر روز از هفته
        daily_averages = {}
        for record in historical_data:
            day_of_week = record['date'].weekday()
            occupancy = record['occupancy_rate']

            if day_of_week not in daily_averages:
                daily_averages[day_of_week] = []

            daily_averages[day_of_week].append(occupancy)

        # محاسبه میانگین برای هر روز
        for day in daily_averages:
            daily_averages[day] = sum(daily_averages[day]) / len(daily_averages[day])

        # تولید پیش‌بینی
        forecast = []
        today = date.today()

        for i in range(forecast_days):
            forecast_date = today + timedelta(days=i)
            day_of_week = forecast_date.weekday()

            # استفاده از میانگین تاریخی برای پیش‌بینی
            predicted_occupancy = daily_averages.get(day_of_week, 50.0)  # پیش‌فرض 50%

            # اعمال فاکتورهای فصلی (ساده)
            month = forecast_date.month
            seasonal_factor = 1.0

            if month in [6, 7, 8]:  # تابستان
                seasonal_factor = 1.2
            elif month in [12, 1, 2]:  # زمستان
                seasonal_factor = 0.8

            predicted_occupancy *= seasonal_factor
            predicted_occupancy = min(100.0, max(0.0, predicted_occupancy))

            forecast.append({
                'date': forecast_date,
                'predicted_occupancy': round(predicted_occupancy, 2),
                'confidence': 0.7  # ضریب اطمینان
            })

        return forecast

    except Exception as e:
        logger.error(f"خطا در پیش‌بینی اشغال: {e}")
        return []

def calculate_optimal_room_rate(current_occupancy: float,
                               demand_trend: float,
                               base_rate: Decimal,
                               min_rate: Decimal,
                               max_rate: Decimal) -> Decimal:
    """
    محاسبه نرخ بهینه اتاق بر اساس اشغال و تقاضا

    Args:
        current_occupancy: نرخ اشغال فعلی
        demand_trend: روند تقاضا (مثبت یا منفی)
        base_rate: نرخ پایه
        min_rate: حداقل نرخ
        max_rate: حداکثر نرخ

    Returns:
        Decimal: نرخ بهینه
    """

    try:
        # فاکتور تعدیل بر اساس اشغال
        occupancy_factor = 1.0

        if current_occupancy > 80:  # اشغال بالا
            occupancy_factor = 1.2
        elif current_occupancy < 40:  # اشغال پایین
            occupancy_factor = 0.8

        # فاکتور تعدیل بر اساس روند تقاضا
        demand_factor = 1.0 + (demand_trend / 100)

        # محاسبه نرخ بهینه
        optimal_rate = base_rate * Decimal(str(occupancy_factor)) * Decimal(str(demand_factor))

        # اعمال محدودیت‌های حداقل و حداکثر
        optimal_rate = max(min_rate, min(max_rate, optimal_rate))

        return optimal_rate.quantize(Decimal('0.01'), ROUND_HALF_UP)

    except Exception as e:
        logger.error(f"خطا در محاسبه نرخ بهینه: {e}")
        return base_rate
