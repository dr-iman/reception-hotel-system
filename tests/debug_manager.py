# debug_managers.py
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("🔍 تست housekeeping_manager...")
    from app.core.housekeeping_manager import HousekeepingManager
    print("✅ housekeeping_manager OK")
except Exception as e:
    print(f"❌ خطا در housekeeping_manager: {e}")
    import traceback
    traceback.print_exc()

try:
    print("🔍 تست maintenance_manager...")  
    from app.core.maintenance_manager import MaintenanceManager
    print("✅ maintenance_manager OK")
except Exception as e:
    print(f"❌ خطا در maintenance_manager: {e}")
    import traceback
    traceback.print_exc()
