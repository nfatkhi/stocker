#!/usr/bin/env python3
# test_edgartools.py - Test EdgarTools installation

print("🧪 Testing EdgarTools Installation")
print("=" * 40)

# Test 1: Basic import
print("1. Testing basic import...")
try:
    import edgar
    print("   ✅ edgar module imported successfully")
    print(f"   📦 Module location: {edgar.__file__}")
    
    # Check what's available in the module
    available_items = [item for item in dir(edgar) if not item.startswith('_')]
    print(f"   📋 Available items: {', '.join(available_items[:10])}...")
    
except ImportError as e:
    print(f"   ❌ Failed to import edgar: {e}")
    print("   💡 Solution: pip install edgartools")
    exit(1)

# Test 2: Check for Company class
print("\n2. Testing Company class...")
try:
    from edgar import Company
    print("   ✅ Company class imported successfully")
    print(f"   📄 Company class: {Company}")
except ImportError as e:
    print(f"   ❌ Failed to import Company: {e}")
    print("   🔍 Available classes in edgar module:")
    
    # List all classes in edgar module
    import inspect
    for name, obj in inspect.getmembers(edgar):
        if inspect.isclass(obj):
            print(f"      - {name}")

# Test 3: Check for set_identity function
print("\n3. Testing set_identity function...")
try:
    from edgar import set_identity
    print("   ✅ set_identity function imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import set_identity: {e}")

# Test 4: Alternative import patterns
print("\n4. Testing alternative import patterns...")

# Try different import styles
import_patterns = [
    "from edgar import *",
    "import edgar.company",
    "from edgar.company import Company",
    "import edgar.core"
]

for pattern in import_patterns:
    try:
        exec(pattern)
        print(f"   ✅ {pattern} - SUCCESS")
    except Exception as e:
        print(f"   ❌ {pattern} - FAILED: {e}")

# Test 5: Check EdgarTools version
print("\n5. Checking EdgarTools version...")
try:
    import edgar
    if hasattr(edgar, '__version__'):
        print(f"   📊 EdgarTools version: {edgar.__version__}")
    else:
        print("   ⚠️ Version information not available")
except:
    print("   ❌ Could not determine version")

# Test 6: Try to create a Company object (minimal test)
print("\n6. Testing Company object creation...")
try:
    # Try the most common import pattern
    from edgar import Company
    
    # Test with a well-known ticker
    print("   🧪 Creating Company object for AAPL...")
    company = Company("AAPL")
    print(f"   ✅ Company object created: {company}")
    
    # Try to get basic info (this might require SEC identity)
    try:
        print(f"   📋 Company name: {company.name}")
    except Exception as e:
        print(f"   ⚠️ Could not get company name (may need SEC identity): {e}")
        
except Exception as e:
    print(f"   ❌ Failed to create Company object: {e}")

# Test 7: Check if SEC identity is required
print("\n7. Testing SEC identity requirement...")
try:
    from edgar import set_identity
    
    # Try setting identity
    test_identity = "test@example.com"
    set_identity(test_identity)
    print(f"   ✅ SEC identity set successfully: {test_identity}")
    
    # Now try Company again
    try:
        from edgar import Company
        company = Company("AAPL")
        print(f"   ✅ Company creation after identity: {company}")
    except Exception as e:
        print(f"   ❌ Company creation still failed: {e}")
        
except Exception as e:
    print(f"   ❌ Failed to set SEC identity: {e}")

print("\n" + "=" * 40)
print("🎯 DIAGNOSIS:")

# Provide diagnosis
try:
    import edgar
    from edgar import Company, set_identity
    print("✅ EdgarTools appears to be properly installed")
    print("💡 The issue may be in the config validation logic")
    print("🔧 Try updating your config.py validation function")
except ImportError:
    print("❌ EdgarTools is not properly installed")
    print("💡 Try: pip install --upgrade edgartools")
except Exception as e:
    print(f"⚠️ EdgarTools is installed but has issues: {e}")
    print("💡 Try: pip uninstall edgartools && pip install edgartools")

print("\n🚀 Next steps:")
print("1. If EdgarTools installed correctly, update config.py validation")
print("2. If not, reinstall EdgarTools")
print("3. Make sure to set a real email address in EDGARTOOLS_CONFIG")