# core/app.py - Updated for new cache system integration

import tkinter as tk
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from core.event_system import EventBus, Event, EventType
from ui.main_window import MainWindow
from components.cache_manager import CacheManager  # REMOVED: start_background_cache_check
from components.analyzer import Analyzer
from components.news_manager import NewsManager  
from components.metrics_display import MetricsDisplay

# Import the chart manager
try:
    from components.chart_manager import EnhancedChartManager, DirectCacheChartManager
    CHART_MANAGER_AVAILABLE = True
    print("✓ Using Enhanced Chart Manager with cache support")
except ImportError:
    CHART_MANAGER_AVAILABLE = False
    print("⚠️ Chart manager not available")

try:
    from config import APP_CONFIG, EDGARTOOLS_CONFIG
except ImportError:
    APP_CONFIG = {'name': 'Stocker App', 'version': '2.0.0'}
    EDGARTOOLS_CONFIG = {'user_identity': 'nfatpro@gmail.com'}


@dataclass
class QuarterlyFinancials:
    """Simple financial data structure for compatibility"""
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


@dataclass
class StockData:
    """Stock data structure for compatibility"""
    ticker: str
    company_name: str
    current_price: float
    market_cap: float
    pe_ratio: Optional[float]
    price_change: float
    price_change_percent: float
    quarterly_financials: List[QuarterlyFinancials]


