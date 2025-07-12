# debug_balance_sheet_import.py - Test balance sheet import issues

print("🔍 Testing Balance Sheet Import...")
print("=" * 50)

# Test 1: Check if the file exists
import os
balance_sheet_path = "components/charts/balance_sheet/balance_sheet_chart.py"
processor_path = "components/charts/balance_sheet/balance_sheet_data_processor.py"
init_path = "components/charts/balance_sheet/__init__.py"

print(f"📁 File existence check:")
print(f"   balance_sheet_chart.py: {'✅' if os.path.exists(balance_sheet_path) else '❌'}")
print(f"   balance_sheet_data_processor.py: {'✅' if os.path.exists(processor_path) else '❌'}")
print(f"   __init__.py: {'✅' if os.path.exists(init_path) else '❌'}")

# Test 2: Try importing the data processor first
print(f"\n🔍 Testing data processor import:")
try:
    from components.charts.balance_sheet.balance_sheet_data_processor import (
        BalanceSheetDataProcessor, 
        BalanceSheetDataPoint, 
        BalanceSheetMetrics,
        process_balance_sheet_data
    )
    print("   ✅ Data processor imports successful")
except ImportError as e:
    print(f"   ❌ Data processor import failed: {e}")
except Exception as e:
    print(f"   ❌ Data processor error: {e}")

# Test 3: Try importing the chart
print(f"\n🔍 Testing chart import:")
try:
    from components.charts.balance_sheet.balance_sheet_chart import BalanceSheetChart, BalanceSheetTab
    print("   ✅ Chart imports successful")
except ImportError as e:
    print(f"   ❌ Chart import failed: {e}")
    print(f"   📝 Import error details: {type(e).__name__}: {str(e)}")
except Exception as e:
    print(f"   ❌ Chart error: {e}")
    print(f"   📝 Error details: {type(e).__name__}: {str(e)}")

# Test 4: Check dependencies
print(f"\n🔍 Testing dependencies:")
try:
    import tkinter as tk
    print("   ✅ tkinter available")
except ImportError:
    print("   ❌ tkinter missing")

try:
    import math
    print("   ✅ math available")
except ImportError:
    print("   ❌ math missing")

try:
    from components.charts.base_chart import FinancialBarChart
    print("   ✅ base_chart available")
except ImportError as e:
    print(f"   ❌ base_chart missing: {e}")

# Test 5: Check config import
print(f"\n🔍 Testing config import:")
try:
    from config import UI_CONFIG
    print("   ✅ config available")
except ImportError as e:
    print(f"   ❌ config missing: {e}")

# Test 6: Try the __init__.py import
print(f"\n🔍 Testing __init__.py import:")
try:
    from components.charts.balance_sheet import BalanceSheetTab
    print("   ✅ __init__.py import successful")
except ImportError as e:
    print(f"   ❌ __init__.py import failed: {e}")
    print(f"   📝 This is likely the main issue!")
except Exception as e:
    print(f"   ❌ __init__.py error: {e}")

print(f"\n✅ Balance sheet import test completed")
print(f"💡 Run this script to identify the exact import issue")