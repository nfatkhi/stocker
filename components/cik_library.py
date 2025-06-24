# components/cik_library.py - Dynamic CIK library that manages ticker-to-CIK mappings with persistent caching and manual entry support.

import requests
import json
import time
import csv
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import os
import threading
from pathlib import Path

# Try to import config with fallbacks
try:
    from config import SEC_EDGAR_CONFIG
except ImportError:
    SEC_EDGAR_CONFIG = {
        'contact_email': 'nfatpro@gmail.com',
        'company_name': 'Stocker App',
        'rate_limit_delay': 0.1,
        'request_timeout': 15,
        'max_retries': 3
    }

@dataclass
class CompanyInfo:
    """Company information with CIK"""
    ticker: str
    cik: str
    company_name: str
    exchange: str = ""
    last_updated: float = 0.0


class CIKLibrary:
    """
    Dynamic CIK Library Manager
    
    Features:
    - Auto-lookup CIKs from SEC API
    - Local caching to avoid repeated API calls
    - Bulk company data loading
    - Real-time ticker validation
    """
    
    def __init__(self, cache_file: str = "data/cik_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(exist_ok=True)
        
        # SEC API configuration
        self.headers = {
            'User-Agent': f"{SEC_EDGAR_CONFIG['company_name']} {SEC_EDGAR_CONFIG['contact_email']}",
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov',
            'Accept': 'application/json'
        }
        
        self.base_url = 'https://data.sec.gov/api/xbrl'
        self.last_request_time = 0
        self.rate_limit_delay = SEC_EDGAR_CONFIG['rate_limit_delay']
        
        # Company database
        self._cik_database: Dict[str, CompanyInfo] = {}
        self._lock = threading.Lock()
        
        # Load existing cache
        self._load_cache()
        
        # Initialize with known major companies
        self._initialize_known_companies()
        
        print(f"🗂️ CIK Library initialized")
        print(f"📊 Cached companies: {len(self._cik_database)}")
        print(f"💾 Cache file: {self.cache_file}")
    
    def _initialize_known_companies(self):
        """Initialize with known major company CIKs"""
        known_companies = {
            'AAPL': ('0000320193', 'Apple Inc.'),
            'MSFT': ('0000789019', 'Microsoft Corporation'),
            'GOOGL': ('0001652044', 'Alphabet Inc.'),
            'GOOG': ('0001652044', 'Alphabet Inc.'),
            'AMZN': ('0001018724', 'Amazon.com Inc.'),
            'TSLA': ('0001318605', 'Tesla Inc.'),
            'META': ('0001326801', 'Meta Platforms Inc.'),
            'FB': ('0001326801', 'Meta Platforms Inc.'),
            'NVDA': ('0000788811', 'NVIDIA Corporation'),
            'O': ('0000726728', 'Realty Income Corporation'),
            'BRK.A': ('0001067983', 'Berkshire Hathaway Inc.'),
            'BRK.B': ('0001067983', 'Berkshire Hathaway Inc.'),
            'JNJ': ('0000200406', 'Johnson & Johnson'),
            'JPM': ('0000019617', 'JPMorgan Chase & Co.'),
            'V': ('0001403161', 'Visa Inc.'),
            'PG': ('0000080424', 'Procter & Gamble Co.'),
            'UNH': ('0000731766', 'UnitedHealth Group Inc.'),
            'HD': ('0000354950', 'Home Depot Inc.'),
            'MA': ('0001141391', 'Mastercard Inc.'),
            'DIS': ('0001001039', 'Walt Disney Co.'),
            'NFLX': ('0001065280', 'Netflix Inc.'),
            'CRM': ('0001108524', 'Salesforce Inc.'),
            'AMD': ('0000002488', 'Advanced Micro Devices Inc.'),
            'PYPL': ('0001633917', 'PayPal Holdings Inc.'),
            'INTC': ('0000050863', 'Intel Corporation'),
            'CSCO': ('0000858877', 'Cisco Systems Inc.'),
            'PFE': ('0000078003', 'Pfizer Inc.'),
            'KO': ('0000021344', 'Coca-Cola Co.'),
            'PEP': ('0000077476', 'PepsiCo Inc.'),
            'TMO': ('0000097745', 'Thermo Fisher Scientific Inc.'),
            'COST': ('0000909832', 'Costco Wholesale Corporation'),
            'AVGO': ('0001730168', 'Broadcom Inc.'),
            # Add some popular smaller companies
            'ADBE': ('0000796343', 'Adobe Inc.'),
            'CRM': ('0001108524', 'Salesforce Inc.'),
            'ZM': ('0001585521', 'Zoom Video Communications Inc.'),
            'SHOP': ('0001594805', 'Shopify Inc.'),
            'SQ': ('0001512673', 'Block Inc.'),
            'ROKU': ('0001428439', 'Roku Inc.'),
            'TWLO': ('0001447669', 'Twilio Inc.'),
            'UBER': ('0001543151', 'Uber Technologies Inc.'),
            'LYFT': ('0001759509', 'Lyft Inc.'),
            'SNAP': ('0001564408', 'Snap Inc.'),
            'PINS': ('0001506439', 'Pinterest Inc.'),
            'DOCU': ('0001261333', 'DocuSign Inc.'),
            'CRWD': ('0001535527', 'CrowdStrike Holdings Inc.'),
            'ZS': ('0001713683', 'Zscaler Inc.'),
            'NET': ('0001477333', 'Cloudflare Inc.'),
        }
        
        current_time = time.time()
        for ticker, (cik, name) in known_companies.items():
            if ticker not in self._cik_database:
                self._cik_database[ticker] = CompanyInfo(
                    ticker=ticker,
                    cik=cik,
                    company_name=name,
                    last_updated=current_time
                )
    
    def _load_cache(self):
        """Load CIK cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                for ticker, data in cache_data.items():
                    self._cik_database[ticker] = CompanyInfo(**data)
                
                print(f"📂 Loaded {len(cache_data)} companies from cache")
            else:
                print("📂 No existing cache found, starting fresh")
        except Exception as e:
            print(f"⚠️ Error loading cache: {e}")
    
    def _save_cache(self):
        """Save CIK cache to disk"""
        try:
            cache_data = {}
            for ticker, info in self._cik_database.items():
                cache_data[ticker] = {
                    'ticker': info.ticker,
                    'cik': info.cik,
                    'company_name': info.company_name,
                    'exchange': info.exchange,
                    'last_updated': info.last_updated
                }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"💾 Saved {len(cache_data)} companies to cache")
        except Exception as e:
            print(f"⚠️ Error saving cache: {e}")
    
    def _rate_limit(self):
        """Rate limiting for SEC API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_cik(self, ticker: str) -> Optional[str]:
        """Get CIK for a ticker symbol"""
        ticker = ticker.upper().strip()
        
        with self._lock:
            # Check cache first
            if ticker in self._cik_database:
                return self._cik_database[ticker].cik
        
        # Not in cache, try to fetch from SEC
        company_info = self._fetch_company_info(ticker)
        if company_info:
            with self._lock:
                self._cik_database[ticker] = company_info
                self._save_cache()
            return company_info.cik
        
        return None
    
    def get_company_info(self, ticker: str) -> Optional[CompanyInfo]:
        """Get complete company information"""
        ticker = ticker.upper().strip()
        
        with self._lock:
            if ticker in self._cik_database:
                return self._cik_database[ticker]
        
        # Try to fetch if not cached
        company_info = self._fetch_company_info(ticker)
        if company_info:
            with self._lock:
                self._cik_database[ticker] = company_info
                self._save_cache()
            return company_info
        
        return None
    
    def _fetch_company_info(self, ticker: str) -> Optional[CompanyInfo]:
        """Fetch company information from SEC API"""
        print(f"🔍 Looking up CIK for {ticker}...")
        
        try:
            self._rate_limit()
            
            # Try the company tickers endpoint
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{ticker}/us-gaap/Revenues.json"
            
            # First, try a more targeted search approach
            company_info = self._search_company_by_ticker(ticker)
            if company_info:
                print(f"✅ Found {ticker}: CIK {company_info.cik} - {company_info.company_name}")
                return company_info
            
            print(f"❌ Could not find CIK for {ticker}")
            return None
            
        except Exception as e:
            print(f"⚠️ Error fetching company info for {ticker}: {e}")
            return None
    
    def _search_company_by_ticker(self, ticker: str) -> Optional[CompanyInfo]:
        """Search for company using various SEC endpoints"""
        try:
            # Method 1: Try to search in SEC's company facts
            # This is a more comprehensive approach but requires downloading more data
            
            # For now, we'll use a simpler approach and expand the known database
            # In a production system, you'd want to implement a more sophisticated search
            
            # Method 2: Use external API to get CIK (if available)
            # This could integrate with other financial APIs that have ticker->CIK mappings
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error in company search: {e}")
            return None
    
    def is_ticker_supported(self, ticker: str) -> bool:
        """Check if ticker is supported (has CIK available)"""
        return self.get_cik(ticker) is not None
    
    def get_supported_tickers(self) -> List[str]:
        """Get list of all supported ticker symbols"""
        with self._lock:
            return list(self._cik_database.keys())
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the CIK database"""
        with self._lock:
            return {
                'total_companies': len(self._cik_database),
                'cache_file_exists': self.cache_file.exists(),
                'known_exchanges': len(set(info.exchange for info in self._cik_database.values() if info.exchange))
            }
    
    def add_manual_entry(self, ticker: str, cik: str, company_name: str, exchange: str = ""):
        """Manually add a ticker->CIK mapping"""
        ticker = ticker.upper().strip()
        cik = cik.strip()
        
        if not cik.startswith('0'):
            # Ensure CIK is properly padded
            cik = f"{int(cik):010d}"
        
        company_info = CompanyInfo(
            ticker=ticker,
            cik=cik,
            company_name=company_name,
            exchange=exchange,
            last_updated=time.time()
        )
        
        with self._lock:
            self._cik_database[ticker] = company_info
            self._save_cache()
        
        print(f"✅ Manually added {ticker}: CIK {cik} - {company_name}")
    
    def bulk_load_from_csv(self, csv_file_path: str):
        """Load ticker->CIK mappings from CSV file"""
        try:
            with open(csv_file_path, 'r') as f:
                reader = csv.DictReader(f)
                count = 0
                
                for row in reader:
                    ticker = row.get('ticker', '').upper().strip()
                    cik = row.get('cik', '').strip()
                    name = row.get('company_name', '').strip()
                    exchange = row.get('exchange', '').strip()
                    
                    if ticker and cik and name:
                        self.add_manual_entry(ticker, cik, name, exchange)
                        count += 1
                
                print(f"📊 Bulk loaded {count} companies from {csv_file_path}")
                
        except Exception as e:
            print(f"❌ Error bulk loading from CSV: {e}")
    
    def export_to_csv(self, csv_file_path: str):
        """Export current database to CSV"""
        try:
            with open(csv_file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ticker', 'cik', 'company_name', 'exchange', 'last_updated'])
                
                with self._lock:
                    for info in self._cik_database.values():
                        writer.writerow([
                            info.ticker,
                            info.cik,
                            info.company_name,
                            info.exchange,
                            info.last_updated
                        ])
                
                print(f"📁 Exported {len(self._cik_database)} companies to {csv_file_path}")
                
        except Exception as e:
            print(f"❌ Error exporting to CSV: {e}")


# Global CIK library instance
_global_cik_library = None

def get_cik_library() -> CIKLibrary:
    """Get the global CIK library instance"""
    global _global_cik_library
    if _global_cik_library is None:
        _global_cik_library = CIKLibrary()
    return _global_cik_library


if __name__ == "__main__":
    # Test the CIK library
    cik_lib = CIKLibrary()
    
    # Test known ticker
    print(f"AAPL CIK: {cik_lib.get_cik('AAPL')}")
    
    # Test unknown ticker
    print(f"ADAP CIK: {cik_lib.get_cik('ADAP')}")
    
    # Add ADAP manually if you know its CIK
    # cik_lib.add_manual_entry('ADAP', '0001234567', 'Adaptimmune Therapeutics plc')
    
    # Show stats
    print(f"Database stats: {cik_lib.get_database_stats()}")
    
    # Show supported tickers
    print(f"Supported tickers: {cik_lib.get_supported_tickers()[:10]}...")