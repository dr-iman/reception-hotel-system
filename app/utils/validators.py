# app/utils/validators.py
"""
ماژول اعتبارسنجی داده‌های ورودی سیستم
"""

import re
import logging
from datetime import datetime, date
from typing import Union, Optional, Tuple
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)

def validate_national_id(national_id: str) -> Tuple[bool, str]:
    """
    اعتبارسنجی کد ملی ایران

    Args:
        national_id: کد ملی (10 رقمی)

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if not national_id:
        return False, "کد ملی نمی‌تواند خالی باشد"

    # حذف فاصله و کاراکترهای غیرعددی
    national_id = re.sub(r'[^\d]', '', national_id)

    # بررسی طول
    if len(national_id) != 10:
        return False, "کد ملی باید 10 رقم باشد"

    # بررسی اینکه تمام ارقام یکسان نباشند
    if len(set(national_id)) == 1:
        return False, "کد ملی معتبر نیست"

    try:
        # الگوریتم اعتبارسنجی کد ملی
        check = int(national_id[9])
        s = sum(int(national_id[i]) * (10 - i) for i in range(9)) % 11
        valid = (s < 2 and check == s) or (s >= 2 and check == 11 - s)

        if not valid:
            return False, "کد ملی معتبر نیست"

        return True, "کد ملی معتبر است"

    except (ValueError, IndexError) as e:
        logger.error(f"خطا در اعتبارسنجی کد ملی: {e}")
        return False, "خطا در پردازش کد ملی"

def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    اعتبارسنجی شماره تلفن همراه ایران

    Args:
        phone: شماره تلفن

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if not phone:
        return False, "شماره تلفن نمی‌تواند خالی باشد"

    # حذف فاصله و کاراکترهای غیرعددی
    cleaned_phone = re.sub(r'[^\d]', '', phone)

    # بررسی طول
    if len(cleaned_phone) != 11:
        return False, "شماره تلفن باید 11 رقم باشد"

    # بررسی پیش‌شماره
    if not cleaned_phone.startswith('09'):
        return False, "شماره تلفن باید با 09 شروع شود"

    # بررسی الگوی تلفن
    pattern = r'^09[0-9]{9}$'
    if not re.match(pattern, cleaned_phone):
        return False, "فرمت شماره تلفن معتبر نیست"

    return True, "شماره تلفن معتبر است"

def validate_email(email: str) -> Tuple[bool, str]:
    """
    اعتبارسنجی آدرس ایمیل

    Args:
        email: آدرس ایمیل

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if not email:
        return True, "ایمیل اختیاری است"  # ایمیل اختیاری در نظر گرفته شده

    # الگوی استاندارد ایمیل
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, "فرمت ایمیل معتبر نیست"

    # بررسی دامنه‌های معروف
    popular_domains = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'icloud.com', 'protonmail.com', 'mail.com'
    ]

    domain = email.split('@')[1].lower()
    if domain not in popular_domains and not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
        return False, "دامنه ایمیل معتبر نیست"

    return True, "ایمیل معتبر است"

