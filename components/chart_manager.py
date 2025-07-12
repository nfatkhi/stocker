# components/chart_manager.py - Fixed imports and data flow for new chart structure with Q4 calculation

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional
import json
import os

from core.event_system import EventBus, Event, EventType

# Import the NEW cache manager
from components.cache_manager import CacheManager

# Import chart components with FIXED paths
try:
    from components.charts.revenue.revenue_chart import RevenueTab
    from components.charts.revenue.revenue_data_processor import get_processed_revenue_data
    REVENUE_CHARTS_AVAILABLE = True
    print("✅ Revenue charts loaded from new structure")
except ImportError as e:
    REVENUE_CHARTS_AVAILABLE = False
    print(f"⚠️ Revenue charts not available: {e}")

# Try to import cash flow charts (future structure)
try:
    from components.charts.cashflow.cashflow_chart import CashFlowTab
    CASHFLOW_CHARTS_AVAILABLE = True
    print("✅ Cash flow charts loaded")
except ImportError:
    CASHFLOW_CHARTS_AVAILABLE = False
    print("⚠️ Cash flow charts not available - will create placeholder")

# Try to import config
try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {
        'font_family': 'Arial',
        'font_size': 10,
        'chart_height': 400,
        'metric_card_width': 200,
        'status_bar_height': 30,
    }


