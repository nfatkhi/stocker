# config.py - Updated for Raw XBRL Cache System Integration

import os
from dotenv import load_dotenv

# Load environment variables (optional for EdgarTools)
load_dotenv()

# ====================
# EDGARTOOLS CONFIGURATION (PRIMARY)
# ====================
EDGARTOOLS_CONFIG = {
    'user_identity': 'nfatpro@gmail.com',  # Required by SEC regulations - MUST BE REAL EMAIL
    'company_name': 'Stocker App',
    'rate_limit_delay': 0.2,  # Delay between requests (200ms = 5 req/sec for safety)
    'request_timeout': 15,
    'max_retries': 3,
    
    # EdgarTools specific settings
    'enable_caching': True,     # EdgarTools has built-in caching
    'cache_duration_days': 1,   # How long to cache Edgar data
    'max_filings_per_request': 100,  # Limit filings per request
    'prefer_quarterly_filings': True,  # Prefer 10-Q over 10-K when possible
    'include_amendments': False,  # Skip amended filings for cleaner data
    
    # Financial statement preferences
    'extract_xbrl_data': True,  # Use XBRL data when available
    'fallback_to_html': True,   # Fall back to HTML parsing if XBRL fails
    'validate_financial_data': True,  # Basic validation of extracted data
}

# ====================
# APPLICATION CONFIGURATION
# ====================
APP_CONFIG = {
    'name': 'Stocker App',
    'version': '2.0.0 - Raw XBRL Cache Edition',
    'description': 'Stock Market Analysis with Raw XBRL Caching (EdgarTools)',
    'data_sources': ['EdgarTools (SEC EDGAR) with Raw XBRL Cache'],
    'author': 'Stocker Team',
    'license': 'MIT',
    
    # Window settings
    'window_title': 'Stocker - Raw XBRL Cache Edition',
    'window_width': 1400,
    'window_height': 900,
    'theme': 'dark',
    'refresh_interval': 300,  # seconds
    'cache_expiry': 3600,     # seconds (legacy - now handled by cache system)
}

# ====================
# RAW XBRL CACHE CONFIGURATION (NEW)
# ====================
CACHE_CONFIG = {
    # Core cache settings
    'cache_directory': 'data/cache',
    'enable_cache_system': True,
    'max_quarters_per_ticker': 12,  # Keep 12 quarters (3 years) per ticker
    'cache_file_format': 'json',    # JSON format for XBRL data
    'enable_compression': False,    # Set to True if files get too large
    
    # Background update settings
    'enable_background_updates': True,
    'background_update_on_startup': True,
    'background_update_delay': 30,  # 30 seconds after startup
    'background_rate_limit': 0.2,   # 200ms between requests (5/sec)
    'max_background_updates_per_session': 50,  # Limit background updates
    
    # Cache maintenance
    'enable_automatic_cleanup': True,
    'cleanup_old_files_days': 90,   # Remove files older than 90 days
    'cleanup_on_startup': False,    # Don't cleanup on startup (too slow)
    'max_cache_size_gb': 5.0,       # Alert if cache exceeds 5GB
    
    # Performance settings
    'cache_validation_timeout': 5,  # Seconds to validate cache
    'concurrent_cache_operations': 2,  # Max concurrent cache operations
    'cache_write_buffer_size': 1024,   # KB buffer for cache writes
}

# ====================
# DATA CONFIGURATION - UPDATED FOR CACHE SYSTEM
# ====================
DATA_CONFIG = {
    # Core fetching limits (optimized for cache system)
    'quarters_to_fetch': 12,  # Maximum quarters to fetch and cache
    'max_filings_to_process': 15,  # Small buffer for failed extractions
    'filing_types': ['10-Q', '10-K'],  # Quarterly + Annual filings
    'years_to_fetch': 3,      # Number of years for analysis
    'cache_duration_hours': 24,  # Legacy setting - now handled by cache system
    'enable_caching': True,   # Enable our cache system
    
    # Raw XBRL extraction settings (NEW)
    'extract_complete_facts': True,     # Extract all facts from XBRL
    'extract_dimensions': True,         # Extract XBRL dimensions
    'extract_statements_info': True,    # Extract financial statements metadata
    'preserve_raw_xbrl_structure': True,  # Keep original XBRL structure
    'enable_xbrl_debugging': True,      # Enhanced debugging for XBRL extraction
    
    # Financial concept extraction
    'extract_revenue_concepts': True,
    'extract_cashflow_concepts': True, 
    'extract_balance_sheet_concepts': True,
    'extract_income_statement_concepts': True,
    'enhanced_reit_support': True,   # Enhanced support for REIT-specific concepts
    
    # Data quality and validation
    'validate_data_consistency': True,     # Check for data inconsistencies
    'min_revenue_threshold': 1000000,      # Minimum revenue for valid company ($1M)
    'min_meaningful_revenue': 1000000,      # $1M minimum to consider revenue meaningful
    'max_quarters_gap': 2,                 # Max quarters between filings before warning
    'fcf_revenue_ratio_warning': 2.0,      # Warn if FCF > 200% of revenue
    
    # Performance optimizations
    'early_termination_on_success': True,  # Stop early if we get enough data
    'limit_concept_attempts': 15,   # Max concepts to try per data type
    'stop_on_target_reached': True,  # Stop processing once we get target quarters
    'enable_parallel_processing': False,  # Keep simple for now
}

