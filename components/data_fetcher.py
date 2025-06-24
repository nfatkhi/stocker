# components/data_fetcher.py - Enhanced with SEC EDGAR shares outstanding data for FCF per share + DEBUG methods

import requests
import json
import time
import math
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from core.event_system import EventBus, Event, EventType
from components.cik_library import get_cik_library

# Try to import auto-updater
try:
    from components.auto_cik_updater import get_auto_updater
    AUTO_UPDATES_AVAILABLE = True
except ImportError:
    AUTO_UPDATES_AVAILABLE = False

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
    cash: float  # FCF data
    debt: float
    eps: float
    shares_outstanding: float = 0.0  # NEW: Shares outstanding for FCF per share

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

# Config fallbacks
try:
    from config import SEC_EDGAR_CONFIG, DATA_CONFIG, AUTO_UPDATE_CONFIG, API_KEYS
except ImportError:
    SEC_EDGAR_CONFIG = {
        'contact_email': 'nfatpro@gmail.com',
        'company_name': 'Stocker App',
        'rate_limit_delay': 0.1,
        'request_timeout': 15
    }
    DATA_CONFIG = {'quarters_to_fetch': 12}
    AUTO_UPDATE_CONFIG = {'enabled': True, 'auto_lookup_unknown_tickers': True}
    API_KEYS = {'polygon': ''}


