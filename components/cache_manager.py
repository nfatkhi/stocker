# components/cache_manager.py - Updated for 15 quarters cache with 12 display limit

import os
import json
import time
import threading
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from components.data_fetcher import fetch_company_data, RawXBRLFiling
from components.xbrl_extractor import extract_multi_row_financials, MultiRowFinancialData
from core.event_system import (
    get_global_event_bus, EventType, Event, create_cache_hit_event,
    create_cache_miss_event, create_cache_update_event, create_new_filing_event,
    create_background_cache_event
)

try:
    from config import DATA_CONFIG
except ImportError:
    DATA_CONFIG = {'quarters_to_fetch': 12, 'cache_directory': 'data/cache'}


@dataclass
class CachedQuarter:
    quarter: str
    year: int
    filing_date: str
    file_path: str
    cached_timestamp: str
    file_size_mb: float = 0.0
    fact_rows_count: int = 0  # NEW: Track number of fact rows
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


@dataclass 
class TickerMetadata:
    ticker: str
    company_name: str
    last_updated: str
    cached_quarters: List[CachedQuarter]
    total_quarters_cached: int
    last_filing_check: str
    latest_cached_filing_date: str = ""
    total_fact_rows: int = 0  # NEW: Track total fact rows across all quarters
    
    def to_dict(self) -> Dict:
        return {
            'ticker': self.ticker,
            'company_name': self.company_name,
            'last_updated': self.last_updated,
            'cached_quarters': [q.to_dict() for q in self.cached_quarters],
            'total_quarters_cached': self.total_quarters_cached,
            'last_filing_check': self.last_filing_check,
            'latest_cached_filing_date': self.latest_cached_filing_date,
            'total_fact_rows': self.total_fact_rows
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        quarters = [CachedQuarter.from_dict(q) for q in data.get('cached_quarters', [])]
        return cls(
            ticker=data['ticker'],
            company_name=data['company_name'],
            last_updated=data['last_updated'],
            cached_quarters=quarters,
            total_quarters_cached=data['total_quarters_cached'],
            last_filing_check=data['last_filing_check'],
            latest_cached_filing_date=data.get('latest_cached_filing_date', ''),
            total_fact_rows=data.get('total_fact_rows', 0)
        )


class MultiRowCacheFileManager:
    """Enhanced cache file manager for multi-row data"""
    
    def __init__(self, cache_dir: str):
        self.cache_dir = cache_dir
        self.cache_index_path = os.path.join(cache_dir, 'cache_index.json')
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_ticker_dir(self, ticker: str) -> str:
        return os.path.join(self.cache_dir, ticker.upper())
    
    def ticker_cache_exists(self, ticker: str) -> bool:
        ticker_dir = self.get_ticker_dir(ticker)
        return os.path.exists(ticker_dir) and os.path.isdir(ticker_dir)
    
    def load_cache_index(self) -> Dict:
        try:
            if os.path.exists(self.cache_index_path):
                with open(self.cache_index_path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            'tickers': [], 
            'total_tickers': 0, 
            'last_global_update': datetime.now().isoformat(),
            'cache_format_version': '3.0_revenue_concepts'  # UPDATED: New cache format version
        }
    
    def save_cache_index(self, index_data: Dict):
        try:
            index_data['cache_format_version'] = '3.0_revenue_concepts'  # UPDATED: New cache format version
            with open(self.cache_index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
        except Exception:
            pass
    
    def save_multi_row_quarter_data(self, ticker: str, filename: str, 
                                   multi_row_data: MultiRowFinancialData) -> Tuple[float, int]:
        """Save multi-row data and return file size + fact count"""
        ticker_dir = self.get_ticker_dir(ticker)
        os.makedirs(ticker_dir, exist_ok=True)
        
        # Use multi_row prefix to distinguish from old format
        multi_row_filename = filename.replace('.json', '_multi_row.json')
        file_path = os.path.join(ticker_dir, multi_row_filename)
        
        # Convert to dict for JSON serialization
        data_dict = multi_row_data.to_dict()
        
        with open(file_path, 'w') as f:
            json.dump(data_dict, f, separators=(',', ':'))
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        fact_rows_count = multi_row_data.total_fact_rows
        
        return file_size_mb, fact_rows_count
    
    def load_multi_row_quarter_data(self, ticker: str, filename: str) -> Optional[MultiRowFinancialData]:
        """Load multi-row data"""
        try:
            # Try multi_row format first
            multi_row_filename = filename.replace('.json', '_multi_row.json')
            file_path = os.path.join(self.get_ticker_dir(ticker), multi_row_filename)
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                try:
                    return MultiRowFinancialData.from_dict(data)
                except Exception as e:
                    print(f"   ⚠️ Error loading multi-row data for {ticker}: {e}")
                    # Clean up corrupted file
                    try:
                        os.remove(file_path)
                    except:
                        pass
                    return None
            
            return None
            
        except Exception:
            return None
    
    def load_ticker_metadata(self, ticker: str) -> Optional[TickerMetadata]:
        try:
            metadata_path = os.path.join(self.get_ticker_dir(ticker), 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                return TickerMetadata.from_dict(data)
        except Exception:
            pass
        return None
    
    def save_ticker_metadata(self, ticker: str, metadata: TickerMetadata):
        try:
            ticker_dir = self.get_ticker_dir(ticker)
            os.makedirs(ticker_dir, exist_ok=True)
            metadata_path = os.path.join(ticker_dir, 'metadata.json')
            
            # Update latest filing date and total fact rows
            if metadata.cached_quarters:
                latest_date = max(q.filing_date for q in metadata.cached_quarters)
                metadata.latest_cached_filing_date = latest_date
                metadata.total_fact_rows = sum(q.fact_rows_count for q in metadata.cached_quarters)
            else:
                metadata.latest_cached_filing_date = ""
                metadata.total_fact_rows = 0
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
        except Exception:
            pass
    
    def add_ticker_to_index(self, ticker: str):
        cache_index = self.load_cache_index()
        if ticker not in cache_index.get('tickers', []):
            cache_index.setdefault('tickers', []).append(ticker)
            cache_index['total_tickers'] = len(cache_index['tickers'])
            cache_index['last_global_update'] = datetime.now().isoformat()
            self.save_cache_index(cache_index)
    
    def remove_ticker_from_index(self, ticker: str):
        cache_index = self.load_cache_index()
        if ticker in cache_index.get('tickers', []):
            cache_index['tickers'].remove(ticker)
            cache_index['total_tickers'] = len(cache_index['tickers'])
            self.save_cache_index(cache_index)
    
    def delete_ticker_cache(self, ticker: str) -> bool:
        try:
            ticker_dir = self.get_ticker_dir(ticker)
            if os.path.exists(ticker_dir):
                shutil.rmtree(ticker_dir)
                return True
        except Exception:
            pass
        return False


class MultiRowCacheManager:
    """Enhanced cache manager for multi-row XBRL data (49 universal concepts)"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = cache_dir or DATA_CONFIG.get('cache_directory', 'data/cache')
        self.max_quarters_cache = 15  # UPDATED: Cache 15 quarters for optimal Q4 calculation
        self.max_quarters_display = 12  # Display only 12 quarters in charts
        
        self.file_manager = MultiRowCacheFileManager(self.cache_dir)
        self.event_publisher = CacheEventPublisher()
        self.rate_limiter = RateLimiter(delay=0.2)
        
        self._initialize()
        
        print(f"🚀 Multi-Row Cache Manager initialized")
        print(f"   📊 49 universal concepts with ALL fact rows (added revenue)")
        print(f"   📁 Cache directory: {self.cache_dir}")
        print(f"   🔄 Cache quarters: {self.max_quarters_cache} (display: {self.max_quarters_display})")
    
    def _initialize(self):
        self.event_publisher.publish_cache_event(
            EventType.COMPONENT_READY,
            component='MultiRowCacheManager',
            cache_dir=self.cache_dir,
            max_quarters_cache=self.max_quarters_cache,
            max_quarters_display=self.max_quarters_display,
            concepts_tracked=49,  # UPDATED: Now 49 concepts
            data_format='multi_row_facts'
        )
    
    def get_ticker_data(self, ticker: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Get ticker data - returns 12 most recent quarters for display"""
        ticker = ticker.upper()
        
        # Ensure cache exists (with 15 quarters)
        cache_result = self._ensure_ticker_cache(ticker)
        
        if cache_result['action'] == 'failed':
            error_msg = f"Failed to ensure cache for {ticker}: {cache_result['reason']}"
            self.event_publisher.publish_error(error_msg, ticker=ticker, operation='ensure_cache')
            return [], {'error': error_msg}
        
        elif cache_result['action'] == 'created':
            self.event_publisher.publish_cache_update(
                ticker, cache_result['cached_quarters'], cache_result['cached_quarters']
            )
        
        return self._load_ticker_multi_row_data(ticker)
    
    def get_ticker_data_for_calculation(self, ticker: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Get ALL cached ticker data (15 quarters) for Q4 calculations"""
        ticker = ticker.upper()
        
        # Load all cached data without display limit
        ticker_metadata = self.file_manager.load_ticker_metadata(ticker)
        if not ticker_metadata:
            return [], {'error': f'No metadata for {ticker}'}
        
        quarterly_data = []
        for cached_quarter in ticker_metadata.cached_quarters:
            multi_row_data = self.file_manager.load_multi_row_quarter_data(ticker, cached_quarter.file_path)
            if multi_row_data:
                quarterly_data.append(multi_row_data.to_dict())
        
        # Sort by filing date (most recent first) but return ALL data
        quarterly_data.sort(key=lambda x: x.get('filing_date', ''), reverse=True)
        
        metadata = {
            'ticker': ticker,
            'company_name': ticker_metadata.company_name,
            'quarters_loaded': len(quarterly_data),
            'data_source': 'Multi-Row Cache (ALL quarters for calculation)',
            'cache_format': 'multi_row_facts',
            'total_quarters_cached': len(quarterly_data)
        }
        
        return quarterly_data, metadata
    
    def _ensure_ticker_cache(self, ticker: str) -> Dict[str, Any]:
        """Ensure ticker cache exists with multi-row data"""
        if not self.file_manager.ticker_cache_exists(ticker):
            return self._create_initial_multi_row_cache(ticker)
        else:
            return {
                'action': 'no_update',
                'reason': 'cache_folder_exists',
                'cached_quarters': 'unknown',
                'mode': 'quick'
            }
    
    def _create_initial_multi_row_cache(self, ticker: str) -> Dict[str, Any]:
        """Create initial cache with multi-row data - FETCH 15 quarters"""
        try:
            print(f"🔄 Creating multi-row cache for {ticker} (15 quarters)")
            
            self.rate_limiter.wait()
            # UPDATED: Fetch 15 quarters for optimal Q4 calculation coverage
            raw_filings, metadata = fetch_company_data(ticker, max_filings=self.max_quarters_cache)
            
            if not raw_filings:
                return {
                    'action': 'failed',
                    'reason': 'no_data_available',
                    'cached_quarters': 0
                }
            
            ticker_metadata = TickerMetadata(
                ticker=ticker,
                company_name=metadata.get('company_name', f'{ticker} Corporation'),
                last_updated=datetime.now().isoformat(),
                cached_quarters=[],
                total_quarters_cached=0,
                last_filing_check=datetime.now().isoformat()
            )
            
            self.file_manager.add_ticker_to_index(ticker)
            
            # Sort filings by date (most recent first)
            sorted_filings = sorted(raw_filings, key=lambda f: f.filing_date, reverse=True)
            cached_quarters = []
            
            print(f"   📊 Extracting multi-row data from {len(sorted_filings)} filings (15 quarters for Q4 calc)...")
            
            for i, raw_filing in enumerate(sorted_filings, 1):
                print(f"   Processing {i}/{len(sorted_filings)}: {raw_filing.filing_date}")
                
                # Extract multi-row data (49 concepts with all fact rows)
                multi_row_data = extract_multi_row_financials(raw_filing)
                
                if multi_row_data.extraction_success:
                    # Generate filename from extracted data
                    quarter_filename = self._generate_quarter_filename(multi_row_data)
                    
                    # Save multi-row data
                    file_size_mb, fact_rows_count = self.file_manager.save_multi_row_quarter_data(
                        ticker, quarter_filename, multi_row_data
                    )
                    
                    cached_quarter = CachedQuarter(
                        quarter=multi_row_data.quarter,
                        year=multi_row_data.year,
                        filing_date=raw_filing.filing_date,
                        file_path=quarter_filename,
                        cached_timestamp=datetime.now().isoformat(),
                        file_size_mb=file_size_mb,
                        fact_rows_count=fact_rows_count
                    )
                    cached_quarters.append(cached_quarter)
                    
                    print(f"      ✅ {multi_row_data.concepts_extracted}/49 concepts, {fact_rows_count} fact rows")
                else:
                    print(f"      ❌ Extraction failed: {multi_row_data.concepts_extracted}/49 concepts")
            
            if cached_quarters:
                ticker_metadata.cached_quarters = cached_quarters
                ticker_metadata.total_quarters_cached = len(cached_quarters)
                self.file_manager.save_ticker_metadata(ticker, ticker_metadata)
                
                total_fact_rows = sum(q.fact_rows_count for q in cached_quarters)
                
                print(f"   ✅ Cache created: {len(cached_quarters)} quarters (15 for Q4), {total_fact_rows} total fact rows")
                
                return {
                    'action': 'created',
                    'reason': 'multi_row_cache_created_15_quarters',
                    'cached_quarters': len(cached_quarters),
                    'total_fact_rows': total_fact_rows
                }
            else:
                return {
                    'action': 'failed',
                    'reason': 'no_data_extracted',
                    'cached_quarters': 0
                }
                
        except Exception as e:
            print(f"❌ Error creating multi-row cache: {e}")
            return {
                'action': 'failed',
                'reason': str(e),
                'cached_quarters': 0
            }
    
    def _load_ticker_multi_row_data(self, ticker: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """Load multi-row data for ticker - LIMIT TO 12 quarters for display"""
        ticker_metadata = self.file_manager.load_ticker_metadata(ticker)
        if not ticker_metadata:
            error_msg = f'Failed to load metadata for {ticker}'
            self.event_publisher.publish_error(error_msg, ticker=ticker, operation='metadata_load')
            return [], {'error': error_msg}
        
        quarterly_data = []
        for cached_quarter in ticker_metadata.cached_quarters:
            multi_row_data = self.file_manager.load_multi_row_quarter_data(ticker, cached_quarter.file_path)
            if multi_row_data:
                quarterly_data.append(multi_row_data.to_dict())
        
        # Sort by filing date (most recent first)
        quarterly_data.sort(key=lambda x: x.get('filing_date', ''), reverse=True)
        
        # UPDATED: Limit to 12 quarters for display (but keep all 15 in cache)
        display_quarters = quarterly_data[:self.max_quarters_display]
        
        metadata = {
            'ticker': ticker,
            'company_name': ticker_metadata.company_name,
            'quarters_loaded': len(display_quarters),
            'quarters_cached_total': len(quarterly_data),  # Show total cached
            'last_updated': ticker_metadata.last_updated,
            'latest_cached_filing': ticker_metadata.latest_cached_filing_date,
            'data_source': 'Multi-Row Cache (49 Concepts)',
            'cache_format': 'multi_row_facts',
            'total_fact_rows': ticker_metadata.total_fact_rows,
            'concepts_per_quarter': 49,  # UPDATED: Now 49 concepts
            'display_limit': self.max_quarters_display,
            'cache_limit': self.max_quarters_cache
        }
        
        self.event_publisher.publish_cache_hit(ticker, len(display_quarters))
        
        print(f"📊 Loaded {len(display_quarters)}/{len(quarterly_data)} quarters for display (cached: {len(quarterly_data)})")
        
        return display_quarters, metadata
    
    def _generate_quarter_filename(self, multi_row_data: MultiRowFinancialData) -> str:
        """Generate filename from multi-row data"""
        quarter = multi_row_data.quarter if multi_row_data.quarter != "Unknown" else "QX"
        year = multi_row_data.year if multi_row_data.year > 0 else 2024
        
        filename = f"{year}_{quarter}_multi_row.json"
        return filename
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get enhanced cache statistics"""
        try:
            cache_index = self.file_manager.load_cache_index()
            tickers = cache_index.get('tickers', [])
            
            total_size_mb = 0
            total_quarters = 0
            total_fact_rows = 0
            ticker_stats = {}
            
            for ticker in tickers:
                ticker_metadata = self.file_manager.load_ticker_metadata(ticker)
                if ticker_metadata:
                    ticker_size = sum(q.file_size_mb for q in ticker_metadata.cached_quarters)
                    ticker_fact_rows = sum(q.fact_rows_count for q in ticker_metadata.cached_quarters)
                    
                    total_size_mb += ticker_size
                    total_quarters += ticker_metadata.total_quarters_cached
                    total_fact_rows += ticker_fact_rows
                    
                    ticker_stats[ticker] = {
                        'quarters': ticker_metadata.total_quarters_cached,
                        'size_mb': round(ticker_size, 2),
                        'fact_rows': ticker_fact_rows,
                        'last_updated': ticker_metadata.last_updated,
                        'latest_cached_filing': ticker_metadata.latest_cached_filing_date
                    }
            
            stats = {
                'total_tickers': len(tickers),
                'total_quarters_cached': total_quarters,
                'total_cache_size_mb': round(total_size_mb, 2),
                'total_fact_rows': total_fact_rows,
                'cache_format': 'multi_row_facts',
                'concepts_per_quarter': 49,  # UPDATED: Now 49 concepts
                'cache_format_version': cache_index.get('cache_format_version', '3.0_revenue_concepts'),
                'cache_directory': self.cache_dir,
                'cache_quarters': self.max_quarters_cache,
                'display_quarters': self.max_quarters_display,
                'ticker_stats': ticker_stats
            }
            
            return stats
            
        except Exception as e:
            error_msg = f'Failed to get cache stats: {e}'
            self.event_publisher.publish_error(error_msg, operation='cache_stats')
            return {'error': error_msg}
    
    def force_refresh_ticker(self, ticker: str) -> bool:
        """Force refresh ticker cache"""
        ticker = ticker.upper()
        
        try:
            if self.file_manager.delete_ticker_cache(ticker):
                print(f"🗑️ Deleted old cache for {ticker}")
            
            self.file_manager.remove_ticker_from_index(ticker)
            cache_result = self._create_initial_multi_row_cache(ticker)
            
            return cache_result['action'] in ['created', 'updated']
            
        except Exception:
            return False


# Add required helper classes from original
class CacheEventPublisher:
    def __init__(self):
        self.event_bus = get_global_event_bus()
    
    def publish_cache_event(self, event_type: EventType, ticker: str = None, **extra_data) -> None:
        data = {'ticker': ticker, **extra_data}
        event = Event(type=event_type, data=data, source='multi_row_cache_manager')
        self.event_bus.publish(event)
    
    def publish_cache_hit(self, ticker: str, quarters_loaded: int):
        self.event_bus.publish(create_cache_hit_event(ticker, quarters_loaded))
    
    def publish_cache_miss(self, ticker: str, reason: str):
        self.event_bus.publish(create_cache_miss_event(ticker, reason))
    
    def publish_cache_update(self, ticker: str, new_quarters: int, total_quarters: int):
        self.event_bus.publish(create_cache_update_event(ticker, new_quarters, total_quarters))
    
    def publish_error(self, error: str, ticker: str = None, operation: str = None):
        self.publish_cache_event(EventType.ERROR_OCCURRED, ticker=ticker, error=error, operation=operation)


class RateLimiter:
    def __init__(self, delay: float = 0.2):
        self.delay = delay
        self.last_request_time = 0
        self._lock = threading.Lock()
    
    def wait(self):
        with self._lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.delay:
                time.sleep(self.delay - time_since_last)
            self.last_request_time = time.time()


# Compatibility alias for existing code
CacheManager = MultiRowCacheManager

# Main interface function
def get_multi_row_ticker_data(ticker: str) -> Tuple[List[Dict], Dict[str, Any]]:
    """Get ticker data using multi-row cache system"""
    cache_manager = MultiRowCacheManager()
    return cache_manager.get_ticker_data(ticker)


if __name__ == "__main__":
    print("🧪 Testing Multi-Row Cache Manager")
    print("=" * 50)
    
    # Test initialization
    cache_manager = MultiRowCacheManager()
    
    # Show cache stats
    stats = cache_manager.get_cache_stats()
    print(f"📊 Cache Statistics:")
    for key, value in stats.items():
        if key != 'ticker_stats':
            print(f"   {key}: {value}")
    
    print(f"\n✅ Multi-Row Cache Manager ready!")
    print(f"🔄 Each quarter contains 49 universal concepts (added revenue)")
    print(f"📊 All fact rows preserved for each concept")
    print(f"💾 Efficient storage with complete context information")