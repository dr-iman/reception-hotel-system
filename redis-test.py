import redis
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_redis_connection():
    try:
        # تست اتصال به localhost
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=5)
        r.ping()
        print("✅ اتصال به Redis روی localhost موفق بود")
        return True
    except Exception as e:
        print(f"❌ خطا در اتصال به localhost: {e}")
    
    try:
        # تست اتصال به 127.0.0.1
        r = redis.Redis(host='127.0.0.1', port=6379, db=0, socket_connect_timeout=5)
        r.ping()
        print("✅ اتصال به Redis روی 127.0.0.1 موفق بود")
        return True
    except Exception as e:
        print(f"❌ خطا در اتصال به 127.0.0.1: {e}")
    
    try:
        # تست اتصال به IP
        r = redis.Redis(host='192.168.1.12', port=6379, db=0, socket_connect_timeout=5)
        r.ping()
        print("✅ اتصال به Redis روی 192.168.1.12 موفق بود")
        return True
    except Exception as e:
        print(f"❌ خطا در اتصال به 192.168.1.12: {e}")
    
    return False

if __name__ == '__main__':
    test_redis_connection()