def validate_credit_card(card_number: str, expiry_date: str = None, cvv: str = None) -> Tuple[bool, str]:
    """
    اعتبارسنجی شماره کارت بانکی (الگوریتم Luhn)

    Args:
        card_number: شماره کارت (16 رقمی)
        expiry_date: تاریخ انقضا (MM/YY)
        cvv: کد CVV

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if not card_number:
        return False, "شماره کارت نمی‌تواند خالی باشد"

    # حذف فاصله و کاراکترهای غیرعددی
    cleaned_card = re.sub(r'[^\d]', '', card_number)

    # بررسی طول
    if len(cleaned_card) not in [16, 15]:  # 16 رقم برای بیشتر کارت‌ها، 15 برای American Express
        return False, "شماره کارت باید 16 رقم باشد"

    try:
        # الگوریتم Luhn
        digits = [int(d) for d in cleaned_card]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        total = sum(odd_digits)

        for digit in even_digits:
            total += sum([int(d) for d in str(digit * 2)])

        if total % 10 != 0:
            return False, "شماره کارت معتبر نیست"

        # اعتبارسنجی تاریخ انقضا (اگر ارائه شده)
        if expiry_date:
            if not validate_expiry_date(expiry_date):
                return False, "تاریخ انقضا معتبر نیست"

        # اعتبارسنجی CVV (اگر ارائه شده)
        if cvv:
            if not re.match(r'^\d{3,4}$', cvv):
                return False, "CVV باید 3 یا 4 رقم باشد"

        return True, "شماره کارت معتبر است"

    except (ValueError, IndexError) as e:
        logger.error(f"خطا در اعتبارسنجی کارت بانکی: {e}")
        return False, "خطا در پردازش شماره کارت"

def validate_expiry_date(expiry_date: str) -> bool:
    """
    اعتبارسنجی تاریخ انقضای کارت بانکی

    Args:
        expiry_date: تاریخ انقضا به فرمت MM/YY

    Returns:
        bool: معتبر بودن
    """

    try:
        if not re.match(r'^\d{2}/\d{2}$', expiry_date):
            return False

        month, year = map(int, expiry_date.split('/'))

        # بررسی ماه
        if month < 1 or month > 12:
            return False

        # تبدیل سال به کامل
        full_year = 2000 + year

        # ایجاد تاریخ انقضا (آخرین روز ماه)
        from datetime import datetime
        import calendar

        last_day = calendar.monthrange(full_year, month)[1]
        expiry = datetime(full_year, month, last_day)

        # بررسی اینکه تاریخ انقضا گذشته نباشد
        return expiry >= datetime.now()

    except (ValueError, IndexError):
        return False

def validate_date_range(start_date: Union[date, datetime],
                       end_date: Union[date, datetime],
                       allow_same_day: bool = False) -> Tuple[bool, str]:
    """
    اعتبارسنجی محدوده تاریخ

    Args:
        start_date: تاریخ شروع
        end_date: تاریخ پایان
        allow_same_day: آیا همان روز مجاز است؟

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if not start_date or not end_date:
        return False, "تاریخ شروع و پایان باید مشخص باشد"

    # تبدیل به date اگر datetime باشد
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    # بررسی اینکه تاریخ شروع قبل از پایان باشد
    if start_date > end_date:
        return False, "تاریخ شروع باید قبل از تاریخ پایان باشد"

    # بررسی اینکه تاریخ‌ها در گذشته نباشند (اختیاری)
    today = date.today()
    if start_date < today:
        return False, "تاریخ شروع نمی‌تواند در گذشته باشد"

    # بررسی حداقل اقامت
    min_stay_days = 1
    if (end_date - start_date).days < min_stay_days:
        return False, f"حداقل اقامت {min_stay_days} شب می‌باشد"

    # بررسی حداکثر اقامت
    max_stay_days = 30
    if (end_date - start_date).days > max_stay_days:
        return False, f"حداکثر اقامت {max_stay_days} شب می‌باشد"

    return True, "محدوده تاریخ معتبر است"

def validate_amount(amount: Union[str, int, float, Decimal],
                   min_amount: Decimal = None,
                   max_amount: Decimal = None) -> Tuple[bool, str]:
    """
    اعتبارسنجی مبلغ مالی

    Args:
        amount: مبلغ
        min_amount: حداقل مبلغ مجاز
        max_amount: حداکثر مبلغ مجاز

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if amount is None:
        return False, "مبلغ نمی‌تواند خالی باشد"

    try:
        # تبدیل به Decimal
        if isinstance(amount, (int, float)):
            amount_decimal = Decimal(str(amount))
        elif isinstance(amount, str):
            # حذف کاما و کاراکترهای غیرعددی
            cleaned_amount = re.sub(r'[^\d.]', '', amount)
            amount_decimal = Decimal(cleaned_amount)
        elif isinstance(amount, Decimal):
            amount_decimal = amount
        else:
            return False, "فرمت مبلغ معتبر نیست"

        # بررسی مثبت بودن
        if amount_decimal <= 0:
            return False, "مبلغ باید بزرگتر از صفر باشد"

        # بررسی حداقل مبلغ
        if min_amount is not None and amount_decimal < min_amount:
            return False, f"مبلغ نمی‌تواند کمتر از {format_currency(min_amount)} باشد"

        # بررسی حداکثر مبلغ
        if max_amount is not None and amount_decimal > max_amount:
            return False, f"مبلغ نمی‌تواند بیشتر از {format_currency(max_amount)} باشد"

        # بررسی اعشار (حداکثر 2 رقم اعشار)
        if abs(amount_decimal.as_tuple().exponent) > 2:
            return False, "مبلغ می‌تواند حداکثر 2 رقم اعشار داشته باشد"

        return True, "مبلغ معتبر است"

    except (InvalidOperation, ValueError) as e:
        logger.error(f"خطا در اعتبارسنجی مبلغ: {e}")
        return False, "فرمت مبلغ معتبر نیست"

def validate_passport_number(passport_number: str) -> Tuple[bool, str]:
    """
    اعتبارسنجی شماره پاسپورت

    Args:
        passport_number: شماره پاسپورت

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if not passport_number:
        return True, "پاسپورت اختیاری است"

    # الگوی پایه پاسپورت (می‌تواند بر اساس کشور متفاوت باشد)
    pattern = r'^[A-Z0-9]{6,9}$'

    if not re.match(pattern, passport_number.upper()):
        return False, "فرمت شماره پاسپورت معتبر نیست"

    return True, "شماره پاسپورت معتبر است"

