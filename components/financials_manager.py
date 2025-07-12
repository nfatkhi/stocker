# components/financials_manager.py - Simplified for EdgarTools only

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Dict, Any

from core.event_system import EventBus, Event, EventType

# Import chart components
try:
    from .charts.revenue_chart import RevenueTab
    from .charts.cashflow_chart import CashFlowTab
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    print("⚠️ Chart components not available")

# Try to import models
try:
    from models import QuarterlyFinancials
except ImportError:
    try:
        from core.models import QuarterlyFinancials
    except ImportError:
        from dataclasses import dataclass
        
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


class FinancialsManager:
    """
    SIMPLIFIED EDGARTOOLS: Financial Analysis Manager
    
    Single data source: EdgarTools for both FCF and Revenue
    Simplified architecture without complex data routing
    """
    
    def __init__(self, parent=None, event_bus=None, **kwargs):
        """Initialize with flexible arguments"""
        self.parent_frame = parent or kwargs.get('parent_frame')
        self.event_bus = event_bus or kwargs.get('event_bus')
        
        if not self.parent_frame or not self.event_bus:
            raise ValueError("FinancialsManager requires both parent and event_bus arguments")
        
        # Current state
        self.current_ticker = ""
        self.current_financial_data = []  # All financial data from EdgarTools
        self.data_source_info = {}
        
        # Data availability flags
        self.fcf_data_available = False
        self.revenue_data_available = False
        
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
        
        # Initialize tab components
        self.revenue_tab = None
        self.cashflow_tab = None
        self.notebook = None
        self.tab_data_loaded = {'revenue': False, 'cashflow': False}
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.on_data_received)
        self.event_bus.subscribe(EventType.TAB_CHANGED, self.on_tab_changed)
        
        # Setup UI
        self._setup_ui()
        
        if CHARTS_AVAILABLE:
            print("📊 SIMPLIFIED EDGARTOOLS: Financials Manager initialized")
            print("   📈 Single source: EdgarTools for all financial data")
            print("   🎯 Simplified architecture - no complex data routing")
        else:
            print("📊 Basic Financials Manager initialized - chart components not available")
    
    def _setup_ui(self):
        """Setup the financial analysis UI with tabbed interface"""
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        if not CHARTS_AVAILABLE:
            self._setup_fallback_ui()
            return
        
        # Main container
        main_frame = tk.Frame(self.parent_frame, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Header with data source information
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 10))
        
        header_label = tk.Label(
            header_frame,
            text="📊 Financial Analysis - EdgarTools (SEC EDGAR)",
            font=(UI_CONFIG['font_family'], 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['header']
        )
        header_label.pack(side='left')
        
        # Data source indicator
        self.data_source_label = tk.Label(
            header_frame,
            text="📈 Single Source: EdgarTools (SEC EDGAR)",
            font=(UI_CONFIG['font_family'], 10),
            bg=self.colors['bg'],
            fg=self.colors['accent']
        )
        self.data_source_label.pack(side='right')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Bind tab change event
        self.notebook.bind('<<NotebookTabChanged>>', self._on_notebook_tab_changed)
        
        # Create tab frames
        self.revenue_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.cashflow_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        
        # Add tabs to notebook
        self.notebook.add(self.revenue_frame, text='📈 Revenue (EdgarTools)')
        self.notebook.add(self.cashflow_frame, text='💰 Free Cash Flow (EdgarTools)')
        
        # Initialize tab components
        self.revenue_tab = RevenueTab(self.revenue_frame)
        self.cashflow_tab = CashFlowTab(self.cashflow_frame)
        
        # Show initial placeholders
        self.revenue_tab.show_placeholder()
        self.cashflow_tab.show_placeholder()
    
    def _setup_fallback_ui(self):
        """Setup fallback UI when chart components are not available"""
        tk.Label(
            self.parent_frame,
            text="📊 Financial Analysis - EdgarTools\n\n⚠️ Chart components not available\nPlease ensure components/charts/ directory exists with required files:\n\n• base_chart.py\n• revenue_chart.py\n• cashflow_chart.py\n• __init__.py",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            justify='center'
        ).pack(expand=True)
    
    def on_data_received(self, event):
        """Handle data received from EdgarTools data fetcher"""
        data = event.data
        stock_data = data.get('stock_data')
        
        if not stock_data:
            print("❌ No stock data received")
            return
        
        self.current_ticker = stock_data.ticker
        approach = data.get('approach', 'unknown')
        
        print(f"\n🔄 EDGARTOOLS DATA RECEIVED for {self.current_ticker}")
        print("=" * 60)
        
        if approach == 'edgartools_unified':
            # ========================================
            # EDGARTOOLS UNIFIED APPROACH
            # ========================================
            
            # Get all financial data from EdgarTools
            self.current_financial_data = stock_data.quarterly_financials
            
            # Extract revenue and FCF data
            revenue_data = data.get('revenue_data', [])
            fcf_data = data.get('fcf_data', [])
            
            self.data_source_info = {
                'source': 'EdgarTools',
                'total_quarters': len(self.current_financial_data),
                'revenue_quarters': len(revenue_data),
                'fcf_quarters': len(fcf_data),
                'approach': approach,
                'metadata': data.get('metadata', {})
            }
            
            # Update availability flags
            self.fcf_data_available = len(fcf_data) > 0
            self.revenue_data_available = len(revenue_data) > 0
            
            print(f"📊 EdgarTools unified data:")
            print(f"   📈 Total quarters: {len(self.current_financial_data)}")
            print(f"   💰 Revenue quarters: {len(revenue_data)}")
            print(f"   💸 FCF quarters: {len(fcf_data)}")
            print(f"   ✅ Revenue available: {self.revenue_data_available}")
            print(f"   ✅ FCF available: {self.fcf_data_available}")
            
            # Store separated data for tabs
            self.revenue_data = revenue_data
            self.fcf_data = fcf_data
            
            # Reset tab loading states
            self.tab_data_loaded = {'revenue': False, 'cashflow': False}
            
            # Update data source indicator
            if CHARTS_AVAILABLE and hasattr(self, 'data_source_label'):
                status = "✅" if (self.revenue_data_available and self.fcf_data_available) else "⚠️"
                self.data_source_label.config(
                    text=f"{status} EdgarTools: {len(self.current_financial_data)} quarters",
                    fg=self.colors['success'] if (self.revenue_data_available and self.fcf_data_available) else self.colors['warning']
                )
            
            # Load data for currently active tab
            self._load_current_tab_data()
            
        else:
            # ========================================
            # FALLBACK FOR OTHER APPROACHES
            # ========================================
            
            print(f"⚠️ Unexpected approach: {approach}")
            
            # Try to work with whatever data we have
            self.current_financial_data = stock_data.quarterly_financials or []
            
            # Extract what we can
            revenue_data = [q for q in self.current_financial_data if hasattr(q, 'revenue') and q.revenue > 0]
            fcf_data = [q for q in self.current_financial_data if hasattr(q, 'cash') and q.cash != 0]
            
            self.revenue_data = revenue_data
            self.fcf_data = fcf_data
            
            self.revenue_data_available = len(revenue_data) > 0
            self.fcf_data_available = len(fcf_data) > 0
            
            self.data_source_info = {
                'source': 'Unknown',
                'total_quarters': len(self.current_financial_data),
                'approach': 'fallback'
            }
            
            # Reset tab loading states
            self.tab_data_loaded = {'revenue': False, 'cashflow': False}
            
            # Load data for currently active tab
            self._load_current_tab_data()
    
    def _on_notebook_tab_changed(self, event):
        """Handle notebook tab change event"""
        if not CHARTS_AVAILABLE:
            return
        
        try:
            current_tab_index = self.notebook.index(self.notebook.select())
            tab_name = self._get_tab_name_from_index(current_tab_index)
            
            print(f"🔄 Tab changed to: {tab_name} (index: {current_tab_index})")
            
            # Publish tab change event
            self.event_bus.publish(Event(
                type=EventType.TAB_CHANGED,
                data={
                    'tab_name': tab_name,
                    'tab_index': current_tab_index,
                    'ticker': self.current_ticker,
                    'data_available': {
                        'fcf': self.fcf_data_available,
                        'revenue': self.revenue_data_available
                    }
                }
            ))
            
            # Load data for the new tab if not already loaded
            self._load_current_tab_data()
            
        except tk.TclError:
            print("⚠️ Tab change event handling: Notebook not ready")
    
    def on_tab_changed(self, event):
        """Handle tab changed event (from external sources)"""
        tab_name = event.data.get('tab_name', '')
        print(f"📊 External tab change request: {tab_name}")
        self._load_current_tab_data()
    
    def _get_tab_name_from_index(self, index: int) -> str:
        """Get tab name from index"""
        tab_names = ['revenue', 'cashflow']
        return tab_names[index] if index < len(tab_names) else 'unknown'
    
    def _load_current_tab_data(self):
        """Load data for currently active tab"""
        if not CHARTS_AVAILABLE or not self.current_ticker:
            return
        
        try:
            current_tab_index = self.notebook.index(self.notebook.select())
            tab_name = self._get_tab_name_from_index(current_tab_index)
            
            print(f"🔄 Loading EdgarTools data for {tab_name} tab...")
            
            if tab_name == 'revenue' and not self.tab_data_loaded['revenue']:
                self._load_revenue_tab_data()
                
            elif tab_name == 'cashflow' and not self.tab_data_loaded['cashflow']:
                self._load_cashflow_tab_data()
                
        except tk.TclError:
            print("⚠️ Notebook not ready for tab loading")
    
    def _load_revenue_tab_data(self):
        """Load revenue data into revenue tab"""
        print(f"\n📈 LOADING REVENUE TAB DATA (EdgarTools)")
        print("-" * 40)
        
        if not self.revenue_data_available:
            print(f"❌ No revenue data available from EdgarTools")
            self._show_revenue_no_data()
            return
        
        try:
            print(f"✅ Loading {len(self.revenue_data)} quarters of revenue data")
            print(f"📊 Source: EdgarTools (SEC EDGAR)")
            
            # Update revenue tab with EdgarTools data
            self.revenue_tab.update_data(
                self.revenue_data, 
                self.current_ticker,
                {
                    **self.data_source_info,
                    'data_type': 'revenue_edgartools',
                    'primary_source': 'EdgarTools'
                }
            )
            
            self.tab_data_loaded['revenue'] = True
            print(f"✅ Revenue tab loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading revenue tab: {e}")
            import traceback
            traceback.print_exc()
            self._show_revenue_error(str(e))
    
    def _load_cashflow_tab_data(self):
        """Load FCF data into cashflow tab"""
        print(f"\n💰 LOADING CASHFLOW TAB DATA (EdgarTools)")
        print("-" * 40)
        
        if not self.fcf_data_available:
            print(f"❌ No FCF data available from EdgarTools")
            self._show_cashflow_no_data()
            return
        
        try:
            print(f"✅ Loading {len(self.fcf_data)} quarters of FCF data")
            print(f"📊 Source: EdgarTools (SEC EDGAR)")
            
            # Update cashflow tab with EdgarTools data
            self.cashflow_tab.update_data(
                self.fcf_data,
                self.current_ticker,
                {
                    **self.data_source_info,
                    'data_type': 'fcf_edgartools',
                    'primary_source': 'EdgarTools'
                }
            )
            
            self.tab_data_loaded['cashflow'] = True
            print(f"✅ Cashflow tab loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading cashflow tab: {e}")
            import traceback
            traceback.print_exc()
            self._show_cashflow_error(str(e))
    
    def _show_revenue_no_data(self):
        """Show no data message for revenue tab"""
        if self.revenue_tab:
            for widget in self.revenue_frame.winfo_children():
                widget.destroy()
            
            tk.Label(
                self.revenue_frame,
                text=f"📈 No Revenue Data Available\n\n" +
                     f"Source: EdgarTools (SEC EDGAR)\n\n" +
                     f"Ticker: {self.current_ticker}\n" +
                     f"• Check ticker symbol\n" +
                     f"• Company may not have recent SEC filings\n" +
                     f"• Revenue data may not be available in EDGAR",
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['warning'],
                justify='center'
            ).pack(expand=True)
    
    def _show_cashflow_no_data(self):
        """Show no data message for cashflow tab"""
        if self.cashflow_tab:
            for widget in self.cashflow_frame.winfo_children():
                widget.destroy()
            
            tk.Label(
                self.cashflow_frame,
                text=f"💰 No Free Cash Flow Data Available\n\n" +
                     f"Source: EdgarTools (SEC EDGAR)\n\n" +
                     f"Ticker: {self.current_ticker}\n" +
                     f"• Check ticker symbol\n" +
                     f"• Company may not have recent SEC filings\n" +
                     f"• Cash flow data may not be available in EDGAR",
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['warning'],
                justify='center'
            ).pack(expand=True)
    
    def _show_revenue_error(self, error_message: str):
        """Show error message for revenue tab"""
        if self.revenue_tab:
            for widget in self.revenue_frame.winfo_children():
                widget.destroy()
            
            tk.Label(
                self.revenue_frame,
                text=f"❌ Revenue Data Error\n\n{error_message}",
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['error'],
                justify='center'
            ).pack(expand=True)
    
    def _show_cashflow_error(self, error_message: str):
        """Show error message for cashflow tab"""
        if self.cashflow_tab:
            for widget in self.cashflow_frame.winfo_children():
                widget.destroy()
            
            tk.Label(
                self.cashflow_frame,
                text=f"❌ FCF Data Error\n\n{error_message}",
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['error'],
                justify='center'
            ).pack(expand=True)
    
    def force_reload_current_tab(self):
        """Force reload current tab data"""
        if not CHARTS_AVAILABLE:
            return
        
        current_tab_index = self.notebook.index(self.notebook.select())
        tab_name = self._get_tab_name_from_index(current_tab_index)
        
        print(f"🔄 Force reloading {tab_name} tab...")
        
        # Reset loading state
        self.tab_data_loaded[tab_name] = False
        
        # Reload data
        self._load_current_tab_data()
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get current data status for debugging"""
        return {
            'ticker': self.current_ticker,
            'total_quarters': len(self.current_financial_data),
            'revenue_available': self.revenue_data_available,
            'fcf_available': self.fcf_data_available,
            'revenue_quarters': len(getattr(self, 'revenue_data', [])),
            'fcf_quarters': len(getattr(self, 'fcf_data', [])),
            'tabs_loaded': self.tab_data_loaded.copy(),
            'data_source_info': self.data_source_info.copy(),
            'current_tab': self._get_tab_name_from_index(self.notebook.index(self.notebook.select())) if CHARTS_AVAILABLE else 'none'
        }
    
    # ========================================
    # LEGACY COMPATIBILITY METHODS
    # ========================================
    
    def set_container(self, container_frame: tk.Frame):
        """Set the container frame for the financials manager"""
        self.parent_frame = container_frame
        self._setup_ui()
        print("📊 EdgarTools Financials Manager container updated")
    
    def get_current_tab_index(self) -> int:
        """Get currently selected tab index"""
        if CHARTS_AVAILABLE and self.notebook:
            try:
                return self.notebook.index(self.notebook.select())
            except tk.TclError:
                return 0
        return 0
    
    def select_tab(self, tab_index: int):
        """Select a specific tab by index"""
        if CHARTS_AVAILABLE and self.notebook:
            try:
                if tab_index < self.notebook.index("end"):
                    self.notebook.select(tab_index)
                    self._load_current_tab_data()
            except tk.TclError:
                pass
    
    def refresh_current_tab(self):
        """Refresh the currently visible tab"""
        self.force_reload_current_tab()


# Factory function to create the manager with proper error handling
def create_financials_manager(parent_frame: tk.Frame, event_bus: EventBus, **kwargs):
    """Factory function to create FinancialsManager with error handling"""
    try:
        return FinancialsManager(parent_frame, event_bus, **kwargs)
    except Exception as e:
        print(f"❌ Error creating FinancialsManager: {e}")
        return BasicFinancialsManager(parent_frame, event_bus, **kwargs)


class BasicFinancialsManager:
    """Fallback financials manager if chart components are not available"""
    
    def __init__(self, parent_frame: tk.Frame, event_bus: EventBus, **kwargs):
        """Initialize basic fallback manager"""
        self.parent_frame = parent_frame
        self.event_bus = event_bus
        
        # Color scheme
        self.colors = {
            'bg': '#2b2b2b',
            'frame': '#3c3c3c',
            'text': '#ffffff',
            'header': '#4CAF50',
            'warning': '#FF9800',
        }
        
        # Setup basic UI
        self._setup_basic_ui()
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.on_data_received)
        
        print("📊 Basic Financials Manager initialized (fallback mode)")
    
    def _setup_basic_ui(self):
        """Setup basic UI when chart components are not available"""
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        tk.Label(
            self.parent_frame,
            text="📊 Financial Analysis - EdgarTools\n\n⚠️ Chart components not available\nPlease create components/charts/ directory with:\n\n• base_chart.py\n• revenue_chart.py\n• cashflow_chart.py\n• __init__.py\n\nThen restart the application.",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            justify='center'
        ).pack(expand=True)
    
    def on_data_received(self, event):
        """Handle data in basic mode"""
        stock_data = event.data.get('stock_data')
        if stock_data:
            print(f"📊 Basic mode: Received EdgarTools data for {stock_data.ticker}")
    
    def set_container(self, container_frame: tk.Frame):
        """Set container in basic mode"""
        self.parent_frame = container_frame
        self._setup_basic_ui()
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get data status in basic mode"""
        return {
            'mode': 'basic_fallback',
            'charts_available': False,
            'data_source': 'EdgarTools'
        }


if __name__ == "__main__":
    # Test the simplified financials manager
    root = tk.Tk()
    root.title("EdgarTools Financials Manager Test")
    root.geometry("1200x800")
    root.configure(bg='#2b2b2b')
    
    from core.event_system import EventBus
    
    event_bus = EventBus()
    
    try:
        manager = create_financials_manager(root, event_bus)
        print("✅ EdgarTools financials manager created successfully")
    except Exception as e:
        print(f"❌ Failed to create manager: {e}")
        tk.Label(root, text=f"Error: {e}", fg='red').pack(expand=True)
    
    root.mainloop()