# components/data_fetcher.py - Enhanced with background cache system

import time
import json
import os
import threading
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# EdgarTools imports
try:
    from edgar import *
except ImportError:
    print("❌ EdgarTools not installed. Install with: pip install edgartools")
    raise

from core.event_system import EventBus, Event, EventType

# Enhanced QuarterlyFinancials with shares outstanding
@dataclass
class QuarterlyFinancials:
    date: str
    revenue: float
    net_income: float
    gross_profit: float
    operating_income: float
    assets: float
    liabilities: float
    cash: float  # Free Cash Flow
    debt: float
    eps: float
    shares_outstanding: float = 0.0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        return cls(**data)

@dataclass
class StockData:
    ticker: str
    company_name: str
    current_price: float
    market_cap: float
    pe_ratio: Optional[float]
    price_change: float
    price_change_percent: float
    quarterly_financials: List[QuarterlyFinancials]
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'ticker': self.ticker,
            'company_name': self.company_name,
            'current_price': self.current_price,
            'market_cap': self.market_cap,
            'pe_ratio': self.pe_ratio,
            'price_change': self.price_change,
            'price_change_percent': self.price_change_percent,
            'quarterly_financials': [q.to_dict() for q in self.quarterly_financials]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary (JSON deserialization)"""
        quarterly_financials = [QuarterlyFinancials.from_dict(q) for q in data.get('quarterly_financials', [])]
        return cls(
            ticker=data['ticker'],
            company_name=data['company_name'],
            current_price=data['current_price'],
            market_cap=data['market_cap'],
            pe_ratio=data['pe_ratio'],
            price_change=data['price_change'],
            price_change_percent=data['price_change_percent'],
            quarterly_financials=quarterly_financials
        )

# Config fallbacks
try:
    from config import EDGARTOOLS_CONFIG, DATA_CONFIG, FINANCIAL_EXTRACTION_CONFIG
except ImportError:
    EDGARTOOLS_CONFIG = {
        'user_identity': 'nfatpro@gmail.com',
        'company_name': 'Stocker App',
        'rate_limit_delay': 0.1,
        'request_timeout': 15
    }
    DATA_CONFIG = {
        'quarters_to_fetch': 12,
        'max_filings_to_process': 15,
        'enable_xbrl_debugging': True,
        'stop_on_target_reached': True
    }
    FINANCIAL_EXTRACTION_CONFIG = {
        'revenue_concepts': ['Revenues', 'Revenue', 'SalesRevenueNet'],
        'operating_cash_flow_concepts': ['NetCashProvidedByUsedInOperatingActivities'],
        'success_criteria_revenue_or_cf': True
    }


class CacheManager:
    """Manages background caching of financial data"""
    
    def __init__(self, base_cache_dir: str = "data/cache"):
        self.base_cache_dir = base_cache_dir
        self.ensure_cache_directory()
        self.cache_update_queue = queue.Queue()
        self.cache_thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="cache")
        self.is_updating = False
        
    def ensure_cache_directory(self):
        """Ensure cache directory structure exists"""
        os.makedirs(self.base_cache_dir, exist_ok=True)
        print(f"📁 Cache directory: {os.path.abspath(self.base_cache_dir)}")
    
    def get_ticker_cache_dir(self, ticker: str) -> str:
        """Get cache directory for specific ticker"""
        ticker_dir = os.path.join(self.base_cache_dir, ticker.upper())
        os.makedirs(ticker_dir, exist_ok=True)
        return ticker_dir
    
    def get_cache_files(self, ticker: str) -> dict:
        """Get all cache file paths for a ticker"""
        ticker_dir = self.get_ticker_cache_dir(ticker)
        return {
            'raw_edgar': os.path.join(ticker_dir, 'raw_edgar_data.json'),
            'quarterly_financials': os.path.join(ticker_dir, 'quarterly_financials.json'),
            'metadata': os.path.join(ticker_dir, 'metadata.json'),
            'cache_info': os.path.join(ticker_dir, 'cache_info.json')
        }
    
    def is_cache_valid(self, ticker: str, max_age_hours: int = 24) -> bool:
        """Check if cache is valid (exists and not too old)"""
        cache_files = self.get_cache_files(ticker)
        
        # Check if quarterly_financials.json exists (main cache file)
        if not os.path.exists(cache_files['quarterly_financials']):
            return False
        
        # Check cache age
        try:
            cache_info_path = cache_files['cache_info']
            if os.path.exists(cache_info_path):
                with open(cache_info_path, 'r') as f:
                    cache_info = json.load(f)
                
                last_update = datetime.fromisoformat(cache_info.get('last_update', '2000-01-01'))
                age_hours = (datetime.now() - last_update).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    print(f"🕒 Cache for {ticker} is {age_hours:.1f} hours old (max: {max_age_hours})")
                    return False
                
                print(f"✅ Cache for {ticker} is valid ({age_hours:.1f} hours old)")
                return True
        except Exception as e:
            print(f"⚠️ Error checking cache age for {ticker}: {e}")
            return False
        
        return True
    
    def save_to_cache(self, ticker: str, raw_data: dict, processed_data: List[QuarterlyFinancials], metadata: dict):
        """Save data to cache files"""
        try:
            cache_files = self.get_cache_files(ticker)
            timestamp = datetime.now().isoformat()
            
            # Save raw EdgarTools data
            with open(cache_files['raw_edgar'], 'w') as f:
                json.dump(raw_data, f, indent=2, default=str)
            
            # Save processed quarterly financials
            quarterly_data = [q.to_dict() for q in processed_data]
            with open(cache_files['quarterly_financials'], 'w') as f:
                json.dump(quarterly_data, f, indent=2)
            
            # Save metadata
            metadata['cache_timestamp'] = timestamp
            with open(cache_files['metadata'], 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save cache info
            cache_info = {
                'ticker': ticker.upper(),
                'last_update': timestamp,
                'quarters_cached': len(processed_data),
                'cache_version': '1.0',
                'files': list(cache_files.keys())
            }
            with open(cache_files['cache_info'], 'w') as f:
                json.dump(cache_info, f, indent=2)
            
            print(f"💾 Cached {len(processed_data)} quarters for {ticker}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving cache for {ticker}: {e}")
            return False
    
    def load_from_cache(self, ticker: str) -> Tuple[Optional[List[QuarterlyFinancials]], Optional[dict]]:
        """Load processed data from cache"""
        try:
            cache_files = self.get_cache_files(ticker)
            
            # Load quarterly financials
            if not os.path.exists(cache_files['quarterly_financials']):
                return None, None
            
            with open(cache_files['quarterly_financials'], 'r') as f:
                quarterly_data = json.load(f)
            
            processed_data = [QuarterlyFinancials.from_dict(q) for q in quarterly_data]
            
            # Load metadata
            metadata = {}
            if os.path.exists(cache_files['metadata']):
                with open(cache_files['metadata'], 'r') as f:
                    metadata = json.load(f)
            
            print(f"📖 Loaded {len(processed_data)} quarters from cache for {ticker}")
            return processed_data, metadata
            
        except Exception as e:
            print(f"❌ Error loading cache for {ticker}: {e}")
            return None, None
    
    def get_cached_tickers(self) -> List[str]:
        """Get list of tickers that have cached data"""
        tickers = []
        try:
            if os.path.exists(self.base_cache_dir):
                for item in os.listdir(self.base_cache_dir):
                    ticker_dir = os.path.join(self.base_cache_dir, item)
                    if os.path.isdir(ticker_dir):
                        cache_files = self.get_cache_files(item)
                        if os.path.exists(cache_files['quarterly_financials']):
                            tickers.append(item.upper())
            return tickers
        except Exception as e:
            print(f"⚠️ Error getting cached tickers: {e}")
            return []
    
    def start_background_refresh(self, edgar_provider, event_bus: EventBus):
        """Start background cache refresh for all cached tickers"""
        if self.is_updating:
            print("🔄 Background refresh already in progress")
            return
        
        cached_tickers = self.get_cached_tickers()
        if not cached_tickers:
            print("📭 No cached tickers to refresh")
            return
        
        print(f"🚀 Starting background refresh for {len(cached_tickers)} tickers")
        
        def refresh_worker():
            self.is_updating = True
            try:
                # Refresh tickers in parallel (max 3 at once for SEC compliance)
                futures = []
                
                for ticker in cached_tickers[:10]:  # Limit to 10 tickers for startup
                    future = self.cache_thread_pool.submit(self._refresh_ticker_cache, ticker, edgar_provider)
                    futures.append((ticker, future))
                
                # Process results as they complete
                for ticker, future in futures:
                    try:
                        success = future.result(timeout=60)  # 60 second timeout per ticker
                        if success:
                            print(f"✅ Background refresh completed for {ticker}")
                        else:
                            print(f"⚠️ Background refresh failed for {ticker}")
                    except Exception as e:
                        print(f"❌ Background refresh error for {ticker}: {e}")
                
                print("🎉 Background cache refresh completed")
                
                # Notify UI that cache has been updated
                event_bus.publish(Event(
                    type=EventType.STATUS_UPDATED,
                    data={'message': 'Background cache refresh completed', 'level': 'info'}
                ))
                
            finally:
                self.is_updating = False
        
        # Start refresh in background thread
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
    
    def _refresh_ticker_cache(self, ticker: str, edgar_provider) -> bool:
        """Refresh cache for a single ticker"""
        try:
            print(f"🔄 Refreshing cache for {ticker}")
            
            # Get fresh data from EdgarTools
            financial_data, metadata = edgar_provider.get_comprehensive_financials(ticker)
            
            if financial_data:
                # Create raw data structure for caching
                raw_data = {
                    'ticker': ticker,
                    'extraction_time': datetime.now().isoformat(),
                    'extraction_method': metadata.get('extraction_method', 'unknown'),
                    'quarters_extracted': len(financial_data),
                    'quarterly_data': [q.to_dict() for q in financial_data]
                }
                
                # Save to cache
                return self.save_to_cache(ticker, raw_data, financial_data, metadata)
            else:
                print(f"⚠️ No fresh data available for {ticker}")
                return False
                
        except Exception as e:
            print(f"❌ Error refreshing cache for {ticker}: {e}")
            return False


class EdgarToolsProvider:
    """EdgarTools provider for all financial data - now with caching"""
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus
        self.last_request_time = 0
        self.rate_limit_delay = EDGARTOOLS_CONFIG.get('rate_limit_delay', 0.1)
        
        # Set Edgar identity (required by SEC)
        try:
            set_identity(EDGARTOOLS_CONFIG.get('user_identity', 'nfatpro@gmail.com'))
            print(f"✅ EdgarTools identity set: {EDGARTOOLS_CONFIG.get('user_identity')}")
        except Exception as e:
            print(f"⚠️ Error setting Edgar identity: {e}")
    
    def _rate_limit(self):
        """Simple rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_comprehensive_financials(self, ticker: str) -> Tuple[List[QuarterlyFinancials], Dict[str, Any]]:
        """Get comprehensive financial data using PROPER EdgarTools approach"""
        print(f"🔍 Fetching EdgarTools data for {ticker}")
        
        try:
            # Get company using EdgarTools
            company = Company(ticker)
            print(f"   Company: {company.name}")
            
            # APPROACH 1: Use company.financials (high-level API) - PRIORITIZED
            print(f"   🎯 Method 1: Using company.financials (high-level API)")
            try:
                financials_data = self._extract_using_financials_api(company, ticker)
                if financials_data:
                    metadata = {
                        'company_name': company.name,
                        'data_source': 'EdgarTools',
                        'quarters_found': len(financials_data),
                        'extraction_method': 'financials_api',
                        'extraction_time': datetime.now().isoformat()
                    }
                    print(f"   ✅ Method 1 Success: {len(financials_data)} quarters")
                    return financials_data, metadata
            except Exception as e:
                print(f"   ⚠️ Method 1 failed: {e}")
            
            # APPROACH 2: Use XBRL instance.query_facts() (backup)
            print(f"   🎯 Method 2: Using XBRL instance.query_facts()")
            try:
                xbrl_data = self._extract_using_xbrl_query_facts(company, ticker)
                if xbrl_data:
                    metadata = {
                        'company_name': company.name,
                        'data_source': 'EdgarTools',
                        'quarters_found': len(xbrl_data),
                        'extraction_method': 'xbrl_query_facts',
                        'extraction_time': datetime.now().isoformat()
                    }
                    print(f"   ✅ Method 2 Success: {len(xbrl_data)} quarters")
                    return xbrl_data, metadata
            except Exception as e:
                print(f"   ⚠️ Method 2 failed: {e}")
            
            # APPROACH 3: Use direct XBRL filings (last resort)
            print(f"   🎯 Method 3: Using direct XBRL filings")
            try:
                filings_data = self._extract_multiple_quarters_data(ticker)
                if filings_data:
                    metadata = {
                        'company_name': company.name,
                        'data_source': 'EdgarTools',
                        'quarters_found': len(filings_data),
                        'extraction_method': 'xbrl_filings_direct',
                        'extraction_time': datetime.now().isoformat()
                    }
                    print(f"   ✅ Method 3 Success: {len(filings_data)} quarters")
                    return filings_data, metadata
            except Exception as e:
                print(f"   ⚠️ Method 3 failed: {e}")
            
            # No data found
            return [], {'error': 'All extraction methods failed', 'data_source': 'EdgarTools'}
            
        except Exception as e:
            print(f"❌ EdgarTools error for {ticker}: {e}")
            return [], {'error': str(e), 'data_source': 'EdgarTools'}
    
    def _extract_using_financials_api(self, company, ticker: str):
        """Extract using high-level financials API"""
        try:
            print(f"   🔧 Trying company.get_financials() API...")
            financials = company.get_financials()
            
            if financials:
                print(f"   📊 Financials object retrieved: {type(financials)}")
                # Try to extract from financials object
                quarters = self._extract_from_financials_object(financials, ticker)
                if quarters:
                    return quarters
            
            # Fallback to multiple quarters method
            print(f"   🔄 Falling back to quarters method...")
            return self._extract_multiple_quarters_data(ticker)
            
        except Exception as e:
            print(f"   ❌ Financials API error: {e}")
            return None
    
    def _extract_using_xbrl_query_facts(self, company, ticker: str):
        """Extract using XBRL query facts"""
        try:
            print(f"   🔧 Trying XBRL query_facts approach...")
            
            # Get a recent filing to test XBRL query
            filings = company.get_filings(form='10-Q').head(1)
            if len(filings) > 0:
                filing = filings[0]
                xbrl_data = filing.xbrl()
                
                if xbrl_data and hasattr(xbrl_data, 'query_facts'):
                    print(f"   📊 XBRL query_facts available")
                    
                    # Test if we can extract data this way
                    revenue_facts = xbrl_data.query_facts(concept='us-gaap:Revenues')
                    if revenue_facts and len(revenue_facts) > 0:
                        print(f"   ✅ Revenue facts found: {len(revenue_facts)}")
                        # If this works, use the multiple quarters method
                        return self._extract_multiple_quarters_data(ticker)
            
            # If no XBRL query support, fall back
            print(f"   🔄 XBRL query not available, using fallback...")
            return None
            
        except Exception as e:
            print(f"   ❌ XBRL query error: {e}")
            return None
    
    def _extract_from_financials_object(self, financials, ticker: str) -> Optional[List[QuarterlyFinancials]]:
        """Extract from EdgarTools financials object"""
        try:
            print(f"   📊 Exploring financials object structure...")
            
            # Check what's available in the financials object
            available_attrs = [attr for attr in dir(financials) if not attr.startswith('_')]
            print(f"   📋 Available attributes: {available_attrs[:10]}...")
            
            # Try to access income statement
            income_data = None
            if hasattr(financials, 'income_statement'):
                income_data = financials.income_statement
            elif hasattr(financials, 'income'):
                income_data = financials.income
            
            if income_data:
                print(f"   📊 Income data type: {type(income_data)}")
                # For now, fall back to filings method for more reliable extraction
                
            # Use the more reliable filings-based extraction
            return self._extract_multiple_quarters_data(ticker)
            
        except Exception as e:
            print(f"   ❌ Financials object extraction error: {e}")
            return None
    
    def _extract_multiple_quarters_data(self, ticker: str) -> List[QuarterlyFinancials]:
        """Extract multiple quarters of data using EdgarTools Company filings"""
        quarterly_data = []
        
        try:
            from edgar import Company
            
            # Get the company
            company = Company(ticker)
            print(f"   🏢 Getting filings for {company.name}")
            
            # Get recent quarterly filings (10-Q forms)
            target_quarters = min(DATA_CONFIG.get('quarters_to_fetch', 12), 12)
            filings = company.get_filings(form='10-Q').head(target_quarters + 3)
            print(f"   📄 Found {len(filings)} quarterly filings")
            
            if len(filings) == 0:
                print(f"   ⚠️ No 10-Q filings found, trying 10-K (annual)")
                filings = company.get_filings(form='10-K').head(4)
                print(f"   📄 Found {len(filings)} annual filings")
            
            # Process each filing
            successful_extractions = 0
            for i, filing in enumerate(filings):
                if successful_extractions >= target_quarters:
                    print(f"   ✅ Reached target of {target_quarters} quarters, stopping")
                    break
                    
                try:
                    print(f"   📋 Processing filing {i+1}: {filing.form} {filing.filing_date}")
                    
                    # Get XBRL data from the filing
                    xbrl_data = filing.xbrl()
                    if xbrl_data is None:
                        print(f"      ⚠️ No XBRL data for filing {filing.filing_date}")
                        continue
                    
                    # Extract data from XBRL
                    quarter_data = self._extract_from_instance_fixed(xbrl_data, filing.filing_date)
                    if quarter_data:
                        quarterly_data.append(quarter_data)
                        successful_extractions += 1
                        revenue_m = quarter_data.revenue / 1e6 if quarter_data.revenue else 0
                        fcf_m = quarter_data.cash / 1e6 if quarter_data.cash else 0
                        print(f"      ✅ {filing.filing_date}: Revenue=${revenue_m:.1f}M, FCF=${fcf_m:.1f}M")
                    else:
                        print(f"      ❌ Failed to extract data from filing {filing.filing_date}")
                        
                except Exception as e:
                    print(f"      ❌ Error processing filing {filing.filing_date}: {e}")
                    continue
            
            # Sort by date (most recent first)
            quarterly_data.sort(key=lambda x: x.date, reverse=True)
            
            print(f"   🎯 Successfully extracted {len(quarterly_data)} quarters")
            return quarterly_data
            
        except Exception as e:
            print(f"   ❌ Error in multiple quarters extraction: {e}")
            return []
    
    def _extract_from_instance_fixed(self, instance, filing_date: str) -> Optional[QuarterlyFinancials]:
        """Extract data from XBRL instance - improved error handling"""
        try:
            date_str = str(filing_date)
            print(f"            🔍 Processing instance for {date_str}")
            
            # Initialize values
            revenue = None
            operating_cf = None
            capex = None
            
            # Try multiple extraction approaches
            print(f"            📊 Instance type: {type(instance)}")
            
            # Method 1: Try query_facts approach
            try:
                revenue = self._extract_revenue_concept(instance)
                if revenue:
                    print(f"            ✅ Revenue extracted: ${revenue/1e6:.1f}M")
            except Exception as e:
                print(f"            ⚠️ Revenue extraction failed: {e}")
            
            try:
                operating_cf = self._extract_cashflow_concept(instance)
                if operating_cf:
                    print(f"            ✅ Operating CF extracted: ${operating_cf/1e6:.1f}M")
            except Exception as e:
                print(f"            ⚠️ Cash flow extraction failed: {e}")
            
            try:
                capex = self._extract_capex_concept(instance)
                if capex:
                    print(f"            ✅ CapEx extracted: ${capex/1e6:.1f}M")
            except Exception as e:
                print(f"            ⚠️ CapEx extraction failed: {e}")
            
            # Method 2: Try facts-based extraction if query_facts failed
            if not revenue and not operating_cf:
                print(f"            🔄 Trying alternative extraction methods...")
                revenue, operating_cf = self._extract_from_facts_alternative(instance)
            
            # Calculate FCF
            fcf = 0.0
            if operating_cf is not None:
                fcf = operating_cf
                if capex is not None:
                    fcf = operating_cf - capex
                print(f"            💰 FCF calculated: ${fcf/1e6:.1f}M")
            
            # Check if we have meaningful data
            min_meaningful = 1000000  # $1M
            has_meaningful_data = (revenue and revenue > min_meaningful) or (operating_cf and abs(operating_cf) > min_meaningful)
            
            if has_meaningful_data:
                quarter_data = QuarterlyFinancials(
                    date=date_str,
                    revenue=float(revenue or 0),
                    net_income=0.0,
                    gross_profit=0.0,
                    operating_income=0.0,
                    assets=0.0,
                    liabilities=0.0,
                    cash=float(fcf),
                    debt=0.0,
                    eps=0.0,
                    shares_outstanding=0.0
                )
                print(f"            ✅ Quarter data created successfully")
                return quarter_data
            else:
                print(f"            ❌ No meaningful data found (Rev: {revenue}, OCF: {operating_cf})")
                return None
            
        except Exception as e:
            print(f"            ❌ Instance extraction error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_from_facts_alternative(self, instance) -> Tuple[Optional[float], Optional[float]]:
        """Alternative facts extraction method"""
        try:
            revenue = None
            operating_cf = None
            
            # Try to access facts directly
            if hasattr(instance, 'facts'):
                facts = instance.facts
                print(f"            📊 Facts type: {type(facts)}")
                
                # If facts is a FactsView, try to convert to DataFrame
                if hasattr(facts, 'to_dataframe'):
                    try:
                        df = facts.to_dataframe()
                        print(f"            📊 DataFrame created: {len(df)} rows")
                        
                        # Look for revenue in DataFrame
                        revenue_concepts = ['Revenues', 'Revenue', 'SalesRevenueNet']
                        for concept in revenue_concepts:
                            concept_rows = df[df['concept'].str.contains(concept, case=False, na=False)]
                            if len(concept_rows) > 0:
                                # Use numeric_value column if available, otherwise value
                                value_col = 'numeric_value' if 'numeric_value' in concept_rows.columns else 'value'
                                revenue_value = concept_rows.iloc[-1][value_col]
                                try:
                                    revenue = float(revenue_value)
                                    if revenue > 1000000:  # > $1M
                                        print(f"            ✅ Found revenue via DataFrame: ${revenue/1e6:.1f}M")
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        # Look for operating cash flow
                        cf_concepts = ['NetCashProvidedByUsedInOperatingActivities', 'CashProvidedByOperatingActivities']
                        for concept in cf_concepts:
                            concept_rows = df[df['concept'].str.contains(concept, case=False, na=False)]
                            if len(concept_rows) > 0:
                                value_col = 'numeric_value' if 'numeric_value' in concept_rows.columns else 'value'
                                cf_value = concept_rows.iloc[-1][value_col]
                                try:
                                    operating_cf = float(cf_value)
                                    if abs(operating_cf) > 1000000:  # > $1M
                                        print(f"            ✅ Found operating CF via DataFrame: ${operating_cf/1e6:.1f}M")
                                        break
                                except (ValueError, TypeError):
                                    continue
                    
                    except Exception as e:
                        print(f"            ⚠️ DataFrame conversion failed: {e}")
                
                # Try iterating through facts if DataFrame approach failed
                if not revenue and not operating_cf:
                    try:
                        print(f"            🔄 Trying facts iteration...")
                        count = 0
                        for fact in facts:
                            if count >= 50:  # Don't process too many
                                break
                            
                            try:
                                concept = getattr(fact, 'concept', str(fact))
                                value = getattr(fact, 'value', None)
                                
                                if value and isinstance(value, (int, float)) and abs(value) > 1000000:
                                    concept_str = str(concept).lower()
                                    
                                    # Look for revenue
                                    if any(keyword in concept_str for keyword in ['revenue', 'income', 'sales']) and not revenue:
                                        if 'loss' not in concept_str or 'income' in concept_str:
                                            revenue = abs(float(value))
                                            print(f"            ✅ Found revenue via iteration: ${revenue/1e6:.1f}M")
                                    
                                    # Look for cash flow
                                    elif 'cash' in concept_str and 'operating' in concept_str and not operating_cf:
                                        operating_cf = float(value)
                                        print(f"            ✅ Found operating CF via iteration: ${operating_cf/1e6:.1f}M")
                                
                                count += 1
                                
                            except Exception:
                                continue
                        
                        print(f"            📊 Processed {count} facts via iteration")
                        
                    except Exception as e:
                        print(f"            ⚠️ Facts iteration failed: {e}")
            
            return revenue, operating_cf
            
        except Exception as e:
            print(f"            ❌ Alternative extraction error: {e}")
            return None, None
    
    def _extract_revenue_concept(self, instance) -> Optional[float]:
        """Extract revenue from XBRL instance - enhanced"""
        revenue_concepts = [
            'Revenues', 'Revenue', 'SalesRevenueNet', 'SalesRevenueGoodsNet',
            'RevenueFromContractWithCustomerExcludingAssessedTax',
            'TotalRevenues', 'OperatingIncomeLoss'
        ]
        
        for concept in revenue_concepts:
            try:
                # Try with us-gaap prefix
                if hasattr(instance, 'query_facts'):
                    facts = instance.query_facts(concept=f'us-gaap:{concept}')
                    if facts and len(facts) > 0:
                        value = self._get_latest_quarterly_value(facts)
                        if value and float(value) > 1000000:  # > $1M
                            return float(value)
                
                # Try without prefix
                if hasattr(instance, 'query_facts'):
                    facts = instance.query_facts(concept=concept)
                    if facts and len(facts) > 0:
                        value = self._get_latest_quarterly_value(facts)
                        if value and float(value) > 1000000:  # > $1M
                            return float(value)
                            
            except Exception as e:
                print(f"            ⚠️ Revenue concept {concept} failed: {e}")
                continue
        return None
    
    def _extract_cashflow_concept(self, instance) -> Optional[float]:
        """Extract operating cash flow from XBRL instance - enhanced"""
        cf_concepts = [
            'NetCashProvidedByUsedInOperatingActivities',
            'NetCashProvidedByOperatingActivities',
            'CashFlowFromOperatingActivities'
        ]
        
        for concept in cf_concepts:
            try:
                # Try with us-gaap prefix
                if hasattr(instance, 'query_facts'):
                    facts = instance.query_facts(concept=f'us-gaap:{concept}')
                    if facts and len(facts) > 0:
                        value = self._get_latest_quarterly_value(facts)
                        if value and abs(float(value)) > 1000000:  # > $1M
                            return float(value)
                
                # Try without prefix
                if hasattr(instance, 'query_facts'):
                    facts = instance.query_facts(concept=concept)
                    if facts and len(facts) > 0:
                        value = self._get_latest_quarterly_value(facts)
                        if value and abs(float(value)) > 1000000:  # > $1M
                            return float(value)
                            
            except Exception as e:
                print(f"            ⚠️ Cash flow concept {concept} failed: {e}")
                continue
        return None
    
    def _extract_capex_concept(self, instance) -> Optional[float]:
        """Extract CapEx from XBRL instance - enhanced"""
        capex_concepts = [
            'PaymentsToAcquirePropertyPlantAndEquipment',
            'PaymentsToAcquireRealEstate',
            'PropertyAndEquipmentAdditions'
        ]
        
        for concept in capex_concepts:
            try:
                # Try with us-gaap prefix
                if hasattr(instance, 'query_facts'):
                    facts = instance.query_facts(concept=f'us-gaap:{concept}')
                    if facts and len(facts) > 0:
                        value = self._get_latest_quarterly_value(facts)
                        if value and abs(float(value)) > 100000:  # > $100K
                            return abs(float(value))  # CapEx is often negative
                
                # Try without prefix
                if hasattr(instance, 'query_facts'):
                    facts = instance.query_facts(concept=concept)
                    if facts and len(facts) > 0:
                        value = self._get_latest_quarterly_value(facts)
                        if value and abs(float(value)) > 100000:  # > $100K
                            return abs(float(value))  # CapEx is often negative
                            
            except Exception as e:
                print(f"            ⚠️ CapEx concept {concept} failed: {e}")
                continue
        return None
    
    def _get_latest_quarterly_value(self, facts):
        """Get the latest quarterly value from facts - enhanced"""
        try:
            if hasattr(facts, '__iter__'):
                # Look for the most recent quarterly value
                latest_value = None
                for fact in facts:
                    if hasattr(fact, 'value') and fact.value is not None:
                        # Prefer quarterly periods over annual
                        if hasattr(fact, 'period') and fact.period:
                            period_str = str(fact.period).lower()
                            if any(term in period_str for term in ['quarter', 'q1', 'q2', 'q3', 'q4', '3m']):
                                return fact.value
                        latest_value = fact.value
                return latest_value
            return None
        except Exception as e:
            print(f"            ⚠️ Error getting latest value: {e}")
            return None


class DataFetcher:
    """Enhanced data fetcher with background cache system"""
    
    def __init__(self, event_bus: EventBus, api_keys: Dict[str, str] = None):
        self.event_bus = event_bus
        
        # Initialize cache manager
        self.cache_manager = CacheManager()
        
        # Initialize EdgarTools provider
        self.edgar_provider = EdgarToolsProvider(event_bus)
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.STOCK_SELECTED, self.fetch_stock_data)
        
        print(f"📊 Enhanced DataFetcher with background cache system initialized")
        
        # Start background cache refresh on startup (delayed)
        threading.Timer(2.0, self._start_background_refresh).start()
    
    def _start_background_refresh(self):
        """Start background cache refresh after app initialization"""
        print("🚀 Starting background cache refresh...")
        self.cache_manager.start_background_refresh(self.edgar_provider, self.event_bus)
    
    def fetch_stock_data(self, event):
        """Fetch stock data - try cache first, then live EdgarTools"""
        ticker = event.data['ticker'].upper()
        
        print(f"\n🔄 FETCHING DATA for {ticker}")
        print("=" * 50)
        
        # Emit fetch started
        self.event_bus.publish(Event(
            type=EventType.DATA_FETCH_STARTED,
            data={'ticker': ticker, 'message': f'Fetching data for {ticker}...'}
        ))
        
        try:
            # Try cache first
            cached_data, cached_metadata = self.cache_manager.load_from_cache(ticker)
            
            if cached_data and self.cache_manager.is_cache_valid(ticker):
                print(f"📖 Using cached data for {ticker}")
                self._emit_success_from_cache(ticker, cached_data, cached_metadata)
            else:
                print(f"🌐 Fetching fresh data for {ticker}")
                self._fetch_fresh_data(ticker)
                
        except Exception as e:
            print(f"❌ Data fetch error for {ticker}: {e}")
            self._emit_error(ticker, f"Data fetch error: {str(e)}", [str(e)])
    
    def _fetch_fresh_data(self, ticker: str):
        """Fetch fresh data from EdgarTools and cache it"""
        try:
            # Get fresh data from EdgarTools
            financial_data, metadata = self.edgar_provider.get_comprehensive_financials(ticker)
            
            if financial_data:
                # Save to cache for future use
                raw_data = {
                    'ticker': ticker,
                    'extraction_time': datetime.now().isoformat(),
                    'extraction_method': metadata.get('extraction_method', 'unknown'),
                    'quarters_extracted': len(financial_data),
                    'quarterly_data': [q.to_dict() for q in financial_data]
                }
                
                self.cache_manager.save_to_cache(ticker, raw_data, financial_data, metadata)
                
                # Emit success with fresh data
                self._emit_success_from_live(ticker, financial_data, metadata)
            else:
                error_msg = metadata.get('error', 'No financial data found')
                self._emit_error(ticker, error_msg, [error_msg])
                
        except Exception as e:
            print(f"❌ Fresh data fetch error for {ticker}: {e}")
            self._emit_error(ticker, f"EdgarTools error: {str(e)}", [str(e)])
    
    def _emit_success_from_cache(self, ticker: str, financial_data: List[QuarterlyFinancials], metadata: dict):
        """Emit success event using cached data"""
        company_name = metadata.get('company_name', f"{ticker} Corporation")
        
        stock_data = StockData(
            ticker=ticker,
            company_name=company_name,
            current_price=0.0,
            market_cap=0.0,
            pe_ratio=None,
            price_change=0.0,
            price_change_percent=0.0,
            quarterly_financials=financial_data
        )
        
        # Separate data for charts
        revenue_data = [q for q in financial_data if q.revenue > 0]
        fcf_data = [q for q in financial_data if q.cash != 0]
        
        enhanced_metadata = {
            **metadata,
            'data_source': 'Cache (EdgarTools)',
            'cache_hit': True,
            'quarters_found': len(financial_data)
        }
        
        self.event_bus.publish(Event(
            type=EventType.DATA_RECEIVED,
            data={
                'stock_data': stock_data,
                'approach': 'cached_edgartools',
                'fcf_data': fcf_data,
                'revenue_data': revenue_data,
                'fcf_available': len(fcf_data) > 0,
                'revenue_available': len(revenue_data) > 0,
                'fcf_source': 'Cache (EdgarTools)',
                'revenue_source': 'Cache (EdgarTools)',
                'metadata': enhanced_metadata,
                'errors': []
            }
        ))