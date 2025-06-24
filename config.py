# config.py - Enhanced with Hybrid Data Provider Configuration (SEC + FMP)
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
API_KEYS = {
    'financial_modeling_prep': os.getenv('FMP_API_KEY', 'tlbdvnfH2xmkfhl9qMLkOHP760puN6lW'),
    'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', 'T2P6CSN7OPVJ599R'),
    'polygon': os.getenv('POLYGON_API_KEY', '4QNMwR3KFGEx8qN8VF9ZisU7JpZ3N2ic'),
    'finnhub': os.getenv('FINNHUB_API_KEY', 'd16hmcpr01qvtdbil250d16hmcpr01qvtdbil25g')
}

# SEC EDGAR Configuration - For Revenue Data
SEC_EDGAR_CONFIG = {
    'contact_email': 'nfatpro@gmail.com',
    'company_name': 'Stocker App',
    'base_url': 'https://data.sec.gov/api/xbrl',
    'company_tickers_url': 'https://www.sec.gov/files/company_tickers.json',
    'rate_limit_delay': 0.1,  # 100ms between requests to be respectful
    'request_timeout': 15,    # 15 seconds timeout
    'max_retries': 3
}

# FinancialModelingPrep Configuration - For FCF Data (NEW)
FINANCIAL_MODELING_PREP_CONFIG = {
    'api_key': API_KEYS['financial_modeling_prep'],
    'base_url': 'https://financialmodelingprep.com/api/v3',
    'rate_limit_delay': 0.1,  # 100ms between requests
    'request_timeout': 15,    # 15 seconds timeout
    'max_retries': 3,
    'endpoints': {
        'cash_flow_statement': '/cash-flow-statement/{ticker}',
        'income_statement': '/income-statement/{ticker}',
        'balance_sheet': '/balance-sheet-statement/{ticker}',
        'financial_ratios': '/ratios/{ticker}'
    }
}

# App Configuration
APP_CONFIG = {
    'window_title': 'Stocker - Stock Analysis (Hybrid: SEC + FMP)',
    'window_width': 1400,
    'window_height': 900,
    'theme': 'dark',
    'refresh_interval': 300,  # seconds
    'cache_expiry': 3600,  # seconds
}

# Data Configuration - Enhanced for Hybrid Approach
DATA_CONFIG = {
    'quarters_to_fetch': 12,
    'price_history_days': 90,
    'news_item_limit': 10,
    'chart_update_interval': 1000,  # milliseconds
    
    # Hybrid data provider settings (NEW)
    'data_providers': {
        'revenue': 'SEC_EDGAR',           # Use SEC for revenue data
        'free_cash_flow': 'FMP',          # Use FinancialModelingPrep for FCF
        'income_statement': 'FMP',        # Future: Use FMP for income data
        'balance_sheet': 'FMP',           # Future: Use FMP for balance sheet
        'financial_ratios': 'FMP'         # Future: Use FMP for ratios
    },
    
    # Data quality preferences
    'prefer_quarterly_data': True,        # Prefer quarterly over annual
    'handle_duplicate_filings': True,     # Smart duplicate handling
    'fallback_to_estimates': True,        # Show estimates if real data unavailable
    'require_minimum_quarters': 4         # Minimum quarters for analysis
}

# UI Configuration
UI_CONFIG = {
    'font_family': 'Arial',
    'font_size': 10,
    'chart_height': 400,
    'metric_card_width': 200,
    'status_bar_height': 30,
}

# Auto CIK Update Configuration - USER-ONLY MODE
AUTO_UPDATE_CONFIG = {
    # Enable/disable auto-updates globally
    'enabled': True,
    
    # Automatically lookup unknown tickers in real-time (ONLY when user enters them)
    'auto_lookup_unknown_tickers': True,
    
    # Run bulk updates on app startup (DISABLED - user-only mode)
    'bulk_update_on_startup': False,
    
    # Enable background thread for periodic updates (DISABLED - user-only mode)  
    'background_updates': False,
    
    # How often to run bulk updates (hours) - NOT USED in user-only mode
    'update_interval_hours': 24,
    
    # Maximum companies to process per update session - NOT USED in user-only mode
    'max_companies_per_session': 50,
    
    # Timeout for individual CIK lookups (seconds)
    'lookup_timeout': 10,
    
    # Enable verbose logging for auto-updates
    'verbose_logging': True
}

