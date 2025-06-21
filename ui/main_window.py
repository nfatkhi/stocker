# ui/main_window.py - Updated with Financials Tab
import tkinter as tk
from tkinter import ttk
from core.event_system import EventBus, Event, EventType
from ui.widgets import (
    TickerInput, StatusBar, TabManager, 
    LoadingSpinner, MetricCard, StockChart
)
from components.financials_manager import FinancialsManager  # NEW IMPORT

class MainWindow:
    """Main application window using custom widgets"""
    
    def __init__(self, root, event_bus):
        self.root = root
        self.event_bus = event_bus
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._populate_tabs()
        self._subscribe_to_events()
        
        # Force initial update
        self.root.update_idletasks()
    
    def _setup_window(self):
        """Configure main window"""
        self.root.title("Stocker - Stock Analysis Tool")
        self.root.configure(bg='#f0f0f0')
        self.root.minsize(900, 700)
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Header frame
        self.header_frame = ttk.Frame(self.root)
        
        # Ticker input widget
        self.ticker_input = TickerInput(
            self.header_frame, 
            self.event_bus
        )
        
        # Tab manager
        self.tab_manager = TabManager(self.root, self.event_bus)
        
        # Status bar
        self.status_bar = StatusBar(self.root, self.event_bus)
        
        # Loading spinner (initially hidden)
        self.loading_spinner = LoadingSpinner(
            self.root,
            text="Fetching stock data..."
        )
        
        # Note: FinancialsManager will be created in _setup_financials_tab()
        # when the tab frame is available
    
    def _setup_layout(self):
        """Arrange widgets in window"""
        # Header
        self.header_frame.pack(fill='x', padx=10, pady=5)
        self.ticker_input.pack(side='left')
        
        # Main content (tabs)
        self.tab_manager.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Status bar at bottom
        self.status_bar.pack(fill='x', side='bottom')
        
        # Loading spinner is not packed initially (hidden)
    
    def _populate_tabs(self):
        """Add content to each tab"""
        # Overview Tab - Add metric cards
        self._setup_overview_tab()
        
        # Charts Tab - Add stock chart
        self._setup_charts_tab()
        
        # Financials Tab - Add financial analysis (NEW)
        self._setup_financials_tab()
    
    def _setup_overview_tab(self):
        """Setup overview tab with metric cards"""
        overview_frame = self.tab_manager.get_tab_frame('Overview')
        
        # Create a frame for metrics
        metrics_frame = ttk.Frame(overview_frame)
        metrics_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            metrics_frame,
            text="Key Metrics",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Metrics container (grid layout)
        self.metrics_container = ttk.Frame(metrics_frame)
        self.metrics_container.pack()
        
        # Create metric cards
        self.metric_cards = {
            'price': MetricCard(
                self.metrics_container,
                title="Current Price",
                value="--",
                suffix="$"
            ),
            'market_cap': MetricCard(
                self.metrics_container,
                title="Market Cap",
                value="--",
                suffix="B"
            ),
            'pe_ratio': MetricCard(
                self.metrics_container,
                title="P/E Ratio",
                value="--"
            ),
            'volume': MetricCard(
                self.metrics_container,
                title="Volume",
                value="--",
                suffix="M"
            )
        }
        
        # Arrange in grid
        self.metric_cards['price'].grid(row=0, column=0, padx=10, pady=10)
        self.metric_cards['market_cap'].grid(row=0, column=1, padx=10, pady=10)
        self.metric_cards['pe_ratio'].grid(row=1, column=0, padx=10, pady=10)
        self.metric_cards['volume'].grid(row=1, column=1, padx=10, pady=10)
    
    def _setup_charts_tab(self):
        """Setup charts tab with stock chart"""
        charts_frame = self.tab_manager.get_tab_frame('Charts')
        
        # Create chart
        self.stock_chart = StockChart(
            charts_frame,
            title="Stock Price History"
        )
        self.stock_chart.pack(fill='both', expand=True, padx=20, pady=20)
    
    def _setup_financials_tab(self):
        """Setup financials tab with financial analysis - CLEAN VERSION"""
        financials_frame = self.tab_manager.get_tab_frame('Financials')
        
        # CLEAR ANY EXISTING PLACEHOLDER CONTENT
        for widget in financials_frame.winfo_children():
            widget.destroy()
        
        # Define theme colors for FinancialsManager
        theme_colors = {
            'bg': '#333333',
            'frame': '#444444', 
            'text': '#e0e0e0',
            'header': '#6ea3d8',
            'success': '#5a9c5a',
            'error': '#d16a6a',
            'warning': '#d8a062',
            'button': '#8a8a8a',
            'button_text': '#2a2a2a',
            'accent': '#8a8a8a'
        }
        
        # Create FinancialsManager with the financials tab frame as parent
        self.financials_manager = FinancialsManager(
            parent=financials_frame,
            theme_colors=theme_colors,
            event_bus=self.event_bus
        )
        
    # NO .pack() NEEDED - FinancialsManager creates content directly in parent
    def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        # Show spinner when fetching starts
        self.event_bus.subscribe(
            EventType.DATA_FETCH_STARTED,
            self._show_loading
        )
        
        # Hide spinner when fetching completes
        self.event_bus.subscribe(
            EventType.DATA_FETCH_COMPLETED,
            self._hide_loading
        )
        
        # Update UI when analysis completes
        self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED,
            self._update_ui
        )
    
    def _show_loading(self, event):
        """Show loading state by disabling individual tabs"""
        for i in range(len(self.tab_manager.tabs())):
            self.tab_manager.tab(i, state='disabled')
    
    def _hide_loading(self, event):
        """Hide loading state by enabling individual tabs"""
        for i in range(len(self.tab_manager.tabs())):
            self.tab_manager.tab(i, state='normal')
            
    def _update_ui(self, event):
        """Update UI with analysis results"""
        data = event.data
        
        # Update metric cards
        if 'metrics' in data:
            metrics = data['metrics']
            
            # Update price card
            if 'price' in metrics:
                self.metric_cards['price'].update_value(
                    f"{metrics['price']:.2f}",
                    trend='up' if metrics.get('price_change', 0) > 0 else 'down'
                )
            
            # Update market cap
            if 'market_cap' in metrics:
                # Convert to billions
                market_cap_b = metrics['market_cap'] / 1e9
                self.metric_cards['market_cap'].update_value(
                    f"{market_cap_b:.2f}"
                )
            
            # Update P/E ratio
            if 'pe_ratio' in metrics:
                self.metric_cards['pe_ratio'].update_value(
                    f"{metrics['pe_ratio']:.2f}"
                )
            
            # Update volume
            if 'volume' in metrics:
                # Convert to millions
                volume_m = metrics['volume'] / 1e6
                self.metric_cards['volume'].update_value(
                    f"{volume_m:.2f}"
                )
        
        # Update chart
        if 'price_history' in data:
            history = data['price_history']
            self.stock_chart.update_data(
                dates=history['dates'],
                prices=history['prices'],
                label=data.get('ticker', 'Stock')
            )
        
        # Schedule a delayed refresh for the current tab
        self.tab_manager.after(100, self.tab_manager._refresh_current_tab)