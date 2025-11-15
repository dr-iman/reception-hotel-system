# test_connection.py
import psycopg2
from config.database_config import database_config

try:
    conn = psycopg2.connect(
        host=database_config.host,
        port=database_config.port,
        database=database_config.name,
        user=database_config.username,
        password=database_config.password
    )
    print("✅ اتصال به دیتابیس موفقیت‌آمیز بود!")
    
    # ایجاد یک cursor برای تست
    cur = conn.cursor()
    cur.execute("SELECT version();")
    db_version = cur.fetchone()
    print(f"✅ نسخه PostgreSQL: {db_version[0]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ خطا در اتصال به دیتابیس: {e}")
