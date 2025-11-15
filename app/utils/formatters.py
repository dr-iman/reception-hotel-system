# app/utils/formatters.py
"""
ماژول فرمت‌دهی داده‌ها برای نمایش در رابط کاربری
"""

import re
from datetime import datetime, date
from decimal import Decimal
from typing import Union, Optional
from babel.dates import format_date as babel_format_date
import locale

try:
    locale.setlocale(locale.LC_ALL, 'fa_IR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'fa_IR')
    except locale.Error:
        pass  # از فرمت‌دهی پیش‌فرض استفاده می‌شود

def format_currency(amount: Union[Decimal, int, float],
                   currency: str = "IRT",
                   include_symbol: bool = True) -> str:
    """
    فرمت‌دهی مبلغ به فرمت پولی فارسی

    Args:
        amount: مبلغ
        currency: واحد پول (IRT: تومان, IRR: ریال)
        include_symbol: آیا نماد پول نمایش داده شود؟

    Returns:
        str: مبلغ فرمت شده
    """

    try:
        if isinstance(amount, (int, float)):
            amount = Decimal(str(amount))

        # تبدیل به تومان اگر ریال باشد
        if currency == "IRT" and amount >= 10:
            amount = amount / 10

        # فرمت‌دهی با جداکننده هزارگان
        formatted = "{:,.0f}".format(amount)

        # جایگزینی کاما با جداکننده فارسی
        formatted = formatted.replace(',', '،')

        # افزودن نماد پول
        if include_symbol:
            if currency == "IRT":
                formatted += " تومان"
            elif currency == "IRR":
                formatted += " ریال"
            else:
                formatted += f" {currency}"

        return formatted

    except (ValueError, TypeError):
        return "۰"

def format_date(date_obj: Union[date, datetime, str],
               format_type: str = "medium") -> str:
    """
    فرمت‌دهی تاریخ به فارسی

    Args:
        date_obj: شیء تاریخ
        format_type: نوع فرمت (short, medium, long, full)

    Returns:
        str: تاریخ فرمت شده به فارسی
    """

    if not date_obj:
        return ""

    try:
        # تبدیل رشته به تاریخ اگر لازم باشد
        if isinstance(date_obj, str):
            if 'T' in date_obj:
                date_obj = datetime.fromisoformat(date_obj.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_obj, '%Y-%m-%d')

        # فرمت‌های مختلف
        formats = {
            'short': 'yyyy/MM/dd',
            'medium': 'yyyy/MM/dd',
            'long': 'd MMMM yyyy',
            'full': 'EEEE d MMMM yyyy'
        }

        format_str = formats.get(format_type, 'yyyy/MM/dd')

        try:
            # استفاده از babel برای فرمت‌دهی فارسی
            return babel_format_date(date_obj, format_str, locale='fa_IR')
        except:
            # فرمت‌دهی ساده در صورت خطا
            if format_type == 'short':
                return date_obj.strftime('%Y/%m/%d')
            elif format_type == 'medium':
                return date_obj.strftime('%Y/%m/%d')
            else:
                return date_obj.strftime('%Y/%m/%d')

    except (ValueError, TypeError) as e:
        return str(date_obj)

def format_time(time_obj: Union[datetime, str]) -> str:
    """
    فرمت‌دهی زمان به فارسی

    Args:
        time_obj: شیء زمان

    Returns:
        str: زمان فرمت شده
    """

    if not time_obj:
        return ""

    try:
        if isinstance(time_obj, str):
            if 'T' in time_obj:
                time_obj = datetime.fromisoformat(time_obj.replace('Z', '+00:00'))
            else:
                time_obj = datetime.strptime(time_obj, '%H:%M:%S')

        return time_obj.strftime('%H:%M')

    except (ValueError, TypeError):
        return str(time_obj)

def format_datetime(datetime_obj: Union[datetime, str],
                   date_format: str = "medium",
                   time_format: str = "short") -> str:
    """
    فرمت‌دهی تاریخ و زمان به فارسی

    Args:
        datetime_obj: شیء تاریخ و زمان
        date_format: فرمت تاریخ
        time_format: فرمت زمان

    Returns:
        str: تاریخ و زمان فرمت شده
    """

    if not datetime_obj:
        return ""

    try:
        if isinstance(datetime_obj, str):
            datetime_obj = datetime.fromisoformat(datetime_obj.replace('Z', '+00:00'))

        date_part = format_date(datetime_obj, date_format)
        time_part = format_time(datetime_obj)

        return f"{date_part} - {time_part}"

    except (ValueError, TypeError):
        return str(datetime_obj)

def format_phone_number(phone: str) -> str:
    """
    فرمت‌دهی شماره تلفن به فرمت استاندارد فارسی

    Args:
        phone: شماره تلفن

    Returns:
        str: شماره تلفن فرمت شده
    """

    if not phone:
        return ""

    # حذف کاراکترهای غیرعددی
    cleaned = re.sub(r'[^\d]', '', phone)

    if len(cleaned) == 11:
        # فرمت: 0912 345 6789
        return f"{cleaned[0:4]} {cleaned[4:7]} {cleaned[7:]}"
    elif len(cleaned) == 10:
        # فرمت: 021 12345678
        return f"{cleaned[0:3]} {cleaned[3:]}"
    else:
        return phone

def format_national_id(national_id: str) -> str:
    """
    فرمت‌دهی کد ملی با جداکننده

    Args:
        national_id: کد ملی

    Returns:
        str: کد ملی فرمت شده
    """

    if not national_id:
        return ""

    cleaned = re.sub(r'[^\d]', '', national_id)

    if len(cleaned) == 10:
        return f"{cleaned[0:3]}-{cleaned[3:6]}-{cleaned[6:]}"
    else:
        return national_id

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    کوتاه کردن متن با اضافه کردن پسوند

    Args:
        text: متن اصلی
        max_length: حداکثر طول
        suffix: پسوند برای متن کوتاه شده

    Returns:
        str: متن کوتاه شده
    """

    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix

def format_duration(minutes: int) -> str:
    """
    فرمت‌دهی مدت زمان به ساعت و دقیقه

    Args:
        minutes: تعداد دقیقه

    Returns:
        str: مدت زمان فرمت شده
    """

    if minutes < 60:
        return f"{minutes} دقیقه"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours} ساعت"
    else:
        return f"{hours} ساعت و {remaining_minutes} دقیقه"

def format_percentage(value: float, decimals: int = 1) -> str:
    """
    فرمت‌دهی درصد

    Args:
        value: مقدار درصد (بین 0-100 یا 0-1)
        decimals: تعداد اعشار

    Returns:
        str: درصد فرمت شده
    """

    # اگر مقدار بین 0-1 باشد، به 0-100 تبدیل می‌شود
    if 0 <= value <= 1:
        value = value * 100

    return f"{value:.{decimals}f}%"

def format_file_size(size_bytes: int) -> str:
    """
    فرمت‌دهی سایز فایل

    Args:
        size_bytes: سایز به بایت

    Returns:
        str: سایز فرمت شده
    """

    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"

def format_room_number(room_number: str) -> str:
    """
    فرمت‌دهی شماره اتاق

    Args:
        room_number: شماره اتاق

    Returns:
        str: شماره اتاق فرمت شده
    """

    if not room_number:
        return ""

    # اضافه کردن پیشوند "اتاق" اگر وجود ندارد
    if not room_number.startswith('اتاق'):
        return f"اتاق {room_number}"

    return room_number

def format_guest_name(first_name: str, last_name: str) -> str:
    """
    فرمت‌دهی نام کامل مهمان

    Args:
        first_name: نام
        last_name: نام خانوادگی

    Returns:
        str: نام کامل فرمت شده
    """

    if not first_name and not last_name:
        return "مهمان"

    return f"{first_name or ''} {last_name or ''}".strip()

def format_stay_period(check_in: date, check_out: date) -> str:
    """
    فرمت‌دهی دوره اقامت

    Args:
        check_in: تاریخ ورود
        check_out: تاریخ خروج

    Returns:
        str: دوره اقامت فرمت شده
    """

    if not check_in or not check_out:
        return ""

    nights = (check_out - check_in).days
    check_in_fa = format_date(check_in, 'medium')
    check_out_fa = format_date(check_out, 'medium')

    return f"{check_in_fa} تا {check_out_fa} ({nights} شب)"

def convert_english_to_persian_numbers(text: str) -> str:
    """
    تبدیل اعداد انگلیسی به فارسی

    Args:
        text: متن حاوی اعداد

    Returns:
        str: متن با اعداد فارسی
    """

    if not text:
        return ""

    # جدول تبدیل اعداد
    english_to_persian = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }

    result = ""
    for char in text:
        result += english_to_persian.get(char, char)

    return result

def convert_persian_to_english_numbers(text: str) -> str:
    """
    تبدیل اعداد فارسی به انگلیسی

    Args:
        text: متن حاوی اعداد فارسی

    Returns:
        str: متن با اعداد انگلیسی
    """

    if not text:
        return ""

    # جدول تبدیل اعداد
    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }

    result = ""
    for char in text:
        result += persian_to_english.get(char, char)

    return result
