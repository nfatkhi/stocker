# components/data_fetcher.py - Clean XBRL data fetcher for raw SEC data

import time
import json
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# EdgarTools imports
try:
    from edgar import *
    EDGARTOOLS_AVAILABLE = True
except ImportError as e:
    print(f"❌ EdgarTools not available: {e}")
    EDGARTOOLS_AVAILABLE = False
    
    # Placeholder classes
    class Company:
        def __init__(self, *args, **kwargs):
            raise ImportError("EdgarTools not available")
    
    class Filing:
        pass
    
    def set_identity(*args, **kwargs):
        pass

# Config fallbacks
try:
    from config import EDGARTOOLS_CONFIG, DATA_CONFIG
except ImportError:
    EDGARTOOLS_CONFIG = {
        'user_identity': 'nfatpro@gmail.com',
        'rate_limit_delay': 0.1
    }
    DATA_CONFIG = {
        'quarters_to_fetch': 12
    }


@dataclass
class RawXBRLFiling:
    """Raw XBRL filing data - no calculations, just what EdgarTools provides"""
    
    # Basic filing info
    ticker: str
    filing_date: str
    form_type: str = "10-Q"
    company_name: str = ""
    
    # Raw XBRL data from EdgarTools
    facts_json: Optional[str] = None  # Complete facts DataFrame as JSON
    dimensions_json: Optional[str] = None  # Dimensions data as JSON
    statements_info: Optional[Dict] = None  # Available financial statements
    
    # Metadata
    xbrl_object_type: str = "unknown"
    total_facts_count: int = 0
    dimensions_count: int = 0
    statements_available: List[str] = None
    
    # Extraction info
    extraction_timestamp: str = ""
    extraction_success: bool = False
    error_message: Optional[str] = None
    
    # Size info
    original_size_estimate_mb: float = 0.0
    
    def __post_init__(self):
        if self.statements_available is None:
            self.statements_available = []
    
  
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        return cls(**data)