# ====================
# UI CONFIGURATION - UPDATED FOR CACHE SYSTEM
# ====================
UI_CONFIG = {
    'font_family': 'Arial',
    'font_size': 10,
    'chart_height': 400,
    'metric_card_width': 200,
    'status_bar_height': 30,
    'window_width': 1400,
    'window_height': 900,
    'theme': 'dark',
    
    # Cache system UI elements (NEW)
    'show_cache_status': True,          # Show cache hit/miss status
    'show_cache_statistics': True,      # Show cache performance stats
    'show_background_updates': True,    # Show background update progress
    'enable_cache_controls': True,      # Enable cache management controls
    'cache_status_refresh_interval': 5,  # Seconds between cache status updates
    
    # EdgarTools specific UI elements
    'show_data_source_attribution': True,  # Show "EdgarTools + Cache" in charts
    'show_filing_dates': True,             # Show when filings were made
    'show_data_quality_indicators': True,  # Show data quality metrics
    'enable_filing_links': True,           # Enable links to actual SEC filings
    'show_quarter_year_labels': True,      # Show Q1 2024, Q2 2024 format
}

# ====================
# CHART CONFIGURATION - UPDATED
# ====================
CHART_CONFIG = {
    'show_tooltips': True,
    'enable_hover': True,
    'max_quarters_display': 12,
    'color_scheme': {
        'positive': '#4CAF50',
        'negative': '#F44336', 
        'neutral': '#9E9E9E',
        'accent': '#2196F3',
        'background': '#2b2b2b',
        'frame': '#3c3c3c',
        'text': '#ffffff',
        'cache_hit': '#4CAF50',      # Green for cache hits
        'cache_miss': '#FF9800',     # Orange for cache misses
        'background_update': '#2196F3'  # Blue for background updates
    },
    
    # Cache-powered chart features (NEW)
    'show_cache_source': True,       # Show "Loaded from Cache" indicator
    'show_filing_source': True,      # Show which SEC filing provided the data
    'enable_sec_filing_links': True, # Make SEC filing references clickable
    'show_quarter_labels': True,     # Show quarter labels (Q1 2024, etc.)
    'enable_yoy_comparison': True,   # Enable year-over-year comparisons
    'cache_loading_animation': True, # Show loading animation for cache operations
}