def validate_birth_date(birth_date: date) -> Tuple[bool, str]:
    """
    اعتبارسنجی تاریخ تولد

    Args:
        birth_date: تاریخ تولد

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if not birth_date:
        return False, "تاریخ تولد باید مشخص باشد"

    today = date.today()

    # بررسی اینکه تاریخ تولد در آینده نباشد
    if birth_date > today:
        return False, "تاریخ تولد نمی‌تواند در آینده باشد"

    # بررسی حداقل سن (18 سال)
    min_age = 18
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    if age < min_age:
        return False, f"حداقل سن برای رزرو {min_age} سال می‌باشد"

    # بررسی حداکثر سن معقول (120 سال)
    max_age = 120
    if age > max_age:
        return False, "تاریخ تولد معتبر نیست"

    return True, "تاریخ تولد معتبر است"

def validate_room_capacity(adults: int, children: int, room_capacity: int) -> Tuple[bool, str]:
    """
    اعتبارسنجی ظرفیت اتاق

    Args:
        adults: تعداد بزرگسالان
        children: تعداد کودکان
        room_capacity: ظرفیت اتاق

    Returns:
        Tuple[bool, str]: (معتبر بودن, پیغام خطا)
    """

    if adults < 1:
        return False, "حداقل یک بزرگسال باید وجود داشته باشد"

    if adults + children > room_capacity:
        return False, f"تعداد مهمانان بیشتر از ظرفیت اتاق ({room_capacity} نفر) است"

    if adults < 0 or children < 0:
        return False, "تعداد مهمانان نمی‌تواند منفی باشد"

    return True, "ظرفیت اتاق معتبر است"

# تابع کمکی برای اعتبارسنجی چندگانه
def validate_guest_data(guest_data: dict) -> Tuple[bool, dict]:
    """
    اعتبارسنجی جامع داده‌های مهمان

    Args:
        guest_data: دیکشنری شامل داده‌های مهمان

    Returns:
        Tuple[bool, dict]: (معتبر بودن تمام فیلدها, دیکشنری خطاها)
    """

    errors = {}

    # اعتبارسنجی نام
    first_name = guest_data.get('first_name', '').strip()
    last_name = guest_data.get('last_name', '').strip()

    if not first_name:
        errors['first_name'] = "نام نمی‌تواند خالی باشد"
    elif len(first_name) < 2:
        errors['first_name'] = "نام باید حداقل 2 کاراکتر باشد"

    if not last_name:
        errors['last_name'] = "نام خانوادگی نمی‌تواند خالی باشد"
    elif len(last_name) < 2:
        errors['last_name'] = "نام خانوادگی باید حداقل 2 کاراکتر باشد"

    # اعتبارسنجی کد ملی
    national_id = guest_data.get('national_id', '')
    if national_id:
        is_valid, msg = validate_national_id(national_id)
        if not is_valid:
            errors['national_id'] = msg

    # اعتبارسنجی تلفن
    phone = guest_data.get('phone', '')
    if phone:
        is_valid, msg = validate_phone(phone)
        if not is_valid:
            errors['phone'] = msg

    # اعتبارسنجی ایمیل
    email = guest_data.get('email', '')
    if email:
        is_valid, msg = validate_email(email)
        if not is_valid:
            errors['email'] = msg

    # اعتبارسنجی تاریخ تولد
    birth_date = guest_data.get('birth_date')
    if birth_date:
        is_valid, msg = validate_birth_date(birth_date)
        if not is_valid:
            errors['birth_date'] = msg

    # اعتبارسنجی پاسپورت
    passport = guest_data.get('passport_number', '')
    if passport:
        is_valid, msg = validate_passport_number(passport)
        if not is_valid:
            errors['passport_number'] = msg

    return len(errors) == 0, errors
