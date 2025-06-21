# components/analyzer.py - Fixed to use net_income instead of earnings
from core.event_system import EventBus, Event, EventType
import tkinter as tk
from tkinter import ttk

class Analyzer:
    """Component to analyze stock data and display insights"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.container = None
        self.analysis_text = None
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.analyze_data)
        self.event_bus.subscribe(EventType.TAB_CHANGED, self.on_tab_changed)
        
        print("StockAnalyzer initialized")
        
    def set_container(self, container):
        """Set the container widget where analysis will be displayed"""
        self.container = container
        self._create_analysis_widgets()
        
    def _create_analysis_widgets(self):
        """Create analysis display widgets"""
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
            text="Stock Analysis", 
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Analysis text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Text widget
        self.analysis_text = tk.Text(
            text_frame,
            wrap='word',
            yscrollcommand=scrollbar.set,
            font=('Arial', 11),
            bg='white',
            fg='black'
        )
        self.analysis_text.pack(side='left', fill='both', expand=True)
        
        scrollbar.config(command=self.analysis_text.yview)
        
        # Initial message
        self.analysis_text.insert('1.0', "Select a stock to see analysis here...")
        self.analysis_text.config(state='disabled')
        
    def analyze_data(self, event: Event):
        """Analyze the received stock data"""
        stock_data = event.data['stock_data']
        print(f"Analyzer: Analyzing data for {stock_data.ticker}")
        
        # Perform analysis
        analysis = self._perform_analysis(stock_data)
        
        # Display analysis
        if self.analysis_text:
            self.analysis_text.config(state='normal')
            self.analysis_text.delete('1.0', 'end')
            self.analysis_text.insert('1.0', analysis)
            self.analysis_text.config(state='disabled')
        
        # Publish analysis completed event
        self.event_bus.publish(Event(
            type=EventType.ANALYSIS_COMPLETED,
            data={'ticker': stock_data.ticker, 'analysis': analysis}
        ))
        
    def _perform_analysis(self, stock_data):
        """Perform actual stock analysis"""
        analysis_parts = []
        
        # Header
        analysis_parts.append(f"ANALYSIS FOR {stock_data.ticker} - {stock_data.company_name}")
        analysis_parts.append("=" * 50)
        analysis_parts.append("")
        
        # Current valuation
        analysis_parts.append("CURRENT VALUATION:")
        analysis_parts.append(f"• Current Price: ${stock_data.current_price:.2f}")
        analysis_parts.append(f"• Market Cap: ${stock_data.market_cap:,.0f}")
        if stock_data.pe_ratio:
            analysis_parts.append(f"• P/E Ratio: {stock_data.pe_ratio:.1f}")
        analysis_parts.append("")
        
        # Price movement analysis
        analysis_parts.append("PRICE MOVEMENT:")
        change_direction = "increased" if stock_data.price_change > 0 else "decreased" if stock_data.price_change < 0 else "unchanged"
        analysis_parts.append(f"• Stock has {change_direction} by ${stock_data.price_change:.2f} ({stock_data.price_change_percent:.2f}%)")
        
        if abs(stock_data.price_change_percent) > 5:
            analysis_parts.append("• This is a significant price movement (>5%)")
        elif abs(stock_data.price_change_percent) > 2:
            analysis_parts.append("• This is a moderate price movement (2-5%)")
        else:
            analysis_parts.append("• This is a minor price movement (<2%)")
        analysis_parts.append("")
        
        # Financial analysis
        if stock_data.quarterly_financials:
            analysis_parts.append("FINANCIAL PERFORMANCE:")
            latest = stock_data.quarterly_financials[-1]
            
            analysis_parts.append(f"• Latest Quarter Revenue: ${latest.revenue:,.0f}")
            analysis_parts.append(f"• Latest Quarter Net Income: ${latest.net_income:,.0f}")  # FIXED: earnings -> net_income
            analysis_parts.append(f"• Latest Quarter EPS: ${latest.eps:.2f}")
            
            # Revenue trend analysis
            if len(stock_data.quarterly_financials) >= 2:
                prev = stock_data.quarterly_financials[-2]
                revenue_growth = ((latest.revenue - prev.revenue) / prev.revenue * 100) if prev.revenue else 0
                earnings_growth = ((latest.net_income - prev.net_income) / prev.net_income * 100) if prev.net_income else 0  # FIXED: earnings -> net_income
                
                analysis_parts.append(f"• Quarter-over-quarter revenue growth: {revenue_growth:.1f}%")
                analysis_parts.append(f"• Quarter-over-quarter earnings growth: {earnings_growth:.1f}%")
                
                if revenue_growth > 10:
                    analysis_parts.append("• Strong revenue growth indicates healthy business expansion")
                elif revenue_growth > 0:
                    analysis_parts.append("• Positive revenue growth shows steady business performance")
                else:
                    analysis_parts.append("• Declining revenue may indicate business challenges")
                    
            analysis_parts.append("")
            
        # Valuation assessment
        analysis_parts.append("VALUATION ASSESSMENT:")
        if stock_data.pe_ratio:
            if stock_data.pe_ratio < 15:
                analysis_parts.append("• P/E ratio suggests the stock may be undervalued")
            elif stock_data.pe_ratio > 25:
                analysis_parts.append("• P/E ratio suggests the stock may be overvalued")
            else:
                analysis_parts.append("• P/E ratio appears to be in a reasonable range")
        else:
            analysis_parts.append("• P/E ratio not available for valuation assessment")
            
        analysis_parts.append("")
        
        # Price history analysis - REMOVED daily_prices section since we don't have it
        # (This was causing issues because StockData no longer has daily_prices)
        
        analysis_parts.append("")
        analysis_parts.append("Note: This is a basic analysis for informational purposes only.")
        analysis_parts.append("Always consult with financial professionals before making investment decisions.")
        
        return "\n".join(analysis_parts)
        
    def on_tab_changed(self, event: Event):
        """Handle tab change events"""
        if event.data.get('tab') == 'Analysis' and self.container:
            # Refresh the display when switching to Analysis tab
            self.container.update_idletasks()