# ====================
# FINANCIAL EXTRACTION CONFIG - UPDATED FOR RAW XBRL
# ====================
FINANCIAL_EXTRACTION_CONFIG = {
    # Revenue extraction (optimized for raw XBRL)
    'revenue_concepts': [
        # Standard revenue concepts
        'Revenues', 'Revenue', 'SalesRevenueNet', 'SalesRevenueGoodsNet',
        'RevenueFromContractWithCustomerExcludingAssessedTax', 
        'RevenueFromContractWithCustomerIncludingAssessedTax',
        'TotalRevenues', 'GrossProfit',
        # REIT-specific revenue concepts
        'PropertyIncome', 'RentalIncome', 'RentalRevenue',
        'RealEstateInvestmentPropertyRentalIncome',
        'OperatingIncomeLoss',  # Sometimes used as revenue proxy for REITs
        'Net sales', 'Total revenue'
    ],
    
    # Cash flow extraction (optimized for raw XBRL)
    'operating_cash_flow_concepts': [
        'NetCashProvidedByUsedInOperatingActivities',
        'NetCashProvidedByOperatingActivities',
        'NetCashUsedInOperatingActivities',  # Could be negative
        'CashFlowFromOperatingActivities',
        'Net cash provided by operating activities',
        'Operating cash flow',
        'Cash from operations'
    ],
    
    'capital_expenditure_concepts': [
        'PaymentsToAcquirePropertyPlantAndEquipment', 
        'PaymentsToAcquireRealEstate',  # REIT-specific
        'PaymentsToAcquireRealEstateInvestments',
        'PropertyAndEquipmentAdditions',
        'Capital expenditures', 'Capex',
        'Property and equipment expenditures'
    ],
    
    # Balance sheet concepts
    'total_assets_concepts': [
        'Assets', 'AssetsCurrent', 'TotalAssets', 'Total assets'
    ],
    
    'total_liabilities_concepts': [
        'Liabilities', 'LiabilitiesCurrent', 'TotalLiabilities', 'Total liabilities'
    ],
    
    # Net income concepts
    'net_income_concepts': [
        'NetIncomeLoss', 'NetIncome', 'ProfitLoss', 'Net income'
    ],
    
    # Raw XBRL processing preferences (NEW)
    'preserve_original_concept_names': True,  # Keep original XBRL concept names
    'extract_all_numeric_facts': True,       # Extract all numeric facts for analysis
    'include_concept_metadata': True,        # Include concept metadata in cache
    'handle_multiple_periods': True,         # Handle multiple time periods in facts
    'validate_extracted_values': True,       # Validate extracted financial values
    
    # Data processing preferences
    'handle_negative_capex': True,    # Convert negative CapEx to positive for FCF calc
    'validate_fcf_calculation': True, # Validate that Operating CF - CapEx = FCF makes sense
    'prefer_most_recent_filing': True, # Use most recent filing if duplicates exist
    'success_criteria_revenue_or_cf': True,  # Success if we get either revenue OR cash flow
    'min_meaningful_value': 1000000,  # $1M minimum for meaningful financial data
}

# ====================
# FEATURE FLAGS - UPDATED FOR CACHE SYSTEM
# ====================
FEATURE_FLAGS = {
    # Core features
    'enable_charts': True,
    'enable_revenue_analysis': True,
    'enable_fcf_analysis': True,
    'enable_yoy_analysis': True,      # Year-over-year analysis
    'enable_export': True,
    
    # Cache system features (NEW)
    'enable_raw_xbrl_cache': True,        # Enable our raw XBRL cache system
    'enable_background_updates': True,    # Enable background cache updates
    'enable_cache_monitoring': True,      # Enable cache performance monitoring
    'enable_cache_debugging': True,       # Enable cache debugging features
    'enable_cache_statistics_ui': True,   # Show cache stats in UI
    
    # Legacy features (maintained for compatibility)
    'enable_caching': True,              # Legacy flag - now always True
    'debug_mode': True,                  # General debugging
    
    # Disabled features (no longer relevant)
    'enable_live_price': False,          # EdgarTools doesn't provide live prices
    'enable_news': False,                # Focus on financial data only  
    'enable_technical_analysis': False,  # Focus on fundamental analysis
    'enable_multiple_data_sources': False, # Single source now
    'enable_api_key_management': False,  # EdgarTools doesn't need API keys
    'enable_cik_auto_discovery': False,  # EdgarTools handles this internally
}

# ====================
# LOGGING CONFIGURATION - ENHANCED FOR CACHE
# ====================
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_logging': True,
    'console_logging': True,
    'log_file': 'stocker_cache_system.log',
    'max_file_size_mb': 10,
    'backup_count': 5,
    
    # Cache system specific logging (NEW)
    'log_cache_operations': True,         # Log cache hits/misses/updates
    'log_background_updates': True,       # Log background update progress
    'log_xbrl_extraction': True,          # Log XBRL data extraction
    'log_cache_performance': True,        # Log cache performance metrics
    
    # EdgarTools specific logging
    'log_edgar_requests': True,           # Log EdgarTools API requests
    'log_financial_extraction': True,     # Log financial data extraction process
    'log_data_validation': True,          # Log data validation steps
}