class XBRLDataFetcher:
    """Clean XBRL data fetcher - extracts raw data only"""
    
    def __init__(self):
        if not EDGARTOOLS_AVAILABLE:
            raise ImportError("EdgarTools not available")
            
        self.last_request_time = 0
        self.rate_limit_delay = EDGARTOOLS_CONFIG.get('rate_limit_delay', 0.1)
        
        # Set Edgar identity (required by SEC)
        try:
            identity = EDGARTOOLS_CONFIG.get('user_identity')
            if identity:
                set_identity(identity)
                print(f"✅ EdgarTools identity set: {identity}")
        except Exception as e:
            print(f"⚠️ Error setting Edgar identity: {e}")
    
    def fetch_company_filings(self, ticker: str, max_filings: int = None) -> Tuple[List[RawXBRLFiling], Dict[str, Any]]:
        """
        Fetch raw XBRL filings for a company
        
        Args:
            ticker: Stock ticker symbol
            max_filings: Maximum number of filings to fetch
            
        Returns:
            Tuple of (list of RawXBRLFiling objects, metadata dict)
        """
        if max_filings is None:
            max_filings = DATA_CONFIG.get('quarters_to_fetch', 12)
        
        print(f"🔍 Fetching 10-Q filings for {ticker}")
        
        try:
            self._rate_limit()
            
            # Get company
            company = Company(ticker)
            print(f"   Company: {company.name}")
            
            # Get 10-Q filings only
            quarterly_filings = company.get_filings(form=['10-Q', '10-K']).head(max_filings)
            filings_list = list(quarterly_filings)
            
            if not filings_list:
                return [], {
                    'ticker': ticker,
                    'company_name': company.name,
                    'error': 'No 10-Q filings found',
                    'extraction_timestamp': datetime.now().isoformat()
                }
            
            print(f"   Found {len(filings_list)} 10-Q filings")
            
            # Process each filing
            raw_filings = []
            successful_count = 0
            
            for i, filing in enumerate(filings_list, 1):
                print(f"   Processing {i}/{len(filings_list)}: {filing.filing_date}")
                
                raw_filing = self._extract_raw_xbrl(filing, ticker, company.name)
                
                if raw_filing and raw_filing.extraction_success:
                    raw_filings.append(raw_filing)
                    successful_count += 1
                    
                    print(f"      ✅ Success - Raw XBRL extracted")
                else:
                    error = raw_filing.error_message if raw_filing else "Unknown error"
                    print(f"      ❌ Failed: {error}")
            
            # Create metadata
            metadata = {
                'ticker': ticker,
                'company_name': company.name,
                'filings_found': len(filings_list),
                'successful_extractions': successful_count,
                'extraction_timestamp': datetime.now().isoformat(),
                'data_source': 'SEC EDGAR via EdgarTools'
            }
            
            print(f"   Extraction complete: {successful_count}/{len(filings_list)} successful")
            
            return raw_filings, metadata
            
        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")
            return [], {
                'ticker': ticker,
                'error': str(e),
                'extraction_timestamp': datetime.now().isoformat()
            }
    
    def _extract_raw_xbrl(self, filing, ticker: str, company_name: str) -> RawXBRLFiling:
        """Extract raw XBRL data from filing - no calculations"""
        
        raw_filing = RawXBRLFiling(
            ticker=ticker,
            filing_date=str(filing.filing_date),
            company_name=company_name,
            extraction_timestamp=datetime.now().isoformat()
        )
        
        try:
            # Get XBRL data
            xbrl_data = filing.xbrl()
            if not xbrl_data:
                raw_filing.error_message = "No XBRL data in filing"
                return raw_filing
            
            # Record XBRL object type
            raw_filing.xbrl_object_type = type(xbrl_data).__name__
            
            # Get instance
            instance = xbrl_data.instance if hasattr(xbrl_data, 'instance') else xbrl_data
            
            # Extract facts DataFrame
            if hasattr(instance, 'facts') and hasattr(instance.facts, 'to_dataframe'):
                try:
                    facts_df = instance.facts.to_dataframe()
                    raw_filing.facts_json = facts_df.to_json(orient='records', date_format='iso')
                    raw_filing.total_facts_count = len(facts_df)
                    print(f"      Facts extracted: {raw_filing.total_facts_count}")
                except Exception as e:
                    print(f"      Facts extraction failed: {e}")
            
            # Extract dimensions
            if hasattr(instance, 'dimensions'):
                try:
                    dimensions_dict = {}
                    for dim_name, dim_values in instance.dimensions.items():
                        dimensions_dict[dim_name] = list(dim_values)
                    
                    raw_filing.dimensions_json = json.dumps(dimensions_dict)
                    raw_filing.dimensions_count = len(dimensions_dict)
                    print(f"      Dimensions extracted: {raw_filing.dimensions_count}")
                except Exception as e:
                    print(f"      Dimensions extraction failed: {e}")
            
            # Extract statements info
            if hasattr(xbrl_data, 'statements'):
                try:
                    statements_info = {'available_statements': []}
                    
                    if hasattr(xbrl_data.statements, 'keys'):
                        statements_info['available_statements'] = list(xbrl_data.statements.keys())
                    
                    raw_filing.statements_info = statements_info
                    raw_filing.statements_available = statements_info['available_statements']
                    print(f"      Statements found: {len(raw_filing.statements_available)}")
                except Exception as e:
                    print(f"      Statements extraction failed: {e}")
            
            # Calculate size estimate
            total_size = 0
            if raw_filing.facts_json:
                total_size += len(raw_filing.facts_json)
            if raw_filing.dimensions_json:
                total_size += len(raw_filing.dimensions_json)
            if raw_filing.statements_info:
                total_size += len(json.dumps(raw_filing.statements_info))
            
            raw_filing.original_size_estimate_mb = total_size / (1024 * 1024)
            
            # Determine success
            if raw_filing.facts_json and raw_filing.total_facts_count > 0:
                raw_filing.extraction_success = True
            else:
                raw_filing.error_message = "No usable facts data extracted"
            
            return raw_filing
            
        except Exception as e:
            raw_filing.error_message = f"XBRL extraction error: {str(e)}"
            return raw_filing
    
    def _rate_limit(self):
        """Rate limiting for SEC compliance"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()


# Simple interface function
def fetch_company_data(ticker: str, max_filings: int = None) -> Tuple[List[RawXBRLFiling], Dict[str, Any]]:
    """
    Fetch raw company XBRL data
    
    Args:
        ticker: Stock ticker symbol
        max_filings: Maximum filings to fetch
        
    Returns:
        Tuple of (raw filings list, metadata dict)
    """
    if not EDGARTOOLS_AVAILABLE:
        return [], {'error': 'EdgarTools not available', 'ticker': ticker}
        
    fetcher = XBRLDataFetcher()
    return fetcher.fetch_company_filings(ticker, max_filings)