class CacheDataOrchestrator:
    """Orchestrates cache system with event-driven architecture"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.cache_manager = CacheManager()
        
        # Subscribe to stock selection events
        self.event_bus.subscribe(EventType.STOCK_SELECTED, self.handle_stock_selected)
        
        print("📊 Cache Data Orchestrator initialized")
        print("   🔗 Connected to event system")
        print("   📁 Cache manager ready")
    
    def handle_stock_selected(self, event):
        """Handle stock selection events by loading from cache"""
        ticker = event.data.get('ticker', '').upper()
        
        if not ticker:
            print("⚠️ No ticker provided in stock selection event")
            return
        
        print(f"\n🔄 Processing stock selection: {ticker}")
        
        # Emit loading started
        self.event_bus.publish(Event(
            type=EventType.LOADING_STARTED,
            data={'ticker': ticker, 'message': f'Loading data for {ticker}...'},
            source='cache_orchestrator'
        ))
        
        try:
            # Get data from cache manager
            quarterly_data, metadata = self.cache_manager.get_ticker_data(ticker)
            
            if not quarterly_data:
                # Emit error if no data
                error_msg = metadata.get('error', f'No data available for {ticker}')
                self.event_bus.publish(Event(
                    type=EventType.ERROR_OCCURRED,
                    data={'ticker': ticker, 'message': error_msg},
                    source='cache_orchestrator'
                ))
                return
            
            # Convert raw cache data to expected format
            processed_data = self._convert_cache_data_to_financials(quarterly_data, metadata)
            
            if processed_data:
                # Emit successful data received
                self._emit_data_received(ticker, processed_data, metadata)
            else:
                # Emit error if conversion failed
                self.event_bus.publish(Event(
                    type=EventType.ERROR_OCCURRED,
                    data={'ticker': ticker, 'message': 'Failed to process cached data'},
                    source='cache_orchestrator'
                ))
            
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            self.event_bus.publish(Event(
                type=EventType.ERROR_OCCURRED,
                data={'ticker': ticker, 'message': f'Error loading data: {str(e)}'},
                source='cache_orchestrator'
            ))
        finally:
            # Emit loading completed
            self.event_bus.publish(Event(
                type=EventType.LOADING_COMPLETED,
                data={'ticker': ticker},
                source='cache_orchestrator'
            ))
    
    def _convert_cache_data_to_financials(self, quarterly_data: List[Dict], metadata: Dict) -> Optional[StockData]:
        """Convert raw cache data to QuarterlyFinancials format"""
        try:
            quarterly_financials = []
            
            for quarter_data in quarterly_data:
                # Extract financial metrics from raw XBRL data
                revenue, cash_flow, net_income, assets = self._extract_financial_metrics(quarter_data)
                
                # Create QuarterlyFinancials object
                quarter_financials = QuarterlyFinancials(
                    date=quarter_data.get('filing_date', ''),
                    revenue=revenue,
                    net_income=net_income,
                    gross_profit=0.0,  # Can be extracted if needed
                    operating_income=0.0,  # Can be extracted if needed
                    assets=assets,
                    liabilities=0.0,  # Can be extracted if needed
                    cash=cash_flow,  # Using operating cash flow as FCF approximation
                    debt=0.0,  # Can be extracted if needed
                    eps=0.0,  # Can be calculated if needed
                    shares_outstanding=0.0
                )
                
                quarterly_financials.append(quarter_financials)
            
            # Create StockData object
            stock_data = StockData(
                ticker=metadata.get('ticker', ''),
                company_name=metadata.get('company_name', ''),
                current_price=0.0,  # Not available from XBRL data
                market_cap=0.0,  # Not available from XBRL data
                pe_ratio=None,  # Not available from XBRL data
                price_change=0.0,  # Not available from XBRL data
                price_change_percent=0.0,  # Not available from XBRL data
                quarterly_financials=quarterly_financials
            )
            
            print(f"   ✅ Converted {len(quarterly_financials)} quarters for {stock_data.ticker}")
            return stock_data
            
        except Exception as e:
            print(f"   ❌ Error converting cache data: {e}")
            return None
    
    def _extract_financial_metrics(self, quarter_data: Dict) -> Tuple[float, float, float, float]:
        """Extract key financial metrics from raw XBRL quarter data"""
        try:
            # Load facts JSON if available
            facts_json = quarter_data.get('facts_json')
            if facts_json:
                import pandas as pd
                import json
                
                facts_df = pd.read_json(facts_json)
                
                # Extract revenue
                revenue = self._extract_concept_from_facts(facts_df, [
                    'Revenues', 'Revenue', 'SalesRevenueNet', 'PropertyIncome', 'RentalIncome'
                ])
                
                # Extract operating cash flow
                cash_flow = self._extract_concept_from_facts(facts_df, [
                    'NetCashProvidedByUsedInOperatingActivities',
                    'NetCashProvidedByOperatingActivities',
                    'CashFlowFromOperatingActivities'
                ])
                
                # Extract net income
                net_income = self._extract_concept_from_facts(facts_df, [
                    'NetIncomeLoss', 'NetIncome', 'ProfitLoss'
                ])
                
                # Extract total assets
                assets = self._extract_concept_from_facts(facts_df, [
                    'Assets', 'TotalAssets'
                ])
                
                return (
                    float(revenue or 0),
                    float(cash_flow or 0), 
                    float(net_income or 0),
                    float(assets or 0)
                )
            
            # Fallback: return zeros if no facts data
            return (0.0, 0.0, 0.0, 0.0)
            
        except Exception as e:
            print(f"   ⚠️ Error extracting financial metrics: {e}")
            return (0.0, 0.0, 0.0, 0.0)
    
    def _extract_concept_from_facts(self, facts_df, concept_names: List[str]) -> Optional[float]:
        """Extract financial concept value from facts DataFrame"""
        try:
            for concept in concept_names:
                # Look for concept in DataFrame (case insensitive)
                concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
                
                if len(concept_rows) > 0:
                    # Try different value columns
                    for value_col in ['numeric_value', 'value', 'amount']:
                        if value_col in concept_rows.columns:
                            value = concept_rows.iloc[-1][value_col]  # Get most recent
                            if value is not None and str(value).replace('.', '').replace('-', '').isdigit():
                                return float(value)
            
            return None
            
        except Exception as e:
            return None
    
    def _emit_data_received(self, ticker: str, stock_data: StockData, metadata: Dict):
        """Emit data received event in expected format"""
        # Separate revenue and FCF data for chart compatibility
        revenue_data = [q for q in stock_data.quarterly_financials if q.revenue > 0]
        fcf_data = [q for q in stock_data.quarterly_financials if q.cash != 0]
        
        # Create enhanced metadata
        enhanced_metadata = {
            **metadata,
            'data_source': 'Cache System (XBRL)',
            'cache_hit': True,
            'quarters_found': len(stock_data.quarterly_financials),
            'extraction_method': 'cache_xbrl_conversion'
        }
        
        # Emit data received event
        self.event_bus.publish(Event(
            type=EventType.DATA_RECEIVED,
            data={
                'stock_data': stock_data,
                'approach': 'cache_system',
                'fcf_data': fcf_data,
                'revenue_data': revenue_data,
                'fcf_available': len(fcf_data) > 0,
                'revenue_available': len(revenue_data) > 0,
                'fcf_source': 'Cache System (XBRL)',
                'revenue_source': 'Cache System (XBRL)',
                'metadata': enhanced_metadata,
                'errors': []
            },
            source='cache_orchestrator'
        ))
        
        print(f"   📡 Data received event emitted for {ticker}")
        print(f"      Revenue quarters: {len(revenue_data)}")
        print(f"      FCF quarters: {len(fcf_data)}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return self.cache_manager.get_cache_stats()


class StockerApp:
    """Main application class with new cache system"""
    
    def __init__(self, root: tk.Tk):
        """Initialize the application with cache system"""
        self.root = root
        self.event_bus = EventBus()
        
        # Print system status
        print(f"🚀 Stocker App v{APP_CONFIG.get('version', '2.0')} - Cache System Edition")
        print(f"📊 Raw XBRL cache with EdgarTools integration")
        print(f"📧 SEC Contact: {EDGARTOOLS_CONFIG.get('user_identity')}")
        
        # Initialize UI first
        self.main_window = MainWindow(self.root, self.event_bus)
        
        # Initialize components
        print(f"\n🔧 Initializing components...")
        
        # NEW: Cache data orchestrator (replaces old data fetcher)
        self.cache_orchestrator = CacheDataOrchestrator(self.event_bus)
        print(f"✅ Cache Data Orchestrator: Raw XBRL + Event System")
        
        # Other components (unchanged)
        self.analyzer = Analyzer(self.event_bus)
        self.news_manager = NewsManager(self.event_bus)
        self.metrics_display = MetricsDisplay(self.event_bus)
        
        # Initialize chart manager
        if CHART_MANAGER_AVAILABLE:
            try:
                # Initialize chart manager - will connect to UI later
                self.chart_manager = EnhancedChartManager(self.event_bus)
                print("✅ Enhanced Chart Manager: Initialized")
            except Exception as e:
                print(f"⚠️ Enhanced chart manager failed: {e}")
                self.chart_manager = None
        else:
            print("❌ Chart manager not available")
            self.chart_manager = None
        
        # Connect components to UI containers
        self._connect_components_to_ui()
        
        # REMOVED: Background cache updates start - no longer automatic
        # self.cache_orchestrator.start_background_cache_updates()
        
        # Print initialization summary
        print(f"\n🎉 StockerApp initialized successfully!")
        print(f"📊 Architecture: Cache Manager → XBRL Data → Event System → Charts")
        print(f"⚡ Performance: Fast cache loading with on-demand updates")
        print(f"🔄 Background: Cache updates only when needed")
        
    def _connect_components_to_ui(self):
        """Connect components to their UI containers"""
        try:
            overview_frame = self.main_window.tab_manager.get_tab_frame('Overview')
            charts_frame = self.main_window.tab_manager.get_tab_frame('Charts')
            analysis_frame = self.main_window.tab_manager.get_tab_frame('Analysis')
            financials_frame = self.main_window.tab_manager.get_tab_frame('Financials')
            
            # Connect components to their containers
            if overview_frame and self.metrics_display:
                self.metrics_display.set_container(overview_frame)
                print("✅ Metrics display → Overview tab")
            
            # Connect chart manager to Financials tab
            if financials_frame and self.chart_manager:
                try:
                    self.chart_manager.set_container('Financials', financials_frame)
                    print("✅ Chart manager → Financials tab (cache-powered)")
                except Exception as e:
                    print(f"⚠️ Error connecting chart manager: {e}")
                    self._setup_financials_placeholder(financials_frame)
            
            if analysis_frame and self.analyzer:
                self.analyzer.set_container(analysis_frame)
                print("✅ Analyzer → Analysis tab")
            
            # Charts tab placeholder
            if charts_frame:
                self._setup_basic_charts_tab(charts_frame)
                print("✅ Basic charts → Charts tab")
            
            # Verify connections
            connected_tabs = sum([
                1 if overview_frame else 0,
                1 if charts_frame else 0,
                1 if analysis_frame else 0,
                1 if financials_frame else 0
            ])
            
            print(f"📊 Connected {connected_tabs}/4 tabs successfully")
            
        except Exception as e:
            print(f"⚠️ Error connecting components to UI: {e}")
    
    def _setup_basic_charts_tab(self, charts_frame: tk.Frame):
        """Setup basic charts tab with placeholder content"""
        for widget in charts_frame.winfo_children():
            widget.destroy()
        
        placeholder_label = tk.Label(
            charts_frame,
            text="📈 Additional Charts\n\n" +
                 "This tab is available for:\n" +
                 "• Price charts\n" +
                 "• Technical analysis\n" +
                 "• Custom visualizations\n\n" +
                 "💡 Financial charts (Revenue/FCF) are in the Financials tab",
            font=('Arial', 12),
            bg='#f0f0f0',
            fg='#666666',
            justify='center'
        )
        placeholder_label.pack(expand=True)
    
    def _setup_financials_placeholder(self, financials_frame: tk.Frame):
        """Setup placeholder for financials tab if chart manager fails"""
        for widget in financials_frame.winfo_children():
            widget.destroy()
        
        placeholder_label = tk.Label(
            financials_frame,
            text="📊 Financial Analysis\n\n" +
                 "⚠️ Chart manager not available\n" +
                 "Please check:\n" +
                 "• components/chart_manager.py exists\n" +
                 "• components/charts/ directory exists\n" +
                 "• All chart dependencies installed\n\n" +
                 "Data extraction is working, but charts need setup.",
            font=('Arial', 12),
            bg='#f0f0f0',
            fg='#666666',
            justify='center'
        )
        placeholder_label.pack(expand=True)
    
    def get_app_status(self) -> dict:
        """Get application status for debugging"""
        status = {
            'app_version': APP_CONFIG.get('version', '2.0'),
            'components_initialized': {
                'cache_orchestrator': self.cache_orchestrator is not None,
                'chart_manager': self.chart_manager is not None,
                'analyzer': self.analyzer is not None,
                'metrics_display': self.metrics_display is not None,
                'news_manager': self.news_manager is not None
            },
            'cache_system': 'new_xbrl_cache',
            'background_updates': 'on_demand_only'
        }
        
        # Get cache status
        if self.cache_orchestrator:
            status['cache_stats'] = self.cache_orchestrator.get_cache_stats()
        
        return status
    
    def run(self):
        """Start the application"""
        print("🚀 Starting Stocker with new cache system...")
        print("📊 Raw XBRL data will be cached and processed on demand!")
        self.root.mainloop()