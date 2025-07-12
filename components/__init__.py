# components/__init__.py - Updated for cache system
"""
Components package for the Stocker application - Cache System Edition.
Contains all reusable UI components and the new cache-powered data system.
"""

# Core cache system components (NEW)
try:
    from .cache_manager import CacheManager, start_background_cache_check
    print("✅ Cache Manager imported successfully")
except ImportError as e:
    print(f"⚠️ Cache Manager import failed: {e}")
    CacheManager = None
    start_background_cache_check = None

# Data processing components (NEW)
try:
    from .data_processor import DataProcessor, start_background_dataset_processing, process_ticker_on_cache_update
    print("✅ Data Processor imported successfully")
except ImportError as e:
    print(f"⚠️ Data Processor import failed: {e}")
    DataProcessor = None
    start_background_dataset_processing = None
    process_ticker_on_cache_update = None

# Data fetching components (UPDATED)
try:
    from .data_fetcher import XBRLDataFetcher, fetch_company_data, test_fetcher
    # Create backward compatibility alias
    DataFetcher = XBRLDataFetcher
    print("✅ XBRL Data Fetcher imported successfully")
except ImportError as e:
    print(f"⚠️ Data Fetcher import failed: {e}")
    XBRLDataFetcher = None
    DataFetcher = None
    fetch_company_data = None
    test_fetcher = None

# Chart management components
try:
    from .chart_manager import EnhancedChartManager, ChartManager
    print("✅ Chart Manager imported successfully")
except ImportError as e:
    print(f"⚠️ Chart Manager import failed: {e}")
    EnhancedChartManager = None
    ChartManager = None

# Legacy financials manager (if still needed)
try:
    from .financials_manager import FinancialsManager
    print("✅ Financials Manager imported successfully")
except ImportError as e:
    print(f"⚠️ Financials Manager not available (expected in cache system): {e}")
    FinancialsManager = None

# Optional components
try:
    from .live_price_widget import LivePriceWidget
    print("✅ Live Price Widget imported successfully")
except ImportError:
    # LivePriceWidget is optional
    LivePriceWidget = None

# Define what gets imported when using "from components import *"
__all__ = [
    # Cache system (NEW)
    'CacheManager',
    'start_background_cache_check',
    
    # Data processing (NEW)
    'DataProcessor',
    'start_background_dataset_processing',
    'process_ticker_on_cache_update',
    
    # Data fetching (UPDATED)
    'XBRLDataFetcher',
    'DataFetcher',  # Backward compatibility alias
    'fetch_company_data',
    'test_fetcher',
    
    # Chart management
    'EnhancedChartManager',
    'ChartManager',
    
    # Legacy/Optional components
    'FinancialsManager',
    'LivePriceWidget'
]

# Version info
__version__ = '2.0.0 - Cache System Edition'

# Component registry for dynamic loading (UPDATED)
COMPONENT_REGISTRY = {
    'cache_manager': CacheManager,
    'data_processor': DataProcessor,
    'xbrl_data_fetcher': XBRLDataFetcher,
    'data_fetcher': DataFetcher,  # Backward compatibility
    'chart_manager': EnhancedChartManager,
    'financials_manager': FinancialsManager,
}

def get_component(name):
    """Get a component class by name"""
    return COMPONENT_REGISTRY.get(name)

def list_components():
    """List all available components"""
    return list(COMPONENT_REGISTRY.keys())

def get_cache_components():
    """Get cache-related components"""
    return {
        'cache_manager': CacheManager,
        'data_fetcher': XBRLDataFetcher,
        'background_check': start_background_cache_check
    }

def validate_cache_system():
    """Validate that cache system components are available"""
    required_components = [CacheManager, XBRLDataFetcher, start_background_cache_check]
    missing = [comp for comp in required_components if comp is None]
    
    if missing:
        print(f"❌ Missing cache system components: {len(missing)}")
        return False
    else:
        print("✅ All cache system components available")
        return True

# Auto-validate on import
if __name__ != "__main__":
    validate_cache_system()