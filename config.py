# config.py - Enhanced with SEC EDGAR configuration
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

# SEC EDGAR Configuration (NEW)
SEC_EDGAR_CONFIG = {
    'contact_email': 'nfatpro@gmail.com',
    'company_name': 'Stocker App',
    'base_url': 'https://data.sec.gov/api/xbrl',
    'company_tickers_url': 'https://www.sec.gov/files/company_tickers.json',
    'rate_limit_delay': 0.1,  # 100ms between requests to be respectful
    'request_timeout': 15,    # 15 seconds timeout
    'max_retries': 3
}

# App Configuration
APP_CONFIG = {
    'window_title': 'Stocker - Stock Analysis (SEC EDGAR Enhanced)',
    'window_width': 1400,
    'window_height': 900,
    'theme': 'dark',
    'refresh_interval': 300,  # seconds
    'cache_expiry': 3600,  # seconds
}

# Data Configuration (NEW)
DATA_CONFIG = {
    'quarters_to_fetch': 12,
    'price_history_days': 90,
    'news_item_limit': 10,
    'chart_update_interval': 1000,  # milliseconds
}

# UI Configuration
UI_CONFIG = {
    'font_family': 'Arial',
    'font_size': 10,
    'chart_height': 400,
    'metric_card_width': 200,
    'status_bar_height': 30,
}