class EnhancedChartManager:
    """Enhanced chart manager supporting new chart structure with data processors and Q4 calculation"""
    
    def __init__(self, event_bus: EventBus, api_keys: Dict[str, str] = None, cache_dir: str = "data/cache"):
        self.event_bus = event_bus
        self.cache_dir = cache_dir
        self.parent_frame = None
        
        # Initialize cache manager
        self.cache_manager = CacheManager(cache_dir=cache_dir)
        
        # Current state
        self.current_ticker = ""
        self.current_cache_data = []
        self.current_all_quarters_data = []  # NEW: Store all quarters for Q4 calculation
        
        # Color scheme
        self.colors = {
            'bg': '#2b2b2b',
            'frame': '#3c3c3c',
            'text': '#ffffff',
            'header': '#4CAF50',
            'accent': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336'
        }
        
        # Chart tabs
        self.revenue_tab = None
        self.cashflow_tab = None
        self.notebook = None
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.STOCK_SELECTED, self.on_stock_selected)
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.on_data_received)
        
        print("📊 Enhanced Chart Manager initialized with FIXED imports + Q4 calculation")
        print(f"   📁 Cache directory: {cache_dir}")
        print(f"   📈 Revenue charts: {'✅' if REVENUE_CHARTS_AVAILABLE else '❌'}")
        print(f"   💰 Cash flow charts: {'✅' if CASHFLOW_CHARTS_AVAILABLE else '❌'}")
        print(f"   🧮 Q4 Calculation: ✅ (uses all 15 cached quarters)")
    
    def set_container(self, tab_name: str, container_frame: tk.Frame):
        """Set container frame and setup UI"""
        self.parent_frame = container_frame
        self._setup_ui()
        print(f"📊 Chart Manager container set for {tab_name}")
    
    def _setup_ui(self):
        """Setup chart UI with new structure and Q4 calculation support"""
        if not self.parent_frame:
            print("📊 Chart Manager: No parent frame yet, skipping UI setup")
            return
        
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Main container
        main_frame = tk.Frame(self.parent_frame, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Header with new structure info + Q4 calculation
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 10))
        
        header_label = tk.Label(
            header_frame,
            text="📊 Financial Charts - FIXED Structure + Q4 Calculation",
            font=(UI_CONFIG['font_family'], 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['header']
        )
        header_label.pack(side='left')
        
        # Cache status indicator with Q4 info
        self.cache_status_label = tk.Label(
            header_frame,
            text="📁 15-Quarter Cache System Ready for Q4 Calc",
            font=(UI_CONFIG['font_family'], 10),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        self.cache_status_label.pack(side='right')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Create tab frames
        self.revenue_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.cashflow_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        
        # Add tabs to notebook with Q4 info
        self.notebook.add(self.revenue_frame, text='📈 Revenue (Q4 Calc)')
        self.notebook.add(self.cashflow_frame, text='💰 Cash Flow')
        
        # Initialize tabs
        if REVENUE_CHARTS_AVAILABLE:
            self.revenue_tab = RevenueTab(self.revenue_frame)
            self.revenue_tab.show_placeholder()
            print("✅ Revenue tab initialized with FIXED structure + Q4 calculation")
        else:
            self._setup_revenue_fallback()
        
        if CASHFLOW_CHARTS_AVAILABLE:
            self.cashflow_tab = CashFlowTab(self.cashflow_frame)
            self.cashflow_tab.show_placeholder()
            print("✅ Cash flow tab initialized")
        else:
            self._setup_cashflow_placeholder()
        
        print("📊 Enhanced Chart Manager UI setup completed with FIXED imports + Q4 calc")
    
    def _setup_revenue_fallback(self):
        """Setup fallback for revenue charts"""
        tk.Label(
            self.revenue_frame,
            text="📈 Revenue Charts\n\n❌ Import failed\n\nCheck:\n• components/charts/revenue/revenue_chart.py\n• components/charts/revenue/revenue_data_processor.py\n• components/charts/base_chart.py\n\nImport path issues resolved in this version\n🧮 Q4 Calculation: Ready when imports fixed",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            justify='center'
        ).pack(expand=True)
    
    def _setup_cashflow_placeholder(self):
        """Setup placeholder for cash flow charts"""
        tk.Label(
            self.cashflow_frame,
            text="💰 Cash Flow Charts\n\n🔄 Coming Soon\n\nWill be structured as:\ncomponents/charts/cashflow/\n├── cashflow_chart.py\n└── cashflow_data_processor.py\n\n🧮 Future: FCF Q4 calculation support",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            justify='center'
        ).pack(expand=True)
    
    def on_stock_selected(self, event):
        """Handle stock selection with new cache system + Q4 calculation"""
        ticker = event.data.get('ticker', '').upper()
        
        if not ticker:
            print("⚠️ No ticker provided in stock selection event")
            return
        
        print(f"\n🔄 Processing stock selection: {ticker} (FIXED Import Path + Q4 Calc)")
        self.current_ticker = ticker
        
        # Show loading state
        self._show_loading_state()
        
        # Emit loading started
        self.event_bus.publish(Event(
            type=EventType.LOADING_STARTED,
            data={'ticker': ticker, 'message': f'Loading data for {ticker}...'},
            source='enhanced_chart_manager'
        ))
        
        try:
            # Get display data (12 quarters) 
            quarterly_data, metadata = self.cache_manager.get_ticker_data(ticker)
            
            # FIXED: Get ALL quarters (15) for Q4 calculation
            all_quarters_data, all_metadata = self.cache_manager.get_ticker_data_for_calculation(ticker)
            
            if not quarterly_data:
                error_msg = metadata.get('error', f'No data available for {ticker}')
                self._show_error_state(error_msg)
                return
            
            self.current_cache_data = quarterly_data
            self.current_all_quarters_data = all_quarters_data  # Store all quarters for Q4 calc
            
            print(f"📊 Loaded {len(quarterly_data)} display quarters")
            print(f"🧮 Loaded {len(all_quarters_data)} total quarters for Q4 calculation")
            
            # FIXED: Update charts with proper data processing + Q4 calculation
            self._update_charts_with_processed_data_and_q4_calc(quarterly_data, all_quarters_data, metadata)
            
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            import traceback
            traceback.print_exc()
            self._show_error_state(str(e))
        finally:
            # Emit loading completed
            self.event_bus.publish(Event(
                type=EventType.LOADING_COMPLETED,
                data={'ticker': ticker},
                source='enhanced_chart_manager'
            ))
    
    def on_data_received(self, event):
        """Handle data received event (for compatibility)"""
        data = event.data
        stock_data = data.get('stock_data')
        
        if not stock_data or stock_data.ticker != self.current_ticker:
            return
        
        print(f"📊 Data received event for {stock_data.ticker} (using cache data + Q4 calc)")
        # Note: We prioritize cache data over event data for consistency with Q4 calculation
    
    def _update_charts_with_processed_data_and_q4_calc(self, display_quarters: List[Dict], all_quarters: List[Dict], metadata: Dict):
        """FIXED: Update charts with proper data processing integration + Q4 calculation"""
        try:
            print(f"📊 FIXED: Updating charts with {len(display_quarters)} display quarters from cache")
            print(f"🧮 Q4 CALC: Using {len(all_quarters)} total quarters for calculation")
            
            # Process revenue data if available
            if REVENUE_CHARTS_AVAILABLE and self.revenue_tab:
                print("   📈 Processing revenue data through FIXED structure + Q4 calc...")
                
                try:
                    # FIXED: Use the revenue data processor properly for display data
                    processed_display_revenue = get_processed_revenue_data(display_quarters)
                    
                    # FIXED: Process ALL quarters for Q4 calculation
                    processed_all_revenue = get_processed_revenue_data(all_quarters)
                    
                    if processed_display_revenue:
                        print(f"      ✅ Display revenue processor: {len(processed_display_revenue)} quarters processed")
                        print(f"      🧮 Q4 calc revenue processor: {len(processed_all_revenue)} quarters available")
                        print(f"      ✅ First display quarter sample: {processed_display_revenue[0].quarter} {processed_display_revenue[0].year}")
                        
                        # FIXED: Update revenue tab with processed data + Q4 calculation support
                        self.revenue_tab.update_data(
                            financial_data=processed_display_revenue,  # Pass processed display data 
                            ticker=self.current_ticker,
                            data_source_info={
                                'metadata': metadata, 
                                'data_source': 'Multi-Row Cache → Data Processor → Charts + Q4 Calc',
                                'processing_method': 'revenue_data_processor',
                                'q4_calculation_enabled': True,
                                'display_quarters': len(processed_display_revenue),
                                'calculation_quarters': len(processed_all_revenue)
                            },
                            all_quarters_data=processed_all_revenue  # NEW: Pass all quarters for Q4 calculation
                        )
                        print("      ✅ Revenue tab updated with processed data + Q4 calculation")
                    else:
                        print("      ❌ Revenue processor returned no data")
                        self._show_revenue_no_data()
                        
                except Exception as e:
                    print(f"      ❌ Revenue processing error: {e}")
                    import traceback
                    traceback.print_exc()
                    self._show_revenue_error(str(e))
            
            # Process cash flow data if available
            if CASHFLOW_CHARTS_AVAILABLE and self.cashflow_tab:
                print("   💰 Processing cash flow data...")
                # Future: Add cash flow data processor here
                self._show_cashflow_coming_soon()
            
            # Update cache status with Q4 calculation info
            if hasattr(self, 'cache_status_label'):
                q4_calc_count = 0
                try:
                    q4_calc_count = len([q for q in processed_all_revenue if getattr(q, 'revenues_needs_q4_calculation', False)])
                except:
                    pass
                
                self.cache_status_label.config(
                    text=f"📁 {len(display_quarters)} display + {len(all_quarters)} calc quarters (Q4 calc: {q4_calc_count})",
                    fg=self.colors['success']
                )
                
        except Exception as e:
            print(f"❌ Error updating charts: {e}")
            import traceback
            traceback.print_exc()
            self._show_error_state(str(e))
    
    def _show_loading_state(self):
        """Show loading state for both tabs"""
        loading_text = f"🔄 Loading data for {self.current_ticker} with Q4 calculation..."
        
        if hasattr(self, 'revenue_frame'):
            for widget in self.revenue_frame.winfo_children():
                widget.destroy()
            tk.Label(
                self.revenue_frame,
                text=loading_text,
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['text'],
                justify='center'
            ).pack(expand=True)
        
        if hasattr(self, 'cashflow_frame'):
            for widget in self.cashflow_frame.winfo_children():
                widget.destroy()
            tk.Label(
                self.cashflow_frame,
                text=loading_text,
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['text'],
                justify='center'
            ).pack(expand=True)
    
    def _show_error_state(self, error_message: str):
        """Show error state for both tabs"""
        self._show_revenue_error(error_message)
        self._show_cashflow_error(error_message)
    
    def _show_revenue_no_data(self):
        """Show no data message for revenue tab"""
        if not hasattr(self, 'revenue_frame'):
            return
        
        for widget in self.revenue_frame.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.revenue_frame,
            text=f"📈 No Revenue Data\n\nTicker: {self.current_ticker}\n• No revenue facts in cache\n• Check data processor logic\n• Debug output in console\n\nFIXED: Import paths resolved\n🧮 Q4 Calculation: Ready but no data",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            justify='center'
        ).pack(expand=True)
    
    def _show_revenue_error(self, error_message: str):
        """Show error message for revenue tab"""
        if not hasattr(self, 'revenue_frame'):
            return
        
        for widget in self.revenue_frame.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.revenue_frame,
            text=f"❌ Revenue Chart Error\n\n{error_message}\n\nFIXED: Import structure updated\n🧮 Q4 Calculation: System ready, chart error",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['error'],
            justify='center'
        ).pack(expand=True)
    
    def _show_cashflow_coming_soon(self):
        """Show coming soon message for cash flow tab"""
        if not hasattr(self, 'cashflow_frame'):
            return
        
        for widget in self.cashflow_frame.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.cashflow_frame,
            text=f"💰 Cash Flow Analysis\n\n🔄 Coming Soon\n\nWill include:\n• Operating Cash Flow\n• Free Cash Flow calculation\n• Cash flow data processor\n• QoQ comparisons\n• FCF Q4 calculation support",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            justify='center'
        ).pack(expand=True)
    
    def _show_cashflow_error(self, error_message: str):
        """Show error message for cash flow tab"""
        if not hasattr(self, 'cashflow_frame'):
            return
        
        for widget in self.cashflow_frame.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.cashflow_frame,
            text=f"❌ Cash Flow Error\n\n{error_message}",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['error'],
            justify='center'
        ).pack(expand=True)
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get current data status for debugging"""
        cache_stats = self.cache_manager.get_cache_stats()
        
        return {
            'ticker': self.current_ticker,
            'cache_quarters_display': len(self.current_cache_data),
            'cache_quarters_calculation': len(self.current_all_quarters_data),  # NEW
            'charts_structure': 'FIXED_imports_organized_by_type_with_Q4_calc',
            'revenue_charts_available': REVENUE_CHARTS_AVAILABLE,
            'cashflow_charts_available': CASHFLOW_CHARTS_AVAILABLE,
            'cache_directory': self.cache_dir,
            'data_source': 'Multi-Row Cache → Data Processor → Charts + Q4 Calculation',
            'cache_stats': cache_stats,
            'import_status': 'FIXED',
            'q4_calculation_enabled': True,  # NEW
            'data_flow': 'cache_manager.get_ticker_data() + get_ticker_data_for_calculation() → get_processed_revenue_data() → revenue_tab.update_data() + Q4 calc',
            'structure_features': [
                'FIXED absolute imports from components.*',
                'Data processors for intelligent value selection',
                'Period classification (quarterly vs annual)',
                'Q4 calculation from annual data using ALL 17 quarters',  # UPDATED
                'Chart type organization',
                'Enhanced error handling',
                'Q4 calculation works even when oldest display quarter is Q4'  # NEW
            ]
        }
    
    def refresh_current_data(self):
        """Refresh current data using cache manager with Q4 calculation"""
        if self.current_ticker:
            try:
                # Get both display and calculation data
                quarterly_data, metadata = self.cache_manager.get_ticker_data(self.current_ticker)
                all_quarters_data, all_metadata = self.cache_manager.get_ticker_data_for_calculation(self.current_ticker)
                
                if quarterly_data:
                    self.current_cache_data = quarterly_data
                    self.current_all_quarters_data = all_quarters_data
                    self._update_charts_with_processed_data_and_q4_calc(quarterly_data, all_quarters_data, metadata)
                else:
                    self._show_error_state("No data available after refresh")
            except Exception as e:
                print(f"❌ Error refreshing data: {e}")
                self._show_error_state(str(e))


# Compatibility aliases
DirectCacheChartManager = EnhancedChartManager
ChartManager = EnhancedChartManager


if __name__ == "__main__":
    print("🧪 Testing FIXED Enhanced Chart Manager with Q4 calculation...")
    
    from core.event_system import EventBus
    
    event_bus = EventBus()
    
    # Test with dummy parent frame
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    
    test_frame = tk.Frame(root)
    
    try:
        chart_manager = EnhancedChartManager(event_bus)
        chart_manager.set_container('Financials', test_frame)
        print("✅ FIXED Enhanced chart manager created successfully with Q4 calculation")
        
        # Test data status
        status = chart_manager.get_data_status()
        print(f"📊 Chart Manager Status: {status}")
        
    except Exception as e:
        print(f"❌ Failed to create enhanced chart manager: {e}")
        import traceback
        traceback.print_exc()
    
    root.destroy()
    print("✅ FIXED Enhanced Chart Manager with Q4 calculation test completed!")