# ====================
# ERROR HANDLING CONFIGURATION - ENHANCED
# ====================
ERROR_HANDLING_CONFIG = {
    'show_user_friendly_errors': True,
    'show_technical_details_in_debug': True,
    'suggest_alternative_tickers': True,
    'retry_failed_requests': True,
    'max_retry_attempts': 3,
    'retry_delay_seconds': 1,
    
    # Cache system error handling (NEW)
    'handle_cache_corruption': True,      # Handle corrupted cache files
    'handle_cache_write_failures': True,  # Handle cache write errors
    'fallback_to_live_data': True,       # Fall back to live EdgarTools if cache fails
    'cache_error_recovery': True,         # Attempt to recover from cache errors
    
    # EdgarTools specific error handling
    'handle_sec_filing_not_found': True,
    'handle_ticker_not_found': True,
    'handle_financial_data_missing': True,
    'provide_edgar_filing_suggestions': True,
}

# ====================
# BACKWARDS COMPATIBILITY - SIMPLIFIED
# ====================
# Keep minimal compatibility for any legacy code
SEC_EDGAR_CONFIG = {
    'contact_email': EDGARTOOLS_CONFIG['user_identity'],
    'company_name': EDGARTOOLS_CONFIG['company_name'],
    'rate_limit_delay': EDGARTOOLS_CONFIG['rate_limit_delay']
}

# Legacy API_KEYS dict (empty - no longer needed)
API_KEYS = {
    # All API keys removed - EdgarTools + Cache system doesn't need them
    # This will cause errors if old code tries to access API keys (good for migration)
}