# Data storage configuration
DATA_STORAGE_CONFIG = {
    # Directory for cache files
    'cache_directory': 'data',
    
    # CIK cache filename
    'cik_cache_file': 'data/cik_cache.json',
    
    # Update timestamp file
    'update_timestamp_file': 'data/last_cik_update.txt',
    
    # FMP cache files (NEW)
    'fmp_cache_file': 'data/fmp_cache.json',
    'fmp_timestamp_file': 'data/last_fmp_update.txt',
    
    # Backup old cache files
    'backup_cache_files': True,
    
    # Maximum cache file size (MB)
    'max_cache_size_mb': 10
}

# Popular tickers configuration (customize for your needs)
POPULAR_TICKERS_CONFIG = {
    # Add tickers that should be prioritized for auto-discovery
    'additional_popular_tickers': [
        # Add any specific tickers your app commonly uses
        'ADAP',  # Adaptimmune Therapeutics (your example)
        'INMB',  # INmune Bio, Inc.
        # Large cap for testing hybrid approach
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NFLX', 'NVDA',
        # Some mid/small cap for testing
        'RBLX', 'PLTR', 'SNOW', 'NET', 'DDOG', 'ZM', 'OKTA', 'CRWD',
        # Add more as needed...
    ],
    
    # Enable discovery of trending tickers
    'discover_trending': False,  # Future feature
    
    # Maximum popular tickers to maintain
    'max_popular_tickers': 200
}

# Cash Flow Chart Configuration (NEW)
CASH_FLOW_CONFIG = {
    # Data source preferences
    'prefer_real_fcf': True,              # Prefer real FCF over estimates
    'show_data_source': True,             # Show which source provided the data
    'fcf_estimation_method': 'revenue_percentage',  # How to estimate if no real data
    'fcf_estimation_percentage': 0.20,    # 20% of revenue for estimates
    
    # Chart display options
    'show_fcf_quality_indicator': True,   # Show data quality in chart
    'highlight_estimated_quarters': True, # Visually distinguish estimates
    'show_fcf_trend_line': False,         # Future: Add trend analysis
    
    # FCF calculation preferences (for SEC-only mode)
    'operating_cf_concept': 'NetCashProvidedByUsedInOperatingActivities',
    'capex_concept': 'PaymentsToAcquirePropertyPlantAndEquipment',
    'handle_negative_capex': True,        # Convert negative CapEx to positive
}

# Hybrid Provider Status Messages (NEW)
PROVIDER_STATUS_CONFIG = {
    'messages': {
        'sec_revenue_success': '📊 Revenue: SEC EDGAR (Government Filings)',
        'fmp_fcf_success': '💰 FCF: FinancialModelingPrep (Professional Data)',
        'hybrid_success': '🎯 Hybrid Data: SEC Revenue + FMP FCF',
        'sec_only': '🏛️ SEC EDGAR Only (Revenue + Estimated FCF)',
        'fmp_only': '💰 FinancialModelingPrep Only (Professional Financial Data)',
        'no_data': '❌ No Data Available from Either Source',
        'partial_data': '⚠️ Partial Data Available',
    },
    
    'show_provider_in_charts': True,      # Show data source in chart titles
    'show_quality_metrics': True,        # Show data quality indicators
}

# Feature Flags (NEW)
FEATURE_FLAGS = {
    'hybrid_data_provider': True,         # Enable hybrid SEC + FMP approach
    'auto_cik_discovery': True,           # Enable auto CIK lookup
    'professional_fcf_data': True,        # Use FMP for FCF instead of SEC calculation
    'smart_date_matching': True,          # Match data between providers by date
    'fallback_to_estimates': True,        # Show estimates when real data unavailable
    'enhanced_error_messages': True,      # Detailed error messages with suggestions
    'data_source_attribution': True,     # Show which provider supplied each data point
}

# Debug Configuration (NEW)
DEBUG_CONFIG = {
    'log_api_requests': False,            # Log all API requests (for debugging)
    'log_data_combination': True,        # Log how SEC + FMP data is combined
    'log_fcf_calculations': True,        # Log FCF calculation details
    'log_cik_lookups': True,             # Log CIK discovery process
    'save_raw_responses': False,         # Save raw API responses (for debugging)
    'verbose_chart_creation': True,      # Detailed chart creation logs
}

# Validation Configuration (NEW)
VALIDATION_CONFIG = {
    'validate_ticker_format': True,      # Check ticker symbol format
    'min_revenue_threshold': 1000000,    # Minimum revenue for valid company ($1M)
    'max_quarters_gap': 2,               # Max quarters between filings before warning
    'validate_fcf_reasonableness': True, # Check if FCF values seem reasonable
    'fcf_revenue_ratio_warning': 2.0,    # Warn if FCF > 200% of revenue
}