# main.py - Updated for new cache system integration

import tkinter as tk
import sys
import os
from typing import Optional, List
from dataclasses import dataclass

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import StockerApp

# Import config for validation
try:
    from config import APP_CONFIG, EDGARTOOLS_CONFIG, validate_config, setup_edgartools
    CONFIG_AVAILABLE = True
    
    # Print cache system info (no more API keys)
    print(f"🚀 Stocker App - Cache System Edition")
    print(f"📊 Data Source: EdgarTools (SEC EDGAR) with Raw XBRL Caching")
    print(f"📧 SEC Contact: {EDGARTOOLS_CONFIG.get('user_identity')}")
    print(f"📁 Cache Directory: data/cache/")
    
except ImportError:
    APP_CONFIG = {'name': 'Stocker App', 'version': '2.0.0'}
    EDGARTOOLS_CONFIG = {'user_identity': 'nfatpro@gmail.com'}
    CONFIG_AVAILABLE = False
    print("⚠️ Config not available - using defaults")


def main():
    """Main entry point with new cache system validation"""
    print("=" * 60)
    print("🚀 STOCKER APP - RAW XBRL CACHE EDITION")
    print("=" * 60)
    
    # Validate configuration if available
    if CONFIG_AVAILABLE:
        print("🔧 Validating configuration...")
        validation_errors = validate_config()
        if validation_errors:
            print("❌ Configuration Errors:")
            for error in validation_errors:
                print(f"   {error}")
            print("\n🛠️  Please fix configuration errors before continuing.")
            return
        else:
            print("✅ Configuration is valid")
            
        # Setup EdgarTools
        print("🔧 Setting up EdgarTools...")
        if setup_edgartools():
            print("✅ EdgarTools configured successfully")
        else:
            print("❌ EdgarTools setup failed")
            return
    else:
        print("⚠️ Skipping validation - config not available")
    
    # Validate cache system dependencies
    print("🔧 Validating cache system dependencies...")
    try:
        # Test pandas (needed for DataFrame operations)
        import pandas as pd
        print("   ✅ Pandas available")
        
        # Test our cache components
        from components.cache_manager import CacheManager
        from components.data_fetcher import XBRLDataFetcher
        print("   ✅ Cache system components available")
        
        # Test cache directory creation
        cache_dir = "data/cache"
        os.makedirs(cache_dir, exist_ok=True)
        print(f"   ✅ Cache directory ready: {cache_dir}")
        
    except ImportError as e:
        print(f"   ❌ Missing dependency: {e}")
        print("   💡 Install required packages:")
        print("      pip install pandas edgartools")
        return
    except Exception as e:
        print(f"   ❌ Cache system validation failed: {e}")
        return
    
    # Create main window
    print("\n🖼️  Creating main window...")
    root = tk.Tk()
    
    # Configure window with new settings
    app_name = APP_CONFIG.get('name', 'Stocker App')
    window_width = APP_CONFIG.get('window_width', 1400)
    window_height = APP_CONFIG.get('window_height', 900)
    
    root.title(f"{app_name} - Cache Edition")
    root.geometry(f"{window_width}x{window_height}")
    root.configure(bg='#f0f0f0')
    root.minsize(1200, 800)
    
    # Set window icon if available
    try:
        # You can add an icon file here
        # root.iconbitmap('assets/stocker_icon.ico')
        pass
    except:
        pass
    
    # Create and run app
    try:
        print("🏗️  Initializing application with cache system...")
        app = StockerApp(root)
        
        # Show app status
        print("\n📊 Application Status:")
        status = app.get_app_status()
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, dict):
                        print(f"     {subkey}:")
                        for subsubkey, subsubvalue in subvalue.items():
                            print(f"       {subsubkey}: {subsubvalue}")
                    else:
                        status_icon = "✅" if subvalue else "❌"
                        print(f"     {status_icon} {subkey}: {subvalue}")
            else:
                print(f"   {key}: {value}")
        
        print("\n🎉 Application ready!")
        print("💡 New Features:")
        print("   • Raw XBRL data cached locally for instant access")
        print("   • Background updates keep all cached tickers current")
        print("   • Only 10-Q quarterly filings (most relevant data)")
        print("   • Financial charts powered by cached XBRL data")
        print("   • No API keys required - direct SEC access")
        
        print("\n🎯 Usage Tips:")
        print("   • Enter any stock ticker to get started")
        print("   • First-time tickers will be cached automatically")
        print("   • Charts appear in the 'Financials' tab")
        print("   • Background system updates cache every startup")
        
        print("\n🚀 Starting application...")
        app.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        
        # Show error dialog
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "Application Error", 
                f"Failed to start Stocker App:\n\n{str(e)}\n\nCheck console for details."
            )
        except:
            pass
    finally:
        try:
            root.destroy()
        except:
            pass


def validate_environment():
    """Validate the runtime environment for cache system"""
    issues = []
    
    # Check Python version
    import sys
    if sys.version_info < (3, 7):
        issues.append("Python 3.7+ required")
    
    # Check required packages
    required_packages = ['pandas', 'edgar', 'tkinter']
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            issues.append(f"Missing package: {package}")
    
    # Check file system permissions
    try:
        test_dir = "data/test"
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
    except Exception:
        issues.append("Cannot write to data directory")
    
    return issues


def show_startup_banner():
    """Show enhanced startup banner"""
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " STOCKER APP - RAW XBRL CACHE EDITION ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + " 📊 Direct SEC EDGAR access via EdgarTools ".center(58) + "║")
    print("║" + " 📁 Local XBRL caching for fast performance ".center(58) + "║")
    print("║" + " 🔄 Background cache updates ".center(58) + "║")
    print("║" + " 📈 Financial charts from real XBRL data ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")


if __name__ == "__main__":
    # Show startup banner
    show_startup_banner()
    
    # Validate environment first
    print("\n🔍 Validating environment...")
    env_issues = validate_environment()
    if env_issues:
        print("❌ Environment Issues Found:")
        for issue in env_issues:
            print(f"   • {issue}")
        print("\n💡 Please resolve these issues before running the app.")
        input("Press Enter to continue anyway or Ctrl+C to exit...")
    else:
        print("✅ Environment validation passed")
    
    # Run main application
    main()