# ====================
# VALIDATION FUNCTIONS - ENHANCED
# ====================
def validate_config():
    """Validate configuration for cache system"""
    errors = []
    
    # Check EdgarTools identity (required by SEC)
    if not EDGARTOOLS_CONFIG.get('user_identity'):
        errors.append("❌ EdgarTools user_identity is required by SEC regulations")
    
    # Check email format (SEC requires real email)
    user_identity = EDGARTOOLS_CONFIG.get('user_identity', '')
    if '@' not in user_identity:
        errors.append("❌ EdgarTools user_identity should be a real email address")
    
    # Check data limits are reasonable
    quarters = DATA_CONFIG.get('quarters_to_fetch', 0)
    if quarters < 1 or quarters > 20:
        errors.append("❌ quarters_to_fetch should be between 1 and 20")
    
    # Check cache configuration
    cache_dir = CACHE_CONFIG.get('cache_directory', 'data/cache')
    try:
        os.makedirs(cache_dir, exist_ok=True)
        # Test write permissions
        test_file = os.path.join(cache_dir, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        errors.append(f"❌ Cache directory not writable: {cache_dir} - {e}")
    
    # Check that we have required dependencies
    try:
        import edgar
        import pandas as pd
        
        # Try to set identity first (required for Company class)
        if user_identity and '@' in user_identity:
            try:
                edgar.set_identity(user_identity)
            except Exception as e:
                errors.append(f"❌ Could not set SEC identity: {e}")
                return errors  # Don't continue if identity fails
        
        # Test basic functionality
        try:
            from edgar import Company
            from components.cache_manager import CacheManager
            from components.data_fetcher import XBRLDataFetcher
        except Exception as e:
            errors.append(f"❌ Cache system components test failed: {e}")
            
    except ImportError as e:
        errors.append(f"❌ Missing required dependency: {e}")
        errors.append("💡 Install with: pip install edgartools pandas")
    except Exception as e:
        errors.append(f"❌ Dependency validation error: {e}")
    
    return errors

def get_data_sources():
    """Get list of configured data sources"""
    return ['EdgarTools (SEC EDGAR) with Raw XBRL Cache']

def get_feature_summary():
    """Get summary of enabled features"""
    enabled_features = [feature for feature, enabled in FEATURE_FLAGS.items() if enabled]
    return {
        'enabled_features': enabled_features,
        'data_sources': get_data_sources(),
        'quarters_to_fetch': DATA_CONFIG.get('quarters_to_fetch'),
        'cache_enabled': CACHE_CONFIG.get('enable_cache_system'),
        'background_updates': CACHE_CONFIG.get('enable_background_updates'),
        'theme': UI_CONFIG.get('theme'),
        'version': APP_CONFIG.get('version')
    }

def get_cache_status():
    """Get cache system status"""
    return {
        'cache_system_enabled': CACHE_CONFIG.get('enable_cache_system', True),
        'cache_directory': CACHE_CONFIG.get('cache_directory', 'data/cache'),
        'background_updates_enabled': CACHE_CONFIG.get('enable_background_updates', True),
        'max_quarters_per_ticker': CACHE_CONFIG.get('max_quarters_per_ticker', 12),
        'filing_types': DATA_CONFIG.get('filing_types', ['10-Q']),
        'rate_limit_delay': EDGARTOOLS_CONFIG.get('rate_limit_delay', 0.2)
    }

# ====================
# EDGARTOOLS SETUP HELPER - ENHANCED
# ====================
def setup_edgartools():
    """Helper function to set up EdgarTools with cache system"""
    try:
        import edgar
        identity = EDGARTOOLS_CONFIG.get('user_identity')
        if identity and '@' in identity:
            edgar.set_identity(identity)
            print(f"✅ EdgarTools identity set: {identity}")
            
            # Test basic functionality
            try:
                from edgar import Company
                print("✅ EdgarTools Company class accessible")
                
                # Test cache system components
                from components.cache_manager import CacheManager
                from components.data_fetcher import XBRLDataFetcher
                print("✅ Cache system components available")
                
                return True
            except Exception as e:
                print(f"⚠️ EdgarTools setup partial - Component test failed: {e}")
                return False
        else:
            print("❌ No valid user_identity configured for EdgarTools")
            return False
    except ImportError:
        print("❌ EdgarTools not installed. Run: pip install edgartools")
        return False
    except Exception as e:
        print(f"❌ Error setting up EdgarTools: {e}")
        return False

# ====================
# CACHE SYSTEM SETUP HELPER (NEW)
# ====================
def setup_cache_system():
    """Helper function to set up the cache system"""
    try:
        from components.cache_manager import CacheManager
        from components.data_fetcher import XBRLDataFetcher
        
        # Test cache directory
        cache_dir = CACHE_CONFIG.get('cache_directory', 'data/cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Test cache manager creation
        cache_manager = CacheManager(cache_dir)
        print(f"✅ Cache system initialized: {cache_dir}")
        
        # Test data fetcher
        data_fetcher = XBRLDataFetcher()
        print("✅ XBRL Data Fetcher initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Cache system setup failed: {e}")
        return False

# ====================
# INITIALIZATION CHECK - ENHANCED
# ====================
def initialize_application():
    """Complete application initialization check"""
    print("📊 Stocker App - Raw XBRL Cache System Initialization")
    print("=" * 60)
    
    # Validate configuration first
    validation_errors = validate_config()
    if validation_errors:
        print("❌ Configuration Errors:")
        for error in validation_errors:
            print(f"   {error}")
        print("\n🛠️  Please fix the errors above before continuing.")
        return False
    else:
        print("✅ Configuration validation passed")
    
    # Setup EdgarTools
    print("\n🔧 Setting up EdgarTools...")
    if not setup_edgartools():
        print("❌ EdgarTools setup failed")
        return False
    
    # Setup cache system
    print("\n📁 Setting up cache system...")
    if not setup_cache_system():
        print("❌ Cache system setup failed")
        return False
    
    # Show configuration summary
    print(f"\n📋 Configuration Summary:")
    print(f"   Version: {APP_CONFIG['version']}")
    print(f"   Data Sources: {', '.join(get_data_sources())}")
    print(f"   EdgarTools Identity: {EDGARTOOLS_CONFIG['user_identity']}")
    print(f"   Quarters to Fetch: {DATA_CONFIG['quarters_to_fetch']}")
    print(f"   Cache Directory: {CACHE_CONFIG['cache_directory']}")
    print(f"   Background Updates: {CACHE_CONFIG['enable_background_updates']}")
    print(f"   Theme: {UI_CONFIG['theme']}")
    
    # Show feature summary
    feature_summary = get_feature_summary()
    enabled_count = len(feature_summary['enabled_features'])
    print(f"\n🎯 Features Enabled: {enabled_count}")
    
    # Show cache status
    cache_status = get_cache_status()
    print(f"\n📁 Cache System Status:")
    for key, value in cache_status.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Application initialization completed successfully!")
    return True

# Print configuration summary on import (simplified)
if __name__ == "__main__":
    # Full initialization when run directly
    if initialize_application():
        print("\n🚀 Ready to run Stocker App!")
    else:
        print("\n❌ Initialization failed")
else:
    # Quick validation on import
    validation_errors = validate_config()
    if validation_errors:
        print(f"⚠️ Config validation: {len(validation_errors)} issues found. Run config.py to see details.")
    else:
        print("✅ Raw XBRL Cache configuration loaded successfully")
        # Auto-setup EdgarTools on import
        setup_edgartools()