# components/metrics_display.py - Fixed to use net_income instead of earnings
from core.event_system import EventBus, Event, EventType
from ui.widgets.metric_card import MetricCard
import tkinter as tk
from tkinter import ttk

class MetricsDisplay:
    """Component to display key financial metrics"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.metric_cards = {}
        self.container = None
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.update_metrics)
        self.event_bus.subscribe(EventType.TAB_CHANGED, self.on_tab_changed)
        
        print("MetricsDisplay initialized")
        
    def set_container(self, container):
        """Set the container widget where metrics will be displayed"""
        self.container = container
        self._create_metric_widgets()
        
    def _create_metric_widgets(self):
        """Create the metric card widgets"""
        if not self.container:
            return
            
        # Clear existing widgets
        for widget in self.container.winfo_children():
            widget.destroy()
            
        # Create main frame
        main_frame = ttk.Frame(self.container)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Key Metrics", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Metrics grid
        metrics_frame = ttk.Frame(main_frame)
        metrics_frame.pack(fill='both', expand=True)
        
        # Create metric cards
        self.metric_cards = {
            'price': MetricCard(metrics_frame, title="Current Price", value="--", suffix="$"),
            'change': MetricCard(metrics_frame, title="Price Change", value="--", suffix="%"),
            'market_cap': MetricCard(metrics_frame, title="Market Cap", value="--", suffix="B"),
            'pe_ratio': MetricCard(metrics_frame, title="P/E Ratio", value="--"),
            'revenue': MetricCard(metrics_frame, title="Latest Revenue", value="--", suffix="M"),
            'earnings': MetricCard(metrics_frame, title="Latest Net Income", value="--", suffix="M")  # Updated title for clarity
        }
        
        # Grid layout (2x3)
        row = 0
        col = 0
        for card in self.metric_cards.values():
            card.grid(row=row, column=col, padx=10, pady=10, sticky='ew')
            col += 1
            if col >= 3:
                col = 0
                row += 1
                
        # Configure grid weights
        for i in range(3):
            metrics_frame.columnconfigure(i, weight=1)
            
    def update_metrics(self, event: Event):
        """Update metrics display with new stock data"""
        stock_data = event.data['stock_data']
        print(f"MetricsDisplay: Updating metrics for {stock_data.ticker}")
        
        if not self.metric_cards:
            return
            
        # Update price
        self.metric_cards['price'].update_value(
            f"{stock_data.current_price:.2f}",
            'up' if stock_data.price_change > 0 else 'down' if stock_data.price_change < 0 else None
        )
        
        # Update price change
        change_color = 'up' if stock_data.price_change_percent > 0 else 'down' if stock_data.price_change_percent < 0 else None
        self.metric_cards['change'].update_value(
            f"{stock_data.price_change_percent:.2f}",
            change_color
        )
        
        # Update market cap (convert to billions)
        market_cap_b = stock_data.market_cap / 1e9 if stock_data.market_cap else 0
        self.metric_cards['market_cap'].update_value(f"{market_cap_b:.1f}")
        
        # Update P/E ratio
        pe_value = f"{stock_data.pe_ratio:.1f}" if stock_data.pe_ratio else "N/A"
        self.metric_cards['pe_ratio'].update_value(pe_value)
        
        # Update revenue and earnings from latest quarter
        if stock_data.quarterly_financials:
            latest = stock_data.quarterly_financials[-1]
            
            # Revenue in millions
            revenue_m = latest.revenue / 1e6 if latest.revenue else 0
            self.metric_cards['revenue'].update_value(f"{revenue_m:.0f}")
            
            # Net Income in millions - FIXED: earnings -> net_income
            earnings_m = latest.net_income / 1e6 if latest.net_income else 0
            earnings_trend = 'up' if latest.net_income > 0 else 'down' if latest.net_income < 0 else None
            self.metric_cards['earnings'].update_value(f"{earnings_m:.0f}", earnings_trend)
        else:
            self.metric_cards['revenue'].update_value("N/A")
            self.metric_cards['earnings'].update_value("N/A")
            
    def on_tab_changed(self, event: Event):
        """Handle tab change events"""
        if event.data.get('tab') == 'Overview' and self.container:
            # Refresh the display when switching to Overview tab
            self.container.update_idletasks()