# app/utils/export_utils.py
"""
ماژول خروجی‌گیری و گزارش‌گیری از داده‌های سیستم
"""

import logging
import csv
import json
import os
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from decimal import Decimal
import tempfile

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.utils.formatters import format_currency, format_date, format_datetime

logger = logging.getLogger(__name__)

def export_to_excel(data: List[Dict[str, Any]],
                   columns: List[Dict[str, str]],
                   filename: str = None,
                   sheet_name: str = "گزارش") -> Optional[str]:
    """
    خروجی گرفتن به فرمت Excel

    Args:
        data: داده‌ها برای export
        columns: تعریف ستون‌ها
        filename: نام فایل خروجی
        sheet_name: نام sheet در Excel

    Returns:
        Optional[str]: مسیر فایل ایجاد شده یا None در صورت خطا
    """

    if not PANDAS_AVAILABLE:
        logger.error("کتابخانه pandas برای خروجی Excel در دسترس نیست")
        return None

    try:
        # ایجاد DataFrame از داده‌ها
        df_data = []
        for row in data:
            formatted_row = {}
            for col in columns:
                key = col['key']
                value = row.get(key)

                # فرمت‌دهی مقدار بر اساس نوع
                if value is not None:
                    if col.get('type') == 'currency':
                        value = format_currency(Decimal(str(value)), include_symbol=False)
                    elif col.get('type') == 'date':
                        if isinstance(value, (datetime, date)):
                            value = format_date(value, 'short')
                    elif col.get('type') == 'datetime':
                        if isinstance(value, datetime):
                            value = format_datetime(value, 'short', 'short')

                formatted_row[col['title']] = value
            df_data.append(formatted_row)

        df = pd.DataFrame(df_data)

        # تعیین نام فایل
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.xlsx"

        # ایجاد پوشه خروجی اگر وجود ندارد
        export_dir = os.path.join('data', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)

        # ذخیره به Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # تنظیم عرض ستون‌ها
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

        logger.info(f"فایل Excel با موفقیت ایجاد شد: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"خطا در ایجاد فایل Excel: {e}")
        return None

def export_to_csv(data: List[Dict[str, Any]],
                 columns: List[Dict[str, str]],
                 filename: str = None) -> Optional[str]:
    """
    خروجی گرفتن به فرمت CSV

    Args:
        data: داده‌ها برای export
        columns: تعریف ستون‌ها
        filename: نام فایل خروجی

    Returns:
        Optional[str]: مسیر فایل ایجاد شده یا None در صورت خطا
    """

    try:
        # تعیین نام فایل
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.csv"

        # ایجاد پوشه خروجی اگر وجود ندارد
        export_dir = os.path.join('data', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)

        # هدرهای CSV
        fieldnames = [col['title'] for col in columns]

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in data:
                formatted_row = {}
                for col in columns:
                    key = col['key']
                    value = row.get(key)

                    # فرمت‌دهی مقدار بر اساس نوع
                    if value is not None:
                        if col.get('type') == 'currency':
                            value = format_currency(Decimal(str(value)), include_symbol=False)
                        elif col.get('type') == 'date':
                            if isinstance(value, (datetime, date)):
                                value = format_date(value, 'short')
                        elif col.get('type') == 'datetime':
                            if isinstance(value, datetime):
                                value = format_datetime(value, 'short', 'short')

                    formatted_row[col['title']] = value

                writer.writerow(formatted_row)

        logger.info(f"فایل CSV با موفقیت ایجاد شد: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"خطا در ایجاد فایل CSV: {e}")
        return None

def export_to_pdf(data: List[Dict[str, Any]],
                 columns: List[Dict[str, str]],
                 title: str = "گزارش",
                 filename: str = None) -> Optional[str]:
    """
    خروجی گرفتن به فرمت PDF

    Args:
        data: داده‌ها برای export
        columns: تعریف ستون‌ها
        title: عنوان گزارش
        filename: نام فایل خروجی

    Returns:
        Optional[str]: مسیر فایل ایجاد شده یا None در صورت خطا
    """

    if not REPORTLAB_AVAILABLE:
        logger.error("کتابخانه reportlab برای خروجی PDF در دسترس نیست")
        return None

    try:
        # تعیین نام فایل
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.pdf"

        # ایجاد پوشه خروجی اگر وجود ندارد
        export_dir = os.path.join('data', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        filepath = os.path.join(export_dir, filename)

        # ایجاد سند PDF
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)

        # استایل‌ها
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # center
        )

        # محتوای سند
        story = []

        # عنوان
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))

        # تاریخ تولید گزارش
        date_str = format_datetime(datetime.now(), 'full', 'short')
        story.append(Paragraph(f"تاریخ تولید: {date_str}", styles["Normal"]))
        story.append(Spacer(1, 20))

        # ایجاد جدول داده‌ها
        if data:
            # هدرهای جدول
            table_data = [[col['title'] for col in columns]]

            # داده‌های جدول
            for row in data:
                table_row = []
                for col in columns:
                    key = col['key']
                    value = row.get(key)

                    # فرمت‌دهی مقدار بر اساس نوع
                    if value is not None:
                        if col.get('type') == 'currency':
                            value = format_currency(Decimal(str(value)))
                        elif col.get('type') == 'date':
                            if isinstance(value, (datetime, date)):
                                value = format_date(value, 'short')
                        elif col.get('type') == 'datetime':
                            if isinstance(value, datetime):
                                value = format_datetime(value, 'short', 'short')
                        else:
                            value = str(value)
                    else:
                        value = ''

                    table_row.append(value)

                table_data.append(table_row)

            # ایجاد جدول
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(table)
        else:
            story.append(Paragraph("هیچ داده‌ای برای نمایش وجود ندارد", styles["Normal"]))

        # ساخت PDF
        doc.build(story)

        logger.info(f"فایل PDF با موفقیت ایجاد شد: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"خطا در ایجاد فایل PDF: {e}")
        return None

def generate_guest_report(guests_data: List[Dict[str, Any]],
                        report_type: str = "current",
                        format: str = "excel") -> Optional[str]:
    """
    تولید گزارش مهمانان

    Args:
        guests_data: داده‌های مهمانان
        report_type: نوع گزارش (current, history, all)
        format: فرمت خروجی (excel, csv, pdf)

    Returns:
        Optional[str]: مسیر فایل ایجاد شده
    """

    try:
        # تعریف ستون‌های گزارش مهمانان
        columns = [
            {'key': 'id', 'title': 'ID', 'type': 'number'},
            {'key': 'full_name', 'title': 'نام کامل', 'type': 'text'},
            {'key': 'national_id', 'title': 'کد ملی', 'type': 'text'},
            {'key': 'phone', 'title': 'تلفن', 'type': 'text'},
            {'key': 'email', 'title': 'ایمیل', 'type': 'text'},
            {'key': 'check_in_date', 'title': 'تاریخ ورود', 'type': 'date'},
            {'key': 'check_out_date', 'title': 'تاریخ خروج', 'type': 'date'},
            {'key': 'room_number', 'title': 'شماره اتاق', 'type': 'text'},
            {'key': 'status', 'title': 'وضعیت', 'type': 'text'}
        ]

        # عنوان گزارش بر اساس نوع
        titles = {
            'current': 'گزارش مهمانان حاضر',
            'history': 'گزارش تاریخچه مهمانان',
            'all': 'گزارش کلی مهمانان'
        }

        title = titles.get(report_type, 'گزارش مهمانان')

        # انتخاب تابع export بر اساس فرمت
        if format == 'excel':
            return export_to_excel(guests_data, columns, title=title)
        elif format == 'csv':
            return export_to_csv(guests_data, columns)
        elif format == 'pdf':
            return export_to_pdf(guests_data, columns, title=title)
        else:
            logger.error(f"فرمت {format} پشتیبانی نمی‌شود")
            return None

    except Exception as e:
        logger.error(f"خطا در تولید گزارش مهمانان: {e}")
        return None

def generate_financial_report(financial_data: List[Dict[str, Any]],
                            report_type: str = "daily",
                            format: str = "excel") -> Optional[str]:
    """
    تولید گزارش مالی

    Args:
        financial_data: داده‌های مالی
        report_type: نوع گزارش (daily, monthly, yearly)
        format: فرمت خروجی (excel, csv, pdf)

    Returns:
        Optional[str]: مسیر فایل ایجاد شده
    """

    try:
        # تعریف ستون‌های گزارش مالی
        columns = [
            {'key': 'date', 'title': 'تاریخ', 'type': 'date'},
            {'key': 'room_revenue', 'title': 'درآمد اتاق‌ها', 'type': 'currency'},
            {'key': 'restaurant_revenue', 'title': 'درآمد رستوران', 'type': 'currency'},
            {'key': 'other_revenue', 'title': 'سایر درآمدها', 'type': 'currency'},
            {'key': 'total_revenue', 'title': 'درآمد کل', 'type': 'currency'},
            {'key': 'occupancy_rate', 'title': 'نرخ اشغال', 'type': 'percentage'},
            {'key': 'average_daily_rate', 'title': 'میانگین نرخ روزانه', 'type': 'currency'},
            {'key': 'revpar', 'title': 'RevPAR', 'type': 'currency'}
        ]

        # عنوان گزارش بر اساس نوع
        titles = {
            'daily': 'گزارش مالی روزانه',
            'monthly': 'گزارش مالی ماهانه',
            'yearly': 'گزارش مالی سالانه'
        }

        title = titles.get(report_type, 'گزارش مالی')

        # انتخاب تابع export بر اساس فرمت
        if format == 'excel':
            return export_to_excel(financial_data, columns, title=title)
        elif format == 'csv':
            return export_to_csv(financial_data, columns)
        elif format == 'pdf':
            return export_to_pdf(financial_data, columns, title=title)
        else:
            logger.error(f"فرمت {format} پشتیبانی نمی‌شود")
            return None

    except Exception as e:
        logger.error(f"خطا در تولید گزارش مالی: {e}")
        return None

def generate_occupancy_report(occupancy_data: List[Dict[str, Any]],
                            format: str = "excel") -> Optional[str]:
    """
    تولید گزارش اشغال

    Args:
        occupancy_data: داده‌های اشغال
        format: فرمت خروجی (excel, csv, pdf)

    Returns:
        Optional[str]: مسیر فایل ایجاد شده
    """

    try:
        columns = [
            {'key': 'date', 'title': 'تاریخ', 'type': 'date'},
            {'key': 'total_rooms', 'title': 'تعداد کل اتاق‌ها', 'type': 'number'},
            {'key': 'occupied_rooms', 'title': 'اتاق‌های اشغال شده', 'type': 'number'},
            {'key': 'vacant_rooms', 'title': 'اتاق‌های خالی', 'type': 'number'},
            {'key': 'occupancy_rate', 'title': 'نرخ اشغال', 'type': 'percentage'},
            {'key': 'arrivals', 'title': 'ورودها', 'type': 'number'},
            {'key': 'departures', 'title': 'خروج‌ها', 'type': 'number'}
        ]

        if format == 'excel':
            return export_to_excel(occupancy_data, columns, title="گزارش اشغال")
        elif format == 'csv':
            return export_to_csv(occupancy_data, columns)
        elif format == 'pdf':
            return export_to_pdf(occupancy_data, columns, title="گزارش اشغال")
        else:
            logger.error(f"فرمت {format} پشتیبانی نمی‌شود")
            return None

    except Exception as e:
        logger.error(f"خطا در تولید گزارش اشغال: {e}")
        return None

def export_audit_logs(audit_data: List[Dict[str, Any]],
                     format: str = "excel") -> Optional[str]:
    """
    خروجی گرفتن از لاگ‌های Audit

    Args:
        audit_data: داده‌های Audit
        format: فرمت خروجی (excel, csv, pdf)

    Returns:
        Optional[str]: مسیر فایل ایجاد شده
    """

    try:
        columns = [
            {'key': 'timestamp', 'title': 'زمان', 'type': 'datetime'},
            {'key': 'user_name', 'title': 'کاربر', 'type': 'text'},
            {'key': 'user_role', 'title': 'نقش', 'type': 'text'},
            {'key': 'action_type', 'title': 'نوع فعالیت', 'type': 'text'},
            {'key': 'entity_type', 'title': 'نوع موجودیت', 'type': 'text'},
            {'key': 'entity_name', 'title': 'موجودیت', 'type': 'text'},
            {'key': 'description', 'title': 'شرح', 'type': 'text'},
            {'key': 'ip_address', 'title': 'آدرس IP', 'type': 'text'},
            {'key': 'severity', 'title': 'سطح شدت', 'type': 'text'}
        ]

        if format == 'excel':
            return export_to_excel(audit_data, columns, title="گزارش فعالیت‌های سیستم")
        elif format == 'csv':
            return export_to_csv(audit_data, columns)
        elif format == 'pdf':
            return export_to_pdf(audit_data, columns, title="گزارش فعالیت‌های سیستم")
        else:
            logger.error(f"فرمت {format} پشتیبانی نمی‌شود")
            return None

    except Exception as e:
        logger.error(f"خطا در خروجی گرفتن از لاگ‌های Audit: {e}")
        return None