class PolygonProvider:
    """Polygon.io provider for FCF data"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.polygon.io'
        self.last_request_time = 0
        self.rate_limit_delay = 12.0  # 5 calls per minute
        
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def get_quarterly_cash_flow(self, ticker: str, quarters: int = 12) -> Dict[str, float]:
        """Get quarterly FCF data from Polygon.io"""
        if not self.api_key:
            print(f"⚠️ Polygon API key not configured")
            return {}
        
        try:
            print(f"🔍 Fetching Polygon FCF data for {ticker}...")
            self._rate_limit()
            
            url = f"{self.base_url}/vX/reference/financials"
            params = {
                'ticker': ticker,
                'timeframe': 'quarterly',
                'limit': quarters,
                'sort': 'filing_date',
                'order': 'desc',
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            print(f"   Polygon response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   Polygon error: {response.text}")
                return {}
            
            data = response.json()
            results = data.get('results', [])
            print(f"   Polygon results: {len(results)} quarters")
            
            fcf_by_date = {}
            
            for result in results:
                end_date = result.get('end_date', '')
                financials = result.get('financials', {})
                cash_flow = financials.get('cash_flow_statement', {})
                
                # Get operating cash flow
                operating_cf = 0
                for field in ['net_cash_flow_from_operating_activities', 'operating_cash_flow']:
                    if field in cash_flow and cash_flow[field].get('value'):
                        operating_cf = cash_flow[field]['value']
                        break
                
                # Get capex
                capex = 0
                for field in ['net_cash_flow_from_investing_activities', 'capital_expenditures']:
                    if field in cash_flow and cash_flow[field].get('value'):
                        capex_raw = cash_flow[field]['value']
                        capex = abs(capex_raw) if capex_raw < 0 else capex_raw
                        break
                
                # Calculate FCF
                if operating_cf != 0:
                    fcf = operating_cf - capex
                    if end_date:
                        fcf_by_date[end_date] = float(fcf)
                        print(f"   {end_date}: ${fcf/1e6:.1f}M FCF")
            
            print(f"   Final FCF data: {len(fcf_by_date)} quarters")
            return fcf_by_date
            
        except Exception as e:
            print(f"❌ Polygon FCF fetch error: {e}")
            return {}


class SECEdgarProvider:
    """Enhanced SEC EDGAR provider for revenue and shares outstanding data"""
    
    def __init__(self, event_bus: EventBus = None):
        self.headers = {
            'User-Agent': f"{SEC_EDGAR_CONFIG['company_name']} {SEC_EDGAR_CONFIG['contact_email']}",
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov',
            'Accept': 'application/json'
        }
        self.base_url = 'https://data.sec.gov/api/xbrl'
        self.last_request_time = 0
        self.rate_limit_delay = SEC_EDGAR_CONFIG['rate_limit_delay']
        
        # Initialize components
        self.cik_library = get_cik_library()
        self.auto_updater = None
        if AUTO_UPDATES_AVAILABLE and AUTO_UPDATE_CONFIG.get('enabled', True):
            self.auto_updater = get_auto_updater(event_bus)
    
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def get_comprehensive_financials(self, ticker: str) -> Tuple[List[QuarterlyFinancials], Dict[str, Any]]:
        """Get comprehensive financial data including revenue and shares outstanding"""
        print(f"🔍 Fetching SEC EDGAR data for {ticker}...")
        
        cik = self.cik_library.get_cik(ticker)
        print(f"   CIK from library: {cik}")
        
        # Auto-lookup if needed
        if not cik and self.auto_updater and AUTO_UPDATE_CONFIG.get('auto_lookup_unknown_tickers', True):
            print(f"   Attempting auto-lookup...")
            result = self.auto_updater.lookup_ticker_realtime(ticker)
            if result:
                cik, company_name = result
                print(f"   Auto-lookup success: CIK={cik}, Company={company_name}")
            else:
                print(f"   Auto-lookup failed")
        
        if not cik:
            print(f"❌ No CIK found for {ticker}")
            return [], {'error': 'CIK not found'}
        
        # Get comprehensive company facts (revenue + shares outstanding)
        company_facts = self._get_company_facts(cik, ticker)
        if not company_facts:
            print(f"❌ No company facts data for {ticker}")
            return [], {'error': 'No company facts data'}
        
        # Extract revenue data
        revenue_data = self._extract_revenue_data(company_facts)
        print(f"   Revenue data: {len(revenue_data)} quarters")
        
        # Extract shares outstanding data
        shares_data = self._extract_shares_outstanding_data(company_facts)
        print(f"   Shares data: {len(shares_data)} quarters")
        
        # Combine revenue and shares data
        combined_data = self._combine_financial_data(revenue_data, shares_data)
        print(f"   Combined data: {len(combined_data)} quarters")
        
        metadata = {
            'revenue_quarters': len(revenue_data),
            'shares_quarters': len(shares_data),
            'combined_quarters': len(combined_data),
            'data_source': 'SEC_EDGAR_comprehensive'
        }
        
        return combined_data, metadata
    
    def _get_company_facts(self, cik: str, ticker: str) -> Optional[Dict]:
        """Get all company facts from SEC EDGAR companyfacts API"""
        self._rate_limit()
        
        url = f"{self.base_url}/companyfacts/CIK{cik}.json"
        print(f"   SEC EDGAR URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=SEC_EDGAR_CONFIG['request_timeout'])
            print(f"   SEC response status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"   SEC error: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"❌ Error fetching company facts for {ticker}: {e}")
            return None
    
    def _extract_revenue_data(self, company_facts: Dict) -> List[Dict]:
        """Extract revenue data from company facts"""
        try:
            facts = company_facts.get('facts', {})
            us_gaap = facts.get('us-gaap', {})
            revenue_concept = us_gaap.get('Revenues', {})
            
            if not revenue_concept:
                print(f"   No 'Revenues' concept found")
                return []
            
            revenue_units = revenue_concept.get('units', {}).get('USD', [])
            print(f"   Revenue units found: {len(revenue_units)}")
            
            # Filter for quarterly filings only
            quarterly_records = [
                record for record in revenue_units 
                if record.get('form') == '10-Q' and record.get('val', 0) > 0
            ]
            print(f"   Quarterly revenue records: {len(quarterly_records)}")
            
            # Group by end date to handle duplicates
            quarters_by_date = {}
            for record in quarterly_records:
                end_date = record.get('end', '')
                if end_date:
                    if end_date not in quarters_by_date:
                        quarters_by_date[end_date] = []
                    quarters_by_date[end_date].append(record)
            
            # Deduplicate (select larger revenue for most recent data, not smaller)
            deduplicated_records = []
            for end_date, records in quarters_by_date.items():
                # Select the record with the largest revenue (most recent/complete)
                selected_record = max(records, key=lambda x: x.get('val', 0))
                deduplicated_records.append(selected_record)
            
            # Sort by date and take target quarters (most recent first)
            deduplicated_records.sort(key=lambda x: x.get('end', ''), reverse=True)
            target_quarters = DATA_CONFIG.get('quarters_to_fetch', 12)
            
            final_records = deduplicated_records[:target_quarters]
            print(f"   Final revenue records: {len(final_records)}")
            
            # Debug: Show date range
            if final_records:
                latest = final_records[0].get('end', 'Unknown')
                oldest = final_records[-1].get('end', 'Unknown')
                print(f"   Revenue date range: {oldest} to {latest}")
            
            return final_records
            
        except Exception as e:
            print(f"❌ Error extracting revenue data: {e}")
            return []
    
    def _extract_shares_outstanding_data(self, company_facts: Dict) -> List[Dict]:
        """Extract shares outstanding data from company facts"""
        try:
            facts = company_facts.get('facts', {})
            dei = facts.get('dei', {})
            shares_concept = dei.get('EntityCommonStockSharesOutstanding', {})
            
            if not shares_concept:
                # Try alternative field names
                alt_fields = [
                    'CommonStockSharesOutstanding',
                    'WeightedAverageNumberOfSharesOutstandingBasic',
                    'CommonSharesOutstanding'
                ]
                
                us_gaap = facts.get('us-gaap', {})
                for field in alt_fields:
                    if field in us_gaap:
                        shares_concept = us_gaap[field]
                        print(f"   Found shares in us-gaap.{field}")
                        break
            
            if not shares_concept:
                print(f"   No shares outstanding concept found")
                return []
            
            shares_units = shares_concept.get('units', {}).get('shares', [])
            print(f"   Shares units found: {len(shares_units)}")
            
            # Filter for quarterly and annual filings
            quarterly_records = [
                record for record in shares_units 
                if record.get('form') in ['10-Q', '10-K'] and record.get('val', 0) > 0
            ]
            
            # Sort by date (newest first)
            quarterly_records.sort(key=lambda x: x.get('end', ''), reverse=True)
            target_quarters = DATA_CONFIG.get('quarters_to_fetch', 12)
            
            final_records = quarterly_records[:target_quarters]
            print(f"   Final shares records: {len(final_records)}")
            
            return final_records
            
        except Exception as e:
            print(f"❌ Error extracting shares data: {e}")
            return []
    
    def _combine_financial_data(self, revenue_data: List[Dict], shares_data: List[Dict]) -> List[QuarterlyFinancials]:
        """Combine revenue and shares data into QuarterlyFinancials objects"""
        combined_data = []
        
        # Create lookup for shares data by date
        shares_by_date = {}
        for shares_record in shares_data:
            end_date = shares_record.get('end', '')
            if end_date:
                shares_by_date[end_date] = shares_record.get('val', 0)
        
        print(f"   Shares lookup table: {len(shares_by_date)} entries")
        
        # Create financial objects from revenue data, matching with shares data
        for revenue_record in revenue_data:
            end_date = revenue_record.get('end', '')
            revenue = revenue_record.get('val', 0)
            
            # Find matching shares outstanding (exact date match first, then closest)
            shares_outstanding = 0
            if end_date in shares_by_date:
                shares_outstanding = shares_by_date[end_date]
            else:
                # Find closest date within reasonable range (±90 days)
                closest_shares = self._find_closest_shares_data(end_date, shares_by_date)
                if closest_shares:
                    shares_outstanding = closest_shares
            
            quarterly_financial = QuarterlyFinancials(
                date=end_date,
                revenue=float(revenue),
                net_income=0.0,
                gross_profit=0.0,
                operating_income=0.0,
                assets=0.0,
                liabilities=0.0,
                cash=0.0,  # FCF will come from Polygon
                debt=0.0,
                eps=0.0,
                shares_outstanding=float(shares_outstanding)
            )
            combined_data.append(quarterly_financial)
            
            print(f"   {end_date}: Revenue=${revenue/1e6:.1f}M, Shares={shares_outstanding/1e6:.1f}M")
        
        return combined_data
    
    def _find_closest_shares_data(self, target_date: str, shares_by_date: Dict[str, float]) -> Optional[float]:
        """Find closest shares outstanding data within reasonable time range"""
        try:
            from datetime import datetime, timedelta
            
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            closest_date = None
            min_diff = timedelta(days=365)  # Max 1 year difference
            
            for date_str in shares_by_date.keys():
                try:
                    date_dt = datetime.strptime(date_str, '%Y-%m-%d')
                    diff = abs(target_dt - date_dt)
                    
                    if diff < min_diff and diff <= timedelta(days=90):  # Within 90 days
                        min_diff = diff
                        closest_date = date_str
                except:
                    continue
            
            return shares_by_date.get(closest_date) if closest_date else None
            
        except Exception:
            return None
    
    def get_supported_tickers(self) -> List[str]:
        """Get list of supported ticker symbols"""
        return self.cik_library.get_supported_tickers()
    
    def is_ticker_supported(self, ticker: str) -> bool:
        """Check if ticker is supported"""
        if self.cik_library.is_ticker_supported(ticker):
            return True
        if self.auto_updater and AUTO_UPDATE_CONFIG.get('auto_lookup_unknown_tickers', True):
            return True
        return False


class DataFetcher:
    """Enhanced data fetcher: Polygon.io FCF + SEC EDGAR Revenue & Shares Outstanding"""
    
    def __init__(self, event_bus: EventBus, api_keys: Dict[str, str]):
        self.event_bus = event_bus
        self.api_keys = api_keys
        
        # Initialize providers
        polygon_api_key = api_keys.get('polygon', '')
        self.polygon_provider = PolygonProvider(polygon_api_key) if polygon_api_key else None
        self.sec_edgar = SECEdgarProvider(event_bus)
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.STOCK_SELECTED, self.fetch_stock_data)
        
        print(f"📊 DataFetcher: Polygon.io FCF + SEC EDGAR Revenue & Shares Outstanding")
    
    def debug_cprt_fetch(self, ticker="CPRT"):
        """Debug CPRT specific data fetching issues"""
        print(f"\n🔍 DEBUGGING {ticker} DATA FETCH")
        print("=" * 50)
        
        # 1. Check API configuration
        print(f"1. API Configuration:")
        print(f"   Polygon API key configured: {bool(self.api_keys.get('polygon'))}")
        print(f"   Polygon provider available: {self.polygon_provider is not None}")
        if self.polygon_provider:
            print(f"   Polygon API key length: {len(self.api_keys.get('polygon', ''))}")
        
        # 2. Check CIK lookup
        print(f"\n2. CIK Lookup:")
        cik = self.sec_edgar.cik_library.get_cik(ticker)
        print(f"   CIK found in library: {cik}")
        
        if not cik and self.sec_edgar.auto_updater:
            print(f"   Attempting auto-lookup...")
            try:
                result = self.sec_edgar.auto_updater.lookup_ticker_realtime(ticker)
                if result:
                    auto_cik, company_name = result
                    print(f"   Auto-lookup result: CIK={auto_cik}, Company={company_name}")
                else:
                    print(f"   Auto-lookup failed: No result")
            except Exception as e:
                print(f"   Auto-lookup error: {e}")
        
        # 3. Test SEC EDGAR fetch
        print(f"\n3. SEC EDGAR Test:")
        try:
            comprehensive_data, sec_metadata = self.sec_edgar.get_comprehensive_financials(ticker)
            print(f"   SEC data quarters: {len(comprehensive_data)}")
            print(f"   SEC metadata: {sec_metadata}")
            
            if comprehensive_data:
                sample = comprehensive_data[0]
                print(f"   Sample quarter: {sample.date}")
                print(f"   Sample revenue: ${sample.revenue/1e6:.1f}M")
                print(f"   Sample FCF (before Polygon): ${sample.cash/1e6:.1f}M")
        except Exception as e:
            print(f"   SEC EDGAR error: {e}")
            comprehensive_data = []
        
        # 4. Test Polygon.io fetch
        print(f"\n4. Polygon.io FCF Test:")
        if self.polygon_provider:
            try:
                fcf_dict = self.polygon_provider.get_quarterly_cash_flow(ticker)
                print(f"   Polygon FCF quarters: {len(fcf_dict)}")
                if fcf_dict:
                    for date, fcf in list(fcf_dict.items())[:3]:  # Show first 3
                        print(f"   {date}: ${fcf/1e6:.1f}M")
                else:
                    print(f"   No FCF data from Polygon")
            except Exception as e:
                print(f"   Polygon error: {e}")
                fcf_dict = {}
        else:
            print(f"   Polygon provider not configured")
            fcf_dict = {}
        
        # 5. Test data merging
        print(f"\n5. Data Merging Test:")
        if comprehensive_data and fcf_dict:
            print(f"   Before merge - FCF quarters: {len([f for f in comprehensive_data if f.cash != 0])}")
            merged_data = self._merge_fcf_with_comprehensive_data(comprehensive_data, fcf_dict)
            print(f"   After merge - FCF quarters: {len([f for f in merged_data if f.cash != 0])}")
            
            # Show merge results
            for financial in merged_data[:3]:  # Show first 3
                print(f"   {financial.date}: Revenue=${financial.revenue/1e6:.1f}M, FCF=${financial.cash/1e6:.1f}M")
        else:
            print(f"   Cannot test merging - missing data")
        
        # 6. Determine why using combined approach
        print(f"\n6. Approach Selection:")
        if comprehensive_data:
            has_fcf_data = any(f.cash != 0 for f in comprehensive_data)
            has_revenue_data = any(f.revenue != 0 for f in comprehensive_data)
            print(f"   Has comprehensive data: True")
            print(f"   Has FCF after merge: {has_fcf_data}")
            print(f"   Has revenue data: {has_revenue_data}")
            print(f"   Should use 'comprehensive' approach: True")
        else:
            print(f"   Has comprehensive data: False")
            print(f"   Will fallback to 'combined' approach")
        
        print(f"\n🎯 DIAGNOSIS:")
        if not comprehensive_data:
            print(f"   Issue: SEC EDGAR data fetch failing")
            print(f"   Solution: Check CIK lookup and SEC API access")
        elif not fcf_dict:
            print(f"   Issue: Polygon.io FCF data not available")
            print(f"   Solution: Check Polygon API key and CPRT availability")
        else:
            print(f"   Data should be working - check event emission logic")

    def test_polygon_api_direct(self, ticker="CPRT"):
        """Test Polygon API directly"""
        if not self.polygon_provider:
            print("❌ Polygon provider not configured")
            return
        
        import requests
        
        url = f"{self.polygon_provider.base_url}/vX/reference/financials"
        params = {
            'ticker': ticker,
            'timeframe': 'quarterly',
            'limit': 4,
            'sort': 'filing_date',
            'order': 'desc',
            'apikey': self.api_keys.get('polygon', '')
        }
        
        print(f"\n🌐 DIRECT POLYGON API TEST for {ticker}")
        print(f"URL: {url}")
        print(f"Params: {params}")
        
        try:
            response = requests.get(url, params=params, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"Results count: {len(results)}")
                
                for i, result in enumerate(results[:2]):  # Show first 2
                    end_date = result.get('end_date', 'No date')
                    financials = result.get('financials', {})
                    cash_flow = financials.get('cash_flow_statement', {})
                    print(f"  Result {i+1}: {end_date}")
                    print(f"    Cash flow keys: {list(cash_flow.keys())}")
            else:
                print(f"Error response: {response.text}")
                
        except Exception as e:
            print(f"Request error: {e}")

    def fetch_stock_data(self, event):
        """Fetch separated data: FCF from Polygon.io, Revenue from SEC EDGAR - NO MERGING"""
        ticker = event.data['ticker'].upper()
        
        print(f"\n🔄 FETCHING SEPARATED DATA for {ticker}")
        print("=" * 50)
        
        # Emit fetch started
        self.event_bus.publish(Event(
            type=EventType.DATA_FETCH_STARTED,
            data={'ticker': ticker, 'message': f'Fetching separated data for {ticker}...'}
        ))
        
        # Initialize separate data containers
        revenue_data = []
        fcf_data = []
        errors = []
        
        # Fetch revenue data from SEC EDGAR
        try:
            sec_revenue_data, sec_metadata = self.sec_edgar.get_comprehensive_financials(ticker)
            if sec_revenue_data:
                revenue_data = sec_revenue_data  # Keep as QuarterlyFinancials for consistency
                print(f"✅ SEC EDGAR revenue data: {len(revenue_data)} quarters")
            else:
                errors.append(f"No SEC EDGAR data: {sec_metadata.get('error', 'Unknown error')}")
                print(f"❌ No SEC EDGAR data for {ticker}")
        except Exception as e:
            errors.append(f"SEC EDGAR fetch error: {str(e)}")
            print(f"❌ SEC EDGAR fetch error: {e}")
        
        # Fetch FCF data from Polygon.io
        if self.polygon_provider:
            try:
                fcf_dict = self.polygon_provider.get_quarterly_cash_flow(ticker)
                if fcf_dict:
                    # Convert FCF dict to QuarterlyFinancials for consistency
                    for date, fcf_value in fcf_dict.items():
                        fcf_quarter = QuarterlyFinancials(
                            date=date,
                            revenue=0.0,
                            net_income=0.0,
                            gross_profit=0.0,
                            operating_income=0.0,
                            assets=0.0,
                            liabilities=0.0,
                            cash=fcf_value,
                            debt=0.0,
                            eps=0.0,
                            shares_outstanding=0.0
                        )
                        fcf_data.append(fcf_quarter)
                    
                    # Sort FCF data by date (newest first)
                    fcf_data.sort(key=lambda x: x.date, reverse=True)
                    print(f"✅ Polygon.io FCF data: {len(fcf_data)} quarters")
                else:
                    errors.append("No FCF data from Polygon.io")
                    print(f"⚠️ No FCF data from Polygon.io for {ticker}")
            except Exception as e:
                errors.append(f"FCF fetch error: {str(e)}")
                print(f"❌ FCF fetch error: {e}")
        else:
            errors.append("Polygon.io not configured")
            print(f"⚠️ Polygon.io not configured")
        
        # Create result - NO MERGING, just send separated data
        if revenue_data or fcf_data:
            print(f"✅ Creating separated result for {ticker}")
            
            # Get company name
            try:
                company_info = self.sec_edgar.cik_library.get_company_info(ticker)
                company_name = company_info.company_name if company_info else f"{ticker} Corporation"
            except:
                company_name = f"{ticker} Corporation"
            
            # Create minimal stock_data (not really used in separated approach)
            stock_data = StockData(
                ticker=ticker,
                company_name=company_name,
                current_price=0.0,
                market_cap=0.0,
                pe_ratio=None,
                price_change=0.0,
                price_change_percent=0.0,
                quarterly_financials=[]  # Empty - not used in separated approach
            )
            
            print(f"📊 Final separated data: FCF={len(fcf_data)}q, Revenue={len(revenue_data)}q")
            
            # Emit success with separated data
            self.event_bus.publish(Event(
                type=EventType.DATA_RECEIVED,
                data={
                    'stock_data': stock_data,
                    'approach': 'separated',
                    'fcf_data': fcf_data,  # Direct FCF data from Polygon
                    'revenue_data': revenue_data,  # Direct revenue data from SEC
                    'fcf_available': len(fcf_data) > 0,
                    'revenue_available': len(revenue_data) > 0,
                    'fcf_source': 'Polygon.io',
                    'revenue_source': 'SEC_EDGAR',
                    'errors': errors
                }
            ))
            
            print(f"✅ {ticker}: Separated data sent - FCF={len(fcf_data)}q, Revenue={len(revenue_data)}q")
        else:
            # Complete failure
            print(f"❌ Complete failure for {ticker} - No data from either source")
            self._emit_error(ticker, "No data available from either source", errors)
    
    def _emit_error(self, ticker: str, error_message: str, detailed_errors: List[str]):
        """Emit error events"""
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
        
        self.event_bus.publish(Event(
            type=EventType.DATA_RECEIVED,
            data={
                'stock_data': empty_stock_data,
                'approach': 'separated',
                'fcf_data': [],
                'revenue_data': [],
                'shares_data': [],
                'fcf_per_share_data': [],
                'fcf_available': False,
                'revenue_available': False,
                'shares_available': False,
                'errors': detailed_errors
            }
        ))
        
        print(f"❌ {ticker}: {error_message}")
    
    def _merge_fcf_with_comprehensive_data(self, comprehensive_data: List[QuarterlyFinancials], fcf_dict: Dict[str, float]) -> List[QuarterlyFinancials]:
        """Merge Polygon FCF data into SEC comprehensive data"""
        print(f"🔧 Merging FCF data: {len(fcf_dict)} FCF quarters into {len(comprehensive_data)} comprehensive quarters")
        
        # Create a copy to avoid modifying original
        updated_data = []
        
        for financial in comprehensive_data:
            # Create a copy of the financial object
            updated_financial = QuarterlyFinancials(
                date=financial.date,
                revenue=financial.revenue,
                net_income=financial.net_income,
                gross_profit=financial.gross_profit,
                operating_income=financial.operating_income,
                assets=financial.assets,
                liabilities=financial.liabilities,
                cash=financial.cash,
                debt=financial.debt,
                eps=financial.eps,
                shares_outstanding=financial.shares_outstanding
            )
                # Add this debug method to your DataFetcher class in data_fetcher.py

def debug_cprt_fetch(self, ticker="CPRT"):
    """Debug CPRT specific data fetching issues"""
    print(f"\n🔍 DEBUGGING {ticker} DATA FETCH")
    print("=" * 50)
    
    # 1. Check API configuration
    print(f"1. API Configuration:")
    print(f"   Polygon API key configured: {bool(self.api_keys.get('polygon'))}")
    print(f"   Polygon provider available: {self.polygon_provider is not None}")
    if self.polygon_provider:
        print(f"   Polygon API key length: {len(self.api_keys.get('polygon', ''))}")
    
    # 2. Check CIK lookup
    print(f"\n2. CIK Lookup:")
    cik = self.sec_edgar.cik_library.get_cik(ticker)
    print(f"   CIK found in library: {cik}")
    
    if not cik and self.sec_edgar.auto_updater:
        print(f"   Attempting auto-lookup...")
        try:
            result = self.sec_edgar.auto_updater.lookup_ticker_realtime(ticker)
            if result:
                auto_cik, company_name = result
                print(f"   Auto-lookup result: CIK={auto_cik}, Company={company_name}")
            else:
                print(f"   Auto-lookup failed: No result")
        except Exception as e:
            print(f"   Auto-lookup error: {e}")
    
    # 3. Test SEC EDGAR fetch
    print(f"\n3. SEC EDGAR Test:")
    try:
        comprehensive_data, sec_metadata = self.sec_edgar.get_comprehensive_financials(ticker)
        print(f"   SEC data quarters: {len(comprehensive_data)}")
        print(f"   SEC metadata: {sec_metadata}")
        
        if comprehensive_data:
            sample = comprehensive_data[0]
            print(f"   Sample quarter: {sample.date}")
            print(f"   Sample revenue: ${sample.revenue/1e6:.1f}M")
            print(f"   Sample FCF (before Polygon): ${sample.cash/1e6:.1f}M")
    except Exception as e:
        print(f"   SEC EDGAR error: {e}")
        comprehensive_data = []
    
    # 4. Test Polygon.io fetch
    print(f"\n4. Polygon.io FCF Test:")
    if self.polygon_provider:
        try:
            fcf_dict = self.polygon_provider.get_quarterly_cash_flow(ticker)
            print(f"   Polygon FCF quarters: {len(fcf_dict)}")
            if fcf_dict:
                for date, fcf in list(fcf_dict.items())[:3]:  # Show first 3
                    print(f"   {date}: ${fcf/1e6:.1f}M")
            else:
                print(f"   No FCF data from Polygon")
        except Exception as e:
            print(f"   Polygon error: {e}")
            fcf_dict = {}
    else:
        print(f"   Polygon provider not configured")
        fcf_dict = {}
    
    # 5. Test data merging
    print(f"\n5. Data Merging Test:")
    if comprehensive_data and fcf_dict:
        print(f"   Before merge - FCF quarters: {len([f for f in comprehensive_data if f.cash != 0])}")
        merged_data = self._merge_fcf_with_comprehensive_data(comprehensive_data, fcf_dict)
        print(f"   After merge - FCF quarters: {len([f for f in merged_data if f.cash != 0])}")
        
        # Show merge results
        for financial in merged_data[:3]:  # Show first 3
            print(f"   {financial.date}: Revenue=${financial.revenue/1e6:.1f}M, FCF=${financial.cash/1e6:.1f}M")
    else:
        print(f"   Cannot test merging - missing data")
    
    # 6. Determine why using combined approach
    print(f"\n6. Approach Selection:")
    if comprehensive_data:
        has_fcf_data = any(f.cash != 0 for f in comprehensive_data)
        has_revenue_data = any(f.revenue != 0 for f in comprehensive_data)
        print(f"   Has comprehensive data: True")
        print(f"   Has FCF after merge: {has_fcf_data}")
        print(f"   Has revenue data: {has_revenue_data}")
        print(f"   Should use 'comprehensive' approach: True")
    else:
        print(f"   Has comprehensive data: False")
        print(f"   Will fallback to 'combined' approach")
    
    print(f"\n🎯 DIAGNOSIS:")
    if not comprehensive_data:
        print(f"   Issue: SEC EDGAR data fetch failing")
        print(f"   Solution: Check CIK lookup and SEC API access")
    elif not fcf_dict:
        print(f"   Issue: Polygon.io FCF data not available")
        print(f"   Solution: Check Polygon API key and CPRT availability")
    else:
        print(f"   Data should be working - check event emission logic")

# Also add this method to test a specific API call
def test_polygon_api_direct(self, ticker="CPRT"):
    """Test Polygon API directly"""
    if not self.polygon_provider:
        print("❌ Polygon provider not configured")
        return
    
    import requests
    
    url = f"{self.polygon_provider.base_url}/vX/reference/financials"
    params = {
        'ticker': ticker,
        'timeframe': 'quarterly',
        'limit': 4,
        'sort': 'filing_date',
        'order': 'desc',
        'apikey': self.api_keys.get('polygon', '')
    }
    
    print(f"\n🌐 DIRECT POLYGON API TEST for {ticker}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"Results count: {len(results)}")
            
            for i, result in enumerate(results[:2]):  # Show first 2
                end_date = result.get('end_date', 'No date')
                financials = result.get('financials', {})
                cash_flow = financials.get('cash_flow_statement', {})
                print(f"  Result {i+1}: {end_date}")
                print(f"    Cash flow keys: {list(cash_flow.keys())}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request error: {e}")

# Usage: Add these methods to your DataFetcher class, then call:
# data_fetcher.debug_cprt_fetch("CPRT")
# data_fetcher.test_polygon_api_direct("CPRT")