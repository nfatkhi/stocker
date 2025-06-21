# components/data_fetcher.py - Working SEC EDGAR implementation with fixed imports

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
import time
from dataclasses import dataclass

from core.event_system import EventBus, Event, EventType

# Define models directly to avoid import issues
@dataclass
class QuarterlyFinancials:
    date: str
    revenue: float
    net_income: float
    gross_profit: float
    operating_income: float
    assets: float
    liabilities: float
    cash: float
    debt: float
    eps: float

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

try:
    from config import DATA_CONFIG
except ImportError:
    DATA_CONFIG = {
        'quarters_to_fetch': 12,
    }


class SECEdgarProvider:
    """Working SEC EDGAR provider that fetches quarterly revenue from 'Revenues' concept"""
    
    def __init__(self):
        # SEC requires proper User-Agent
        self.headers = {
            'User-Agent': f"{SEC_EDGAR_CONFIG['company_name']} {SEC_EDGAR_CONFIG['contact_email']}",
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov',
            'Accept': 'application/json'
        }
        
        self.base_url = 'https://data.sec.gov/api/xbrl'
        self.last_request_time = 0
        self.rate_limit_delay = SEC_EDGAR_CONFIG['rate_limit_delay']
        
        # Known CIKs for major companies - this avoids ticker lookup issues
        self.known_ciks = {
            'AAPL': '0000320193',  # Apple Inc.
            'MSFT': '0000789019',  # Microsoft Corporation
            'GOOGL': '0001652044', # Alphabet Inc.
            'GOOG': '0001652044',  # Alphabet Inc.
            'AMZN': '0001018724',  # Amazon.com Inc.
            'TSLA': '0001318605',  # Tesla Inc.
            'META': '0001326801',  # Meta Platforms Inc.
            'FB': '0001326801',    # Meta Platforms Inc. (old ticker)
            'NVDA': '0000788811',  # NVIDIA Corporation
            'O': '0000726728',     # Realty Income Corporation
            'BRK.A': '0001067983', # Berkshire Hathaway Inc.
            'BRK.B': '0001067983', # Berkshire Hathaway Inc.
            'JNJ': '0000200406',   # Johnson & Johnson
            'JPM': '0000019617',   # JPMorgan Chase & Co.
            'V': '0001403161',     # Visa Inc.
            'PG': '0000080424',    # Procter & Gamble Co.
            'UNH': '0000731766',   # UnitedHealth Group Inc.
            'HD': '0000354950',    # Home Depot Inc.
            'MA': '0001141391',    # Mastercard Inc.
            'DIS': '0001001039',   # Walt Disney Co.
            'NFLX': '0001065280',  # Netflix Inc.
            'CRM': '0001108524',   # Salesforce Inc.
            'AMD': '0000002488',   # Advanced Micro Devices Inc.
            'PYPL': '0001633917',  # PayPal Holdings Inc.
            'INTC': '0000050863',  # Intel Corporation
            'CSCO': '0000858877',  # Cisco Systems Inc.
            'PFE': '0000078003',   # Pfizer Inc.
            'KO': '0000021344',    # Coca-Cola Co.
            'PEP': '0000077476',   # PepsiCo Inc.
            'TMO': '0000097745',   # Thermo Fisher Scientific Inc.
            'COST': '0000909832',  # Costco Wholesale Corporation
            'AVGO': '0001730168',  # Broadcom Inc.
        }
        
        print(f"🏛️ SEC EDGAR Provider initialized")
        print(f"📧 Contact: {SEC_EDGAR_CONFIG['contact_email']}")
        print(f"📊 Known companies: {len(self.known_ciks)}")
    
    def _rate_limit(self):
        """Rate limiting to be respectful to SEC servers"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_quarterly_financials(self, ticker: str) -> List[QuarterlyFinancials]:
        """Get quarterly revenue data from SEC EDGAR 'Revenues' concept"""
        try:
            print(f"🏛️ SEC EDGAR: Fetching data for {ticker}")
            
            # Check if we have the CIK for this ticker
            cik = self.known_ciks.get(ticker.upper())
            if not cik:
                print(f"❌ Unknown ticker {ticker}")
                print(f"💡 Known tickers: {list(self.known_ciks.keys())[:10]}...")
                return []
            
            print(f"✅ Found CIK {cik} for {ticker}")
            
            # Get revenue data from 'Revenues' concept
            revenue_data = self._get_revenues_concept_data(cik, ticker)
            if not revenue_data:
                print(f"❌ No revenue data found for {ticker}")
                return []
            
            # Extract quarterly financials
            quarterly_data = self._extract_quarterly_revenue_data(revenue_data, ticker)
            
            if quarterly_data:
                print(f"✅ SEC EDGAR: Retrieved {len(quarterly_data)} quarters for {ticker}")
                # Show recent quarters for verification
                for i, quarter in enumerate(quarterly_data[:3]):
                    revenue_b = quarter.revenue / 1e9 if quarter.revenue > 0 else 0
                    print(f"   Q{i+1}: {quarter.date} - Revenue: ${revenue_b:.2f}B")
            else:
                print(f"⚠️ No quarterly revenue data extracted for {ticker}")
            
            return quarterly_data
            
        except Exception as e:
            print(f"❌ SEC EDGAR error for {ticker}: {e}")
            return []
    
    def _get_revenues_concept_data(self, cik: str, ticker: str) -> Optional[List[Dict]]:
        """Get data from the 'Revenues' concept endpoint"""
        self._rate_limit()
        
        url = f"{self.base_url}/companyconcept/CIK{cik}/us-gaap/Revenues.json"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=SEC_EDGAR_CONFIG['request_timeout'])
            
            if response.status_code == 200:
                data = response.json()
                company_name = data.get('entityName', ticker)
                print(f"✅ Retrieved revenue concept data for {company_name}")
                
                # Get USD revenue data
                usd_data = data.get('units', {}).get('USD', [])
                print(f"📊 Found {len(usd_data)} revenue records")
                
                return usd_data
            elif response.status_code == 404:
                print(f"⚠️ No revenue concept data found for {ticker}")
            else:
                print(f"⚠️ SEC API error: HTTP {response.status_code}")
            
        except Exception as e:
            print(f"⚠️ Error fetching revenue concept data: {e}")
        
        return None
    
    def _extract_quarterly_revenue_data(self, revenue_data: List[Dict], ticker: str) -> List[QuarterlyFinancials]:
        """Extract clean quarterly revenue data from SEC revenue records"""
        quarterly_data = []
        
        try:
            print(f"🔍 Extracting quarterly data for {ticker}")
            
            # Filter for 10-Q quarterly filings only
            quarterly_records = [
                record for record in revenue_data 
                if record.get('form') == '10-Q' and record.get('val', 0) > 0
            ]
            
            print(f"📋 Found {len(quarterly_records)} quarterly (10-Q) records")
            
            if not quarterly_records:
                print(f"❌ No 10-Q quarterly records found")
                return []
            
            # Sort by end date (newest first)
            quarterly_records.sort(key=lambda x: x.get('end', ''), reverse=True)
            
            # Create quarterly financial objects
            for record in quarterly_records:
                end_date = record.get('end', '')
                start_date = record.get('start', '')
                revenue = record.get('val', 0)
                form = record.get('form', '')
                fy = record.get('fy', '')
                fp = record.get('fp', '')
                filed_date = record.get('filed', '')
                
                if not end_date or revenue <= 0:
                    continue
                
                # Create quarterly financial record
                quarterly_financial = QuarterlyFinancials(
                    date=end_date,
                    revenue=float(revenue),
                    net_income=0.0,  # We'll need other concepts for these
                    gross_profit=0.0,
                    operating_income=0.0,
                    assets=0.0,
                    liabilities=0.0,
                    cash=0.0,
                    debt=0.0,
                    eps=0.0
                )
                
                quarterly_data.append(quarterly_financial)
                
                # Debug output
                revenue_b = revenue / 1e9
                print(f"   ✅ {end_date}: ${revenue_b:.2f}B (Period: {start_date} to {end_date}, {fp} {fy})")
            
            # Limit to requested number of quarters
            max_quarters = DATA_CONFIG.get('quarters_to_fetch', 12)
            return quarterly_data[:max_quarters]
            
        except Exception as e:
            print(f"❌ Error extracting quarterly data: {e}")
            return []
    
    def is_ticker_supported(self, ticker: str) -> bool:
        """Check if ticker is supported (has known CIK)"""
        return ticker.upper() in self.known_ciks
    
    def get_supported_tickers(self) -> List[str]:
        """Get list of supported ticker symbols"""
        return list(self.known_ciks.keys())


class DataFetcher:
    """
    SEC EDGAR Only Data Fetcher - Working Version
    
    Uses SEC EDGAR 'Revenues' concept for quarterly financial data
    """
    
    def __init__(self, event_bus: EventBus, api_keys: Dict[str, str]):
        self.event_bus = event_bus
        self.api_keys = api_keys
        
        # Initialize SEC EDGAR provider
        self.sec_edgar = SECEdgarProvider()
        
        # Subscribe to stock selection events
        self.event_bus.subscribe(EventType.STOCK_SELECTED, self.fetch_stock_data)
        
        print("🏛️ SEC EDGAR Working DataFetcher initialized")
        print(f"📊 Supported tickers: {len(self.sec_edgar.get_supported_tickers())}")
        print("✅ Using 'Revenues' concept for quarterly data")
    
    def fetch_stock_data(self, event):
        """Fetch stock data using working SEC EDGAR implementation"""
        ticker = event.data['ticker'].upper()
        
        print(f"\n🎯 Fetching SEC EDGAR data for {ticker}")
        print("=" * 50)
        
        # Check if ticker is supported
        if not self.sec_edgar.is_ticker_supported(ticker):
            print(f"❌ Ticker {ticker} not supported")
            print(f"💡 Supported tickers: {self.sec_edgar.get_supported_tickers()[:10]}...")
            self._emit_error(ticker, f"Ticker {ticker} not supported by SEC EDGAR fetcher")
            return
        
        # Emit fetch started
        self.event_bus.publish(Event(
            type=EventType.DATA_FETCH_STARTED,
            data={'ticker': ticker, 'message': f'Fetching SEC EDGAR data for {ticker}...'}
        ))
        
        # Get quarterly revenue data
        quarterly_data = self.sec_edgar.get_quarterly_financials(ticker)
        
        if quarterly_data and len(quarterly_data) >= 1:
            print(f"✅ SUCCESS: Retrieved {len(quarterly_data)} quarters from SEC EDGAR")
            
            # Create stock data object
            stock_data = StockData(
                ticker=ticker,
                company_name=f"{ticker} Corporation",
                current_price=0.0,  # SEC EDGAR doesn't have current prices
                market_cap=0.0,     # SEC EDGAR doesn't have market cap
                pe_ratio=None,      # SEC EDGAR doesn't have P/E ratios
                price_change=0.0,   # SEC EDGAR doesn't have price changes
                price_change_percent=0.0,
                quarterly_financials=quarterly_data
            )
            
            # Emit data received
            self.event_bus.publish(Event(
                type=EventType.DATA_RECEIVED,
                data={'stock_data': stock_data, 'data_source': 'SEC_EDGAR'}
            ))
            
            # Emit completion
            self.event_bus.publish(Event(
                type=EventType.DATA_FETCH_COMPLETED,
                data={'ticker': ticker, 'quarters_count': len(quarterly_data)}
            ))
            
        else:
            # No data found
            print(f"❌ No SEC EDGAR data available for {ticker}")
            self._emit_error(ticker, f"No quarterly revenue data found for {ticker}")
    
    def _emit_error(self, ticker: str, error_message: str):
        """Emit error events"""
        # Create empty stock data
        empty_stock_data = StockData(
            ticker=ticker,
            company_name=ticker,
            current_price=0.0,
            market_cap=0.0,
            pe_ratio=None,
            price_change=0.0,
            price_change_percent=0.0,
            quarterly_financials=[]
        )
        
        # Emit empty data
        self.event_bus.publish(Event(
            type=EventType.DATA_RECEIVED,
            data={'stock_data': empty_stock_data, 'data_source': 'SEC_EDGAR'}
        ))
        
        # Emit error
        self.event_bus.publish(Event(
            type=EventType.ERROR_OCCURRED,
            data={'error': error_message, 'ticker': ticker}
        ))
    
    def get_supported_tickers(self) -> List[str]:
        """Get list of tickers supported by this data fetcher"""
        return self.sec_edgar.get_supported_tickers()


if __name__ == "__main__":
    # Test the working SEC EDGAR data fetcher
    from core.event_system import EventBus
    
    event_bus = EventBus()
    fetcher = DataFetcher(event_bus, {})
    
    # Test with a known supported ticker
    test_ticker = "AAPL"
    print(f"🧪 Testing SEC EDGAR fetcher with {test_ticker}")
    
    event = Event(type=EventType.STOCK_SELECTED, data={'ticker': test_ticker})
    fetcher.fetch_stock_data(event)