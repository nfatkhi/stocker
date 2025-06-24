# components/financials_manager.py - UPDATED: Separated Data Routing Architecture

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Dict, Any

from core.event_system import EventBus, Event, EventType

# Import chart components with relative imports
try:
    from .charts.revenue_chart import RevenueTab
    from .charts.cashflow_chart import CashFlowTab
    CHARTS_AVAILABLE = True
except ImportError:
    # Fallback if charts not available
    CHARTS_AVAILABLE = False
    print("⚠️ Chart components not available, using fallback mode")

# Try to import models from different possible locations
try:
    from models import QuarterlyFinancials
except ImportError:
    try:
        from core.models import QuarterlyFinancials
    except ImportError:
        # Create basic model if none exists
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
    SEPARATED DATA ROUTING: Financial Analysis Manager
    
    Routes FCF data (Polygon.io) to cashflow_chart
    Routes Revenue data (SEC EDGAR) to revenue_chart
    Fetches data when tabs are activated
    """
    
    def __init__(self, parent=None, event_bus=None, **kwargs):
        """Initialize with flexible arguments to match existing interface"""
        # Handle different argument patterns
        self.parent_frame = parent or kwargs.get('parent_frame')
        self.event_bus = event_bus or kwargs.get('event_bus')
        
        if not self.parent_frame or not self.event_bus:
            raise ValueError("FinancialsManager requires both parent and event_bus arguments")
        
        # Current state
        self.current_ticker = ""
        self.current_fcf_data = []      # FCF data from Polygon.io
        self.current_revenue_data = []  # Revenue data from SEC EDGAR
        self.data_source_info = {}      # Information about data sources
        
        # Data availability flags
        self.fcf_data_available = False
        self.revenue_data_available = False
        
        # Color scheme for consistency
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
            print("📊 SEPARATED DATA ROUTING: Financials Manager initialized")
            print("   💰 FCF data -> cashflow_chart (Polygon.io)")
            print("   📈 Revenue data -> revenue_chart (SEC EDGAR)")
            print("   🔄 Lazy loading: Data fetched when tabs activated")
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
            text="📊 Financial Analysis - Separated Data Sources",
            font=(UI_CONFIG['font_family'], 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['header']
        )
        header_label.pack(side='left')
        
        # Data source indicator
        self.data_source_label = tk.Label(
            header_frame,
            text="💰 FCF: Polygon.io | 📈 Revenue: SEC EDGAR",
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
        
        # Add tabs to notebook with enhanced labels
        self.notebook.add(self.revenue_frame, text='📈 Revenue (SEC EDGAR)')
        self.notebook.add(self.cashflow_frame, text='💰 Free Cash Flow (Polygon.io)')
        
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
            text="📊 Financial Analysis\n\n⚠️ Chart components not available\nPlease ensure components/charts/ directory exists with required files:\n\n• base_chart.py\n• revenue_chart.py\n• cashflow_chart.py\n• __init__.py",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            justify='center'
        ).pack(expand=True)
    
    def on_data_received(self, event):
        """Handle separated data received from data fetcher"""
        data = event.data
        stock_data = data.get('stock_data')
        
        if not stock_data:
            print("❌ No stock data received")
            return
        
        # Extract separated data
        self.current_ticker = stock_data.ticker
        approach = data.get('approach', 'unknown')
        
        print(f"\n🔄 SEPARATED DATA ROUTING for {self.current_ticker}")
        print("=" * 60)
        
        if approach == 'separated':
            # ========================================
            # SEPARATED DATA APPROACH - NEW ROUTING
            # ========================================
            
            # Extract separated datasets
            self.current_fcf_data = data.get('fcf_data', [])
            self.current_revenue_data = data.get('revenue_data', [])
            self.data_source_info = {
                'fcf_source': data.get('fcf_source', 'Unknown'),
                'revenue_source': data.get('revenue_source', 'Unknown'),
                'fcf_quarters': data.get('fcf_quarters', 0),
                'revenue_quarters': data.get('revenue_quarters', 0),
                'approach': approach
            }
            
            # Update availability flags
            self.fcf_data_available = len(self.current_fcf_data) > 0
            self.revenue_data_available = len(self.current_revenue_data) > 0
            
            print(f"📊 Separated data received:")
            print(f"   💰 FCF data: {len(self.current_fcf_data)} quarters ({self.data_source_info['fcf_source']})")
            print(f"   📈 Revenue data: {len(self.current_revenue_data)} quarters ({self.data_source_info['revenue_source']})")
            print(f"   ✅ FCF available: {self.fcf_data_available}")
            print(f"   ✅ Revenue available: {self.revenue_data_available}")
            
            # Check for recent data
            if self.current_fcf_data:
                recent_fcf = [q for q in self.current_fcf_data if q.date.startswith('2024') or q.date.startswith('2025')]
                if recent_fcf:
                    print(f"   🎉 Recent FCF data: {len(recent_fcf)} quarters (2024-2025)!")
            
            # Reset tab loading states
            self.tab_data_loaded = {'revenue': False, 'cashflow': False}
            
            # Update data source indicator
            if CHARTS_AVAILABLE and hasattr(self, 'data_source_label'):
                fcf_status = "✅" if self.fcf_data_available else "❌"
                revenue_status = "✅" if self.revenue_data_available else "❌"
                
                self.data_source_label.config(
                    text=f"💰 FCF: {fcf_status} Polygon.io | 📈 Revenue: {revenue_status} SEC EDGAR",
                    fg=self.colors['success'] if (self.fcf_data_available and self.revenue_data_available) else self.colors['warning']
                )
            
            # Load data for currently active tab
            self._load_current_tab_data()
            
        else:
            # ========================================
            # FALLBACK TO COMBINED APPROACH
            # ========================================
            
            print(f"⚠️ Using fallback combined approach for {self.current_ticker}")
            
            quarterly_financials = stock_data.quarterly_financials
            
            # Try to separate the combined data based on content
            self.current_fcf_data = [q for q in quarterly_financials if q.cash != 0]
            self.current_revenue_data = [q for q in quarterly_financials if q.revenue > 0]
            
            self.fcf_data_available = len(self.current_fcf_data) > 0
            self.revenue_data_available = len(self.current_revenue_data) > 0
            
            self.data_source_info = {
                'fcf_source': 'Combined',
                'revenue_source': 'Combined', 
                'fcf_quarters': len(self.current_fcf_data),
                'revenue_quarters': len(self.current_revenue_data),
                'approach': 'combined_fallback'
            }
            
            # Reset tab loading states
            self.tab_data_loaded = {'revenue': False, 'cashflow': False}
            
            # Load data for currently active tab
            self._load_current_tab_data()
    
    def _on_notebook_tab_changed(self, event):
        """Handle notebook tab change event"""
        if not CHARTS_AVAILABLE:
            return
        
        # Get current tab info
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
                    'separated_data_available': {
                        'fcf': self.fcf_data_available,
                        'revenue': self.revenue_data_available
                    }
                }
            ))
            
            # Load data for the new tab if not already loaded
            self._load_current_tab_data()
            
        except tk.TclError:
            # Handle case where notebook might not be ready
            print("⚠️ Tab change event handling: Notebook not ready")
    
    def on_tab_changed(self, event):
        """Handle tab changed event (from external sources)"""
        # This can be used by other components to trigger tab changes
        tab_name = event.data.get('tab_name', '')
        print(f"📊 External tab change request: {tab_name}")
        self._load_current_tab_data()
    
    def _get_tab_name_from_index(self, index: int) -> str:
        """Get tab name from index"""
        tab_names = ['revenue', 'cashflow']
        return tab_names[index] if index < len(tab_names) else 'unknown'
    
    def _load_current_tab_data(self):
        """Load data for currently active tab - LAZY LOADING"""
        if not CHARTS_AVAILABLE or not self.current_ticker:
            return
        
        try:
            current_tab_index = self.notebook.index(self.notebook.select())
            tab_name = self._get_tab_name_from_index(current_tab_index)
            
            print(f"🔄 Loading data for {tab_name} tab...")
            
            if tab_name == 'revenue' and not self.tab_data_loaded['revenue']:
                self._load_revenue_tab_data()
                
            elif tab_name == 'cashflow' and not self.tab_data_loaded['cashflow']:
                self._load_cashflow_tab_data()
                
        except tk.TclError:
            # Handle case where notebook might not be ready
            print("⚠️ Notebook not ready for tab loading")
    
    def _load_revenue_tab_data(self):
        """Load revenue-specific data into revenue tab"""
        print(f"\n📈 LOADING REVENUE TAB DATA")
        print("-" * 40)
        
        if not self.revenue_data_available:
            print(f"❌ No revenue data available from {self.data_source_info.get('revenue_source', 'Unknown')}")
            self._show_revenue_no_data()
            return
        
        try:
            print(f"✅ Loading {len(self.current_revenue_data)} quarters of revenue data")
            print(f"📊 Source: {self.data_source_info.get('revenue_source', 'Unknown')}")
            
            # Update revenue tab with revenue-specific data
            self.revenue_tab.update_data(
                self.current_revenue_data, 
                self.current_ticker,
                {
                    **self.data_source_info,
                    'data_type': 'revenue_only',
                    'primary_source': self.data_source_info.get('revenue_source', 'Unknown')
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
        """Load FCF-specific data into cashflow tab"""
        print(f"\n💰 LOADING CASHFLOW TAB DATA")
        print("-" * 40)
        
        if not self.fcf_data_available:
            print(f"❌ No FCF data available from {self.data_source_info.get('fcf_source', 'Unknown')}")
            self._show_cashflow_no_data()
            return
        
        try:
            print(f"✅ Loading {len(self.current_fcf_data)} quarters of FCF data")
            print(f"📊 Source: {self.data_source_info.get('fcf_source', 'Unknown')}")
            
            # Check for recent FCF data
            recent_fcf = [q for q in self.current_fcf_data if q.date.startswith('2024') or q.date.startswith('2025')]
            if recent_fcf:
                print(f"🎉 Including {len(recent_fcf)} recent quarters (2024-2025)")
                for q in recent_fcf:
                    fcf_b = q.cash / 1e9
                    print(f"   📈 {q.date}: ${fcf_b:.2f}B")
            
            # Update cashflow tab with FCF-specific data
            self.cashflow_tab.update_data(
                self.current_fcf_data,
                self.current_ticker,
                {
                    **self.data_source_info,
                    'data_type': 'fcf_only',
                    'primary_source': self.data_source_info.get('fcf_source', 'Unknown')
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
            # Clear existing content
            for widget in self.revenue_frame.winfo_children():
                widget.destroy()
            
            tk.Label(
                self.revenue_frame,
                text=f"📈 No Revenue Data Available\n\n" +
                     f"Source: {self.data_source_info.get('revenue_source', 'SEC EDGAR')}\n\n" +
                     f"Ticker: {self.current_ticker}\n" +
                     f"• Check ticker symbol\n" +
                     f"• Company may not report revenue in standard format\n" +
                     f"• SEC EDGAR may not have recent filings",
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['warning'],
                justify='center'
            ).pack(expand=True)
    
    def _show_cashflow_no_data(self):
        """Show no data message for cashflow tab"""
        if self.cashflow_tab:
            # Clear existing content
            for widget in self.cashflow_frame.winfo_children():
                widget.destroy()
            
            tk.Label(
                self.cashflow_frame,
                text=f"💰 No Free Cash Flow Data Available\n\n" +
                     f"Source: {self.data_source_info.get('fcf_source', 'Polygon.io')}\n\n" +
                     f"Ticker: {self.current_ticker}\n" +
                     f"• Check ticker symbol\n" +
                     f"• Polygon.io API may be unavailable\n" +
                     f"• Company may not report cash flow data\n" +
                     f"• API key may be invalid",
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
            'fcf_data_available': self.fcf_data_available,
            'revenue_data_available': self.revenue_data_available,
            'fcf_quarters': len(self.current_fcf_data),
            'revenue_quarters': len(self.current_revenue_data),
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
        print("📊 Separated Financials Manager container updated")
    
    def add_chart_tab(self, tab_name: str, chart_component):
        """Add a new chart tab dynamically (for future expansion)"""
        if not CHARTS_AVAILABLE or not self.notebook:
            return None
        
        new_frame = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(new_frame, text=tab_name)
        
        # Initialize the chart component with the new frame
        if hasattr(chart_component, '__call__'):
            chart_instance = chart_component(new_frame)
            chart_instance.show_placeholder()
            return chart_instance
        return None
    
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
                    # Trigger data loading
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
        # Return basic fallback manager
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
            text="📊 Financial Analysis\n\n⚠️ Chart components not available\nPlease create components/charts/ directory with:\n\n• base_chart.py\n• revenue_chart.py\n• cashflow_chart.py\n• __init__.py\n\nThen restart the application.",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            justify='center'
        ).pack(expand=True)
    
    def on_data_received(self, event):
        """Handle data in basic mode"""
        stock_data = event.data['stock_data']
        print(f"📊 Basic mode: Received data for {stock_data.ticker}")
    
    def set_container(self, container_frame: tk.Frame):
        """Set container in basic mode"""
        self.parent_frame = container_frame
        self._setup_basic_ui()
    
    def get_data_status(self) -> Dict[str, Any]:
        """Get data status in basic mode"""
        return {
            'mode': 'basic_fallback',
            'charts_available': False
        }


if __name__ == "__main__":
    # Test the separated financials manager
    root = tk.Tk()
    root.title("Separated Financials Manager Test")
    root.geometry("1200x800")
    root.configure(bg='#2b2b2b')
    
    from core.event_system import EventBus
    
    event_bus = EventBus()
    
    try:
        manager = create_financials_manager(root, event_bus)
        print("✅ Separated financials manager created successfully")
    except Exception as e:
        print(f"❌ Failed to create manager: {e}")
        tk.Label(root, text=f"Error: {e}", fg='red').pack(expand=True)
    
    root.mainloop()