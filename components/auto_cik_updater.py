# components/auto_cik_updater.py - Automatic CIK discovery system that searches SEC's company_tickers.json and caches results in the CIK library.

import requests
import json
import time
import threading
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from pathlib import Path
import csv

from core.event_system import EventBus, Event, EventType
from components.cik_library import get_cik_library, CompanyInfo

# Try to import config with fallbacks
try:
    from config import SEC_EDGAR_CONFIG, AUTO_UPDATE_CONFIG
except ImportError:
    SEC_EDGAR_CONFIG = {
        'contact_email': 'nfatpro@gmail.com',
        'company_name': 'Stocker App',
        'rate_limit_delay': 0.1,
        'request_timeout': 15,
        'max_retries': 3
    }
    AUTO_UPDATE_CONFIG = {
        'enabled': True,
        'update_interval_hours': 24,
        'bulk_update_on_startup': True,
        'max_companies_per_session': 100,
        'background_updates': True
    }


class AutoCIKUpdater:
    """
    Automatic CIK Lookup and Database Update System
    
    Features:
    - Real-time CIK lookup for unknown tickers
    - Background periodic updates
    - Popular ticker prioritization
    - Smart rate limiting and caching
    """
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus
        self.cik_library = get_cik_library()
        
        # SEC API configuration
        self.headers = {
            'User-Agent': f"{SEC_EDGAR_CONFIG['company_name']} {SEC_EDGAR_CONFIG['contact_email']}",
            'Accept': 'application/json',
            'Host': 'data.sec.gov'
        }
        
        self.base_url = 'https://data.sec.gov'
        self.last_request_time = 0
        self.rate_limit_delay = SEC_EDGAR_CONFIG['rate_limit_delay']
        
        # Update tracking
        self.last_bulk_update = self._get_last_update_timestamp()
        self.update_queue: Set[str] = set()
        self.updating = False
        self.background_thread = None
        
        # Popular tickers that should be prioritized
        self.popular_tickers = {
            # Major Tech
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
            # Major Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'USB', 'PNC', 'TFC', 'COF',
            # Popular Growth
            'PLTR', 'SNOW', 'ABNB', 'UBER', 'LYFT', 'DOCU', 'ZOOM', 'CRM', 'NOW',
            # Biotech/Pharma
            'PFE', 'JNJ', 'MRNA', 'BNTX', 'GILD', 'BIIB', 'AMGN', 'REGN', 'VRTX',
            # Consumer
            'DIS', 'NFLX', 'SHOP', 'SQ', 'PYPL', 'ROKU', 'SPOT', 'TWTR', 'SNAP',
            # Recent IPOs/SPACs
            'RIVN', 'LCID', 'SOFI', 'HOOD', 'COIN', 'RBLX', 'U', 'PATH', 'DDOG'
        }
        
        print(f"🤖 Auto CIK Updater initialized")
        print(f"📊 Current database size: {len(self.cik_library.get_supported_tickers())}")
        print(f"⚡ Auto-updates: {'Enabled for user queries only' if AUTO_UPDATE_CONFIG['enabled'] else 'Disabled'}")
        
        # NO background updates - only on-demand lookups
        print(f"🔇 Background updates disabled - only lookup unknown tickers on user request")
    
    def _rate_limit(self):
        """Rate limiting for SEC API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_last_update_timestamp(self) -> float:
        """Get timestamp of last bulk update"""
        try:
            timestamp_file = Path("data/last_cik_update.txt")
            if timestamp_file.exists():
                with open(timestamp_file, 'r') as f:
                    return float(f.read().strip())
        except:
            pass
        return 0.0
    
    def _save_update_timestamp(self):
        """Save timestamp of bulk update"""
        try:
            timestamp_file = Path("data/last_cik_update.txt")
            timestamp_file.parent.mkdir(exist_ok=True)
            with open(timestamp_file, 'w') as f:
                f.write(str(time.time()))
        except Exception as e:
            print(f"⚠️ Could not save update timestamp: {e}")
    
    def lookup_ticker_realtime(self, ticker: str) -> Optional[Tuple[str, str]]:
        """
        Real-time CIK lookup using SEC JSON with immediate caching
        This is the main entry point for unknown ticker discovery
        """
        print(f"🔍 Real-time lookup for {ticker}")
        
        try:
            # Check if already in database first
            if self.cik_library.is_ticker_supported(ticker):
                cik = self.cik_library.get_cik(ticker)
                company_info = self.cik_library.get_company_info(ticker)
                company_name = company_info.company_name if company_info else f"{ticker} Corporation"
                print(f"✅ {ticker} already in database")
                return cik, company_name
            
            # Search in SEC company_tickers.json
            result = self._search_sec_company_tickers(ticker)
            if result:
                cik, company_name, exchange = result
                
                # Verify has financial data
                print(f"🔍 Verifying financial data for {ticker} (CIK: {cik})")
                if self._verify_has_financial_data(cik):
                    # Add to database and cache immediately
                    self.cik_library.add_manual_entry(ticker, cik, company_name, exchange)
                    print(f"✅ Auto-added and cached {ticker}: {company_name} (CIK: {cik})")
                    
                    # Emit event if event bus available
                    if self.event_bus:
                        self.event_bus.publish(Event(
                            type=EventType.STATUS_UPDATED,
                            data={
                                'message': f'Auto-discovered CIK for {ticker}',
                                'ticker': ticker,
                                'cik': cik,
                                'company_name': company_name,
                                'source': 'SEC_JSON_AUTO_LOOKUP'
                            }
                        ))
                    
                    return cik, company_name
                else:
                    print(f"❌ {ticker} found but no financial data available")
            else:
                print(f"❌ {ticker} not found in SEC database")
            
            return None
            
        except Exception as e:
            print(f"❌ Error in real-time lookup for {ticker}: {e}")
            return None
    
    def _search_sec_company_tickers(self, ticker: str) -> Optional[Tuple[str, str, str]]:
        """Search SEC company tickers endpoint - EXACT MATCHES ONLY"""
        try:
            self._rate_limit()
            
            # Use the exact URL you confirmed works
            url = "https://www.sec.gov/files/company_tickers.json"
            print(f"🔍 Searching SEC company_tickers.json for {ticker}")
            
            # Minimal headers - treat it like a public JSON file
            headers = {
                'User-Agent': f"{SEC_EDGAR_CONFIG['company_name']} {SEC_EDGAR_CONFIG['contact_email']}",
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"📊 Loaded {len(data)} companies from SEC database")
                    
                    # ONLY exact ticker match (case insensitive) - NO FUZZY MATCHING
                    for key, company_info in data.items():
                        company_ticker = company_info.get('ticker', '').upper()
                        if company_ticker == ticker.upper():
                            cik = str(company_info.get('cik_str', '')).zfill(10)
                            title = company_info.get('title', '')
                            
                            print(f"✅ Exact match found: {ticker} -> {title} (CIK: {cik})")
                            return cik, title, "NASDAQ/NYSE"
                    
                    # If no exact match found, return None (NO FUZZY MATCHING)
                    print(f"❌ No exact match found for {ticker} in SEC database")
                    print(f"💡 {ticker} is not in the SEC master ticker list")
                    return None
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Error parsing SEC JSON response: {e}")
                    print(f"🔍 Response content preview: {response.text[:200]}...")
                    return None
                    
            elif response.status_code == 403:
                print(f"❌ SEC API returned 403 Forbidden")
                print(f"💡 Try accessing manually: https://www.sec.gov/files/company_tickers.json")
                print(f"🔧 May need different User-Agent or headers")
                return None
                
            elif response.status_code == 404:
                print(f"❌ SEC API returned 404 - URL may have changed")
                print(f"💡 Confirmed working URL: https://www.sec.gov/files/company_tickers.json")
                return None
                
            else:
                print(f"❌ SEC API error: HTTP {response.status_code}")
                print(f"📄 Response: {response.text[:200]}...")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏱️ SEC API request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print(f"🌐 Connection error to SEC API")
            return None
        except Exception as e:
            print(f"❌ Unexpected error accessing SEC tickers: {e}")
            return None
    
    def _check_known_edge_cases(self, ticker: str) -> Optional[Tuple[str, str, str]]:
        """Check against known edge cases when SEC JSON fails"""
        print(f"🔍 Checking known edge cases for {ticker}")
        
        # Known edge cases that may not be in SEC JSON or when SEC API fails
        edge_cases = {
            'INMB': ('0001711754', 'INmune Bio, Inc.'),
            'ADAP': ('0001621227', 'Adaptimmune Therapeutics plc'),
            # Add more as discovered
        }
        
        ticker_upper = ticker.upper()
        if ticker_upper in edge_cases:
            cik, company_name = edge_cases[ticker_upper]
            print(f"✅ Found {ticker} in edge cases: {company_name} (CIK: {cik})")
            return cik, company_name, "NASDAQ"
        
        print(f"❌ {ticker} not found in edge cases either")
        return None
    
    def lookup_with_manual_fallback(self, ticker: str, cik: str = None, company_name: str = None) -> Optional[Tuple[str, str]]:
        """
        Lookup with manual fallback for edge cases like INMB
        If CIK is provided, skip SEC JSON lookup and verify directly
        """
        print(f"🎯 Lookup with manual fallback for {ticker}")
        
        # If manual CIK provided, use it directly
        if cik and company_name:
            print(f"📝 Using provided CIK for {ticker}: {company_name} (CIK: {cik})")
            
            # Verify has financial data
            if self._verify_has_financial_data(cik):
                # Add to database
                self.cik_library.add_manual_entry(ticker, cik, company_name)
                print(f"✅ Manually added and cached {ticker}: {company_name} (CIK: {cik})")
                return cik, company_name
            else:
                print(f"❌ Manual CIK {cik} for {ticker} has no financial data")
                return None
        
        # Otherwise, try normal lookup
        return self.lookup_ticker_realtime(ticker)
    
    def _verify_has_financial_data(self, cik: str) -> bool:
        """Verify CIK has usable financial data"""
        try:
            self._rate_limit()
            
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/Revenues.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                usd_data = data.get('units', {}).get('USD', [])
                quarterly_data = [r for r in usd_data if r.get('form') == '10-Q']
                return len(quarterly_data) > 0
            
            return False
            
        except:
            return False
    
    def bulk_update_popular_tickers(self) -> Dict[str, bool]:
        """
        Update popular tickers that aren't in database using SEC JSON lookup
        """
        print(f"🚀 Starting auto-lookup of missing popular tickers...")
        
        missing_tickers = []
        for ticker in self.popular_tickers:
            if not self.cik_library.is_ticker_supported(ticker):
                missing_tickers.append(ticker)
        
        if not missing_tickers:
            print(f"✅ All popular tickers already in database")
            return {}
        
        print(f"📋 Found {len(missing_tickers)} missing popular tickers")
        print(f"🔍 Starting SEC JSON lookups...")
        
        results = {}
        max_per_session = AUTO_UPDATE_CONFIG.get('max_companies_per_session', 100)
        
        for i, ticker in enumerate(missing_tickers[:max_per_session], 1):
            print(f"[{i}/{min(len(missing_tickers), max_per_session)}] Processing {ticker}")
            
            # Skip cache check and go directly to SEC lookup
            result = self._search_sec_company_tickers(ticker)
            if result:
                cik, company_name, exchange = result
                
                # Verify has financial data
                if self._verify_has_financial_data(cik):
                    # Add to database and cache immediately
                    self.cik_library.add_manual_entry(ticker, cik, company_name, exchange)
                    print(f"   ✅ Added {ticker}: {company_name}")
                    results[ticker] = True
                else:
                    print(f"   ❌ {ticker} found but no financial data")
                    results[ticker] = False
            else:
                print(f"   ❌ {ticker} not found in SEC database")
                results[ticker] = False
            
            # Rate limiting between requests
            if i < len(missing_tickers):
                time.sleep(0.3)  # Slightly longer delay for bulk operations
        
        success_count = sum(results.values())
        print(f"🎯 Auto-lookup complete: {success_count}/{len(results)} successful")
        print(f"📊 Database now has {len(self.cik_library.get_supported_tickers())} companies")
        
        self._save_update_timestamp()
        return results
    
    def should_auto_update(self) -> bool:
        """Check if auto-update should run - DISABLED for user-only mode"""
        return False  # Never run automatic bulk updates
    
    def _start_background_updates(self):
        """Background updates disabled - only lookup on user request"""
        print(f"🔇 Background updates disabled - auto-lookup only when user enters unknown ticker")
    
    def _background_update_loop(self):
        """Background updates disabled - no automatic processing"""
        print(f"🔇 Background processing disabled - only user-triggered lookups")
        return
    
    def add_ticker_to_queue(self, ticker: str):
        """Add ticker to update queue - DISABLED in user-only mode"""
        print(f"📝 Queue disabled - {ticker} will be looked up immediately when requested")
    
    def process_update_queue(self):
        """Process queued ticker updates"""
        if not self.update_queue or self.updating:
            return
        
        self.updating = True
        processed = []
        
        try:
            print(f"🔄 Processing {len(self.update_queue)} queued tickers...")
            
            for ticker in list(self.update_queue):
                result = self.lookup_ticker_realtime(ticker)
                if result:
                    processed.append(ticker)
                
                self.update_queue.discard(ticker)
                time.sleep(0.2)  # Rate limiting
            
            print(f"✅ Processed queue: {len(processed)} successful")
            
        finally:
            self.updating = False
    
    def get_update_stats(self) -> Dict:
        """Get statistics about auto-updates"""
        return {
            'database_size': len(self.cik_library.get_supported_tickers()),
            'mode': 'User-triggered lookups only',
            'auto_updates_enabled': AUTO_UPDATE_CONFIG.get('enabled', True),
            'background_thread_active': False,
            'bulk_updates': 'Disabled',
            'lookup_on_demand': True
        }
    
    def force_update_now(self):
        """Force immediate bulk update"""
        print(f"⚡ Force updating CIK database...")
        return self.bulk_update_popular_tickers()


# Global auto-updater instance
_global_auto_updater = None

def get_auto_updater(event_bus: EventBus = None) -> AutoCIKUpdater:
    """Get the global auto-updater instance"""
    global _global_auto_updater
    if _global_auto_updater is None:
        _global_auto_updater = AutoCIKUpdater(event_bus)
    return _global_auto_updater


# Helper function to manually add edge case tickers
def add_edge_case_tickers():
    """Add known edge case tickers that might not be in SEC JSON"""
    from components.cik_library import get_cik_library
    
    cik_lib = get_cik_library()
    
    edge_cases = [
        ('INMB', '0001711754', 'INmune Bio, Inc.'),
        ('ADAP', '0001621227', 'Adaptimmune Therapeutics plc'),
        # Add more edge cases as discovered
    ]
    
    for ticker, cik, company_name in edge_cases:
        if not cik_lib.is_ticker_supported(ticker):
            cik_lib.add_manual_entry(ticker, cik, company_name)
            print(f"✅ Added edge case: {ticker} -> {company_name}")
        else:
            print(f"⏭️  Already exists: {ticker}")
    
    return len(edge_cases)


def test_sec_endpoint():
    """Test if the SEC company_tickers.json endpoint is accessible"""
    import requests
    
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {
        'User-Agent': 'Stocker App nfatpro@gmail.com',
    }
    
    print(f"🧪 Testing SEC endpoint: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS: Loaded {len(data)} companies")
                
                # Test search for INMB specifically
                inmb_found = False
                for key, company_info in data.items():
                    if company_info.get('ticker', '').upper() == 'INMB':
                        cik = company_info.get('cik_str', '')
                        title = company_info.get('title', '')
                        print(f"🎯 INMB found: {title} (CIK: {cik})")
                        inmb_found = True
                        break
                
                if not inmb_found:
                    print(f"❌ INMB not found in SEC data")
                    print(f"💡 INMB may not be in the SEC master ticker list")
                
                return True
                
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing JSON: {e}")
                print(f"📄 Response preview: {response.text[:200]}...")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False


def fix_inmb_now():
    """Quick fix to add INMB to the database immediately"""
    print(f"🔧 Quick fix for INMB...")
    
    # First test if we can access SEC data
    if test_sec_endpoint():
        print(f"✅ SEC endpoint is accessible")
        
        # Try auto-lookup
        updater = get_auto_updater()
        result = updater.lookup_ticker_realtime('INMB')
        if result:
            cik, company_name = result
            print(f"✅ INMB auto-discovered: {company_name} (CIK: {cik})")
            return True
    
    # Fall back to manual addition
    print(f"🔄 Falling back to manual addition...")
    from components.cik_library import get_cik_library
    
    cik_lib = get_cik_library()
    
    if not cik_lib.is_ticker_supported('INMB'):
        cik_lib.add_manual_entry('INMB', '0001711754', 'INmune Bio, Inc.')
        print(f"✅ INMB manually added to database")
        print(f"🎯 Try searching for INMB again - it should work now!")
        return True
    else:
        print(f"✅ INMB already exists in database")
        return False


if __name__ == "__main__":
    # Test the SEC JSON auto-lookup and caching
    updater = AutoCIKUpdater()
    
    print("🧪 Testing with known edge case: INMB")
    print("=" * 50)
    
    # First try normal auto-lookup
    result = updater.lookup_ticker_realtime('INMB')
    if result:
        cik, company_name = result
        print(f"✅ SUCCESS: Auto-discovered INMB -> {company_name} (CIK: {cik})")
    else:
        print(f"❌ INMB not found in SEC JSON, trying manual fallback...")
        
        # Use manual fallback with known CIK
        result = updater.lookup_with_manual_fallback(
            'INMB', 
            '0001711754', 
            'INmune Bio, Inc.'
        )
        if result:
            cik, company_name = result
            print(f"✅ SUCCESS: Manually added INMB -> {company_name} (CIK: {cik})")
    
    print("\n" + "=" * 50)
    print("🧪 Testing with popular ticker: AAPL")
    
    result = updater.lookup_ticker_realtime('AAPL')
    if result:
        cik, company_name = result
        print(f"✅ SUCCESS: Found AAPL -> {company_name} (CIK: {cik})")
    
    # Show final database stats
    stats = updater.get_update_stats()
    print(f"\n📊 Final database stats:")
    print(f"   Total companies: {stats['database_size']}")
    print(f"   Auto-updates enabled: {stats['auto_updates_enabled']}")
    
    print(f"\n💡 Key takeaway:")
    print(f"   - SEC JSON lookup works for most tickers")
    print(f"   - Manual fallback handles edge cases like INMB")
    print(f"   - Both methods cache results for instant future access")