# finnhub_raw_data_explorer.py
# Script to explore raw revenue data from Finnhub API

import requests
import json
from datetime import datetime, timedelta
import time

# Your Finnhub API key from config.py
FINNHUB_API_KEY = 'd16hmcpr01qvtdbil250d16hmcpr01qvtdbil25g'

class FinnhubDataExplorer:
    """Explore raw financial data from Finnhub API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1"
        
        # Rate limiting
        self.last_request_time = 0
        self.rate_limit_delay = 1.1  # Finnhub allows 60 calls/minute, so 1+ second delay
        
    def _rate_limit(self):
        """Simple rate limiting to respect API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_company_basic_financials(self, ticker):
        """Get basic financial metrics"""
        self._rate_limit()
        
        url = f"{self.base_url}/stock/metric"
        params = {
            'symbol': ticker,
            'metric': 'all',
            'token': self.api_key
        }
        
        print(f"\n🔍 Fetching basic financials for {ticker}")
        print(f"📡 URL: {url}")
        print(f"📋 Params: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Data keys: {list(data.keys())}")
                return data
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def get_quarterly_financials(self, ticker):
        """Get quarterly financial statements"""
        self._rate_limit()
        
        url = f"{self.base_url}/stock/financials"
        params = {
            'symbol': ticker,
            'statement': 'ic',  # Income statement
            'freq': 'quarterly',
            'token': self.api_key
        }
        
        print(f"\n🔍 Fetching quarterly income statement for {ticker}")
        print(f"📡 URL: {url}")
        print(f"📋 Params: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Data keys: {list(data.keys())}")
                return data
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None
    
    def get_financials_reported(self, ticker):
        """Get financials as reported (most detailed)"""
        self._rate_limit()
        
        url = f"{self.base_url}/stock/financials-reported"
        params = {
            'symbol': ticker,
            'token': self.api_key
        }
        
        print(f"\n🔍 Fetching reported financials for {ticker}")
        print(f"📡 URL: {url}")
        print(f"📋 Params: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"📊 Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Data keys: {list(data.keys())}")
                return data
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None

    def print_json_structure(self, data, title, max_depth=3, current_depth=0):
        """Pretty print JSON structure with limited depth"""
        print(f"\n{'='*50}")
        print(f"📊 {title}")
        print(f"{'='*50}")
        
        if data is None:
            print("❌ No data available")
            return
        
        self._print_nested_structure(data, current_depth, max_depth)
    
    def _print_nested_structure(self, obj, current_depth, max_depth, indent=""):
        """Recursively print nested structure"""
        if current_depth >= max_depth:
            print(f"{indent}... (max depth reached)")
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, (dict, list)):
                    print(f"{indent}{key}: {type(value).__name__}")
                    if isinstance(value, list) and len(value) > 0:
                        print(f"{indent}  └─ Length: {len(value)}")
                        if len(value) > 0:
                            print(f"{indent}  └─ First item type: {type(value[0]).__name__}")
                            if isinstance(value[0], dict):
                                print(f"{indent}     Sample keys: {list(value[0].keys())[:5]}")
                    self._print_nested_structure(value, current_depth + 1, max_depth, indent + "  ")
                else:
                    # Show actual values for simple types
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    print(f"{indent}{key}: {value_str}")
        
        elif isinstance(obj, list):
            print(f"{indent}List with {len(obj)} items")
            if len(obj) > 0:
                print(f"{indent}First item:")
                self._print_nested_structure(obj[0], current_depth + 1, max_depth, indent + "  ")
                if len(obj) > 1:
                    print(f"{indent}... and {len(obj)-1} more items")
    
    def find_revenue_fields(self, data, path=""):
        """Find all fields that might contain revenue data"""
        revenue_fields = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Check if this key might be revenue-related
                key_lower = key.lower()
                if any(keyword in key_lower for keyword in ['revenue', 'sales', 'income', 'total']):
                    if isinstance(value, (int, float)) and value != 0:
                        revenue_fields.append((current_path, value))
                
                # Recursively search nested structures
                if isinstance(value, (dict, list)):
                    revenue_fields.extend(self.find_revenue_fields(value, current_path))
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                current_path = f"{path}[{i}]"
                revenue_fields.extend(self.find_revenue_fields(item, current_path))
        
        return revenue_fields

def main():
    """Main function to explore Finnhub data"""
    print("🏢 Finnhub Financial Data Explorer")
    print("=" * 50)
    
    explorer = FinnhubDataExplorer(FINNHUB_API_KEY)
    
    # Get ticker from user input
    while True:
        ticker_input = input("\n📈 Enter ticker symbol (or 'quit' to exit): ").strip().upper()
        
        if ticker_input.lower() == 'quit':
            print("👋 Goodbye!")
            break
        
        if not ticker_input:
            print("❌ Please enter a valid ticker symbol")
            continue
        
        # You can test multiple tickers by entering them separated by commas
        if ',' in ticker_input:
            test_tickers = [t.strip().upper() for t in ticker_input.split(',')]
        else:
            test_tickers = [ticker_input]
        
        for ticker in test_tickers:
            print(f"\n\n🎯 EXPLORING DATA FOR {ticker}")
            print("=" * 60)
            
            # 1. Basic Financials
            basic_data = explorer.get_company_basic_financials(ticker)
            explorer.print_json_structure(basic_data, f"{ticker} - Basic Financials")
            
            if basic_data:
                revenue_fields = explorer.find_revenue_fields(basic_data)
                if revenue_fields:
                    print(f"\n💰 Revenue-related fields found in basic data:")
                    for field_path, value in revenue_fields[:10]:  # Show first 10
                        print(f"   {field_path}: {value:,}")
            
            # 2. Quarterly Financials
            quarterly_data = explorer.get_quarterly_financials(ticker)
            explorer.print_json_structure(quarterly_data, f"{ticker} - Quarterly Financials")
            
            if quarterly_data:
                revenue_fields = explorer.find_revenue_fields(quarterly_data)
                if revenue_fields:
                    print(f"\n💰 Revenue-related fields found in quarterly data:")
                    for field_path, value in revenue_fields[:10]:  # Show first 10
                        print(f"   {field_path}: {value:,}")
            
            # 3. Reported Financials (most detailed)
            reported_data = explorer.get_financials_reported(ticker)
            explorer.print_json_structure(reported_data, f"{ticker} - Reported Financials", max_depth=2)
            
            if reported_data:
                revenue_fields = explorer.find_revenue_fields(reported_data)
                if revenue_fields:
                    print(f"\n💰 Revenue-related fields found in reported data:")
                    for field_path, value in revenue_fields[:15]:  # Show first 15
                        print(f"   {field_path}: {value:,}")
            
            print(f"\n✅ Completed exploration for {ticker}")
            
            # Rate limiting between tickers
            if ticker != test_tickers[-1]:
                print("⏳ Waiting before next ticker...")
                time.sleep(2)
        
        print(f"\n🎉 Exploration Complete for: {', '.join(test_tickers)}")
        print("📋 You can see the exact data structure from Finnhub above")
        print("💡 Look for the revenue fields in the output")
        print("\n" + "="*50)

if __name__ == "__main__":
    main()