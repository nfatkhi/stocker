# components/chart_manager.py - Enhanced with Integrated Live Price Indicator
from core.event_system import EventBus, Event, EventType
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import mplfinance as mpf
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta, time as dt_time
import threading
import math
import warnings
import requests
import json
import time
import pytz
from dataclasses import dataclass
from typing import Optional, Tuple

# Suppress mplfinance warnings
warnings.filterwarnings('ignore', message='.*too much data.*')


@dataclass
class LivePriceData:
    """Data structure for live price information"""
    current_price: float
    price_change_1h: float
    price_change_1h_percent: float
    market_status: str  # 'open', 'closed', 'premarket', 'afterhours'
    last_update: datetime
    volume_1h: Optional[int] = None


class EnhancedChartManager:
    """Enhanced chart manager with integrated live price indicator and market status"""
    
    def __init__(self, event_bus: EventBus, api_keys: dict = None):
        self.event_bus = event_bus
        self.containers = {}
        self.current_stock_data = None
        self.charts_created = False
        self.ticker_symbol = None
        
        # Chart data and components
        self.canvas = None
        self.main_ax = None
        self.volume_ax = None
        self.rsi_ax = None
        self.chart_data = None
        self.figure = None
        
        # Mode tracking for live hourly charts
        self.current_mode = 'daily'  # 'daily' or 'hourly'
        self.live_update_timer = None
        self.live_update_active = False
        
        # API keys from config
        self.api_keys = api_keys or {}
        self.polygon_api_key = self.api_keys.get('polygon', 'DEMO')
        self.alpha_vantage_key = self.api_keys.get('alpha_vantage', 'DEMO')
        
        # Live price tracking (ENHANCED)
        self.live_price_data = LivePriceData(
            current_price=0,
            price_change_1h=0,
            price_change_1h_percent=0,
            market_status='closed',
            last_update=datetime.now()
        )
        
        # Market timezone
        self.eastern_tz = pytz.timezone('US/Eastern')
        
        # Interactive elements for crosshair
        self.horiz_line = None
        self.vert_line_main = None
        self.vert_line_volume = None
        self.vert_line_rsi = None
        self.price_annotation = None
        self.date_annotation = None
        self.main_background = None
        self.volume_background = None
        self.rsi_background = None
        
        # Live price indicator elements (ENHANCED)
        self.live_price_line = None
        self.live_price_text = None
        self.market_status_indicator = None
        
        # Pan and zoom functionality
        self.pan_active = False
        self.pan_start_x = None
        self.pan_start_xlim = None
        self.zoom_sensitivity = 0.1
        
        # Y-axis drag functionality
        self.y_drag_active = False
        self.y_drag_start_y = None
        self.y_drag_start_ylim = None
        self.y_drag_chart = None
        
        # UI colors (matching Stocker theme)
        self.BG_COLOR = '#333333'
        self.FRAME_COLOR = '#444444'
        self.TEXT_COLOR = '#e0e0e0'
        self.HEADER_COLOR = '#6ea3d8'
        self.SUCCESS_COLOR = '#5a9c5a'
        self.ERROR_COLOR = '#d16a6a'
        self.WARNING_COLOR = '#d8a062'
        self.BUTTON_COLOR = '#8a8a8a'
        self.BUTTON_TEXT_COLOR = '#2a2a2a'
        
        # Live price indicator colors (NEW)
        self.LIVE_PRICE_COLOR = '#00ff00'
        self.MARKET_OPEN_COLOR = '#5a9c5a'
        self.MARKET_CLOSED_COLOR = '#8a8a8a'
        self.PREMARKET_COLOR = '#d8a062'
        self.AFTERHOURS_COLOR = '#6ea3d8'
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.update_charts)
        self.event_bus.subscribe(EventType.TAB_CHANGED, self.on_tab_changed)
        
    def set_container(self, tab_name, container):
        """Set container for a specific tab"""
        self.containers[tab_name] = container
        
    def on_tab_changed(self, event: Event):
        """Handle tab change events"""
        tab_name = event.data.get('tab')
        
        if tab_name == 'Charts':
            container = self.containers.get('Charts')
            if container and not self.charts_created:
                container.after(200, lambda: self._create_enhanced_charts(container))
            elif self.charts_created and self.current_stock_data:
                self._update_existing_charts()
                
    def _create_enhanced_charts(self, container):
        """Create sophisticated charts with live price indicator"""
        # Force container update
        container.update()
        container.update_idletasks()
        
        # Check container size
        width = container.winfo_width()
        height = container.winfo_height()
        
        if width <= 1 or height <= 1:
            container.after(100, lambda: self._create_enhanced_charts(container))
            return
            
        # Clear existing widgets
        for widget in container.winfo_children():
            widget.destroy()
            
        # Create main frame
        main_frame = tk.Frame(container, bg=self.FRAME_COLOR)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create chart controls
        self._create_chart_controls(main_frame)
        
        # Create chart frame
        self.chart_frame = tk.Frame(main_frame, bg=self.FRAME_COLOR)
        self.chart_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        self.charts_created = True
        
        # Update with existing data if available
        if self.current_stock_data:
            self._start_chart_update()
        else:
            self._show_no_data_message()
            
    def _create_chart_controls(self, parent):
        """Create chart control buttons and info display"""
        controls_frame = tk.Frame(parent, bg=self.FRAME_COLOR)
        controls_frame.pack(fill='x', pady=(0, 5))
        
        # Chart title with live price info
        self.chart_title = tk.Label(
            controls_frame, 
            text="Interactive Price Chart with Live Updates", 
            font=('Arial', 14, 'bold'), 
            bg=self.FRAME_COLOR, 
            fg=self.HEADER_COLOR
        )
        self.chart_title.pack(side='left')
        
        # Market status indicator (NEW)
        self.market_status_label = tk.Label(
            controls_frame,
            text="MARKET: CLOSED",
            font=('Arial', 10, 'bold'),
            bg=self.FRAME_COLOR,
            fg=self.MARKET_CLOSED_COLOR,
            padx=10
        )
        self.market_status_label.pack(side='left', padx=(20, 0))
        
        # Timeframe buttons
        timeframe_frame = tk.Frame(controls_frame, bg=self.FRAME_COLOR)
        timeframe_frame.pack(side='right', padx=(0, 10))
        
        timeframes = [
            ('1D', 'hourly'), ('1M', 21), ('3M', 63), ('6M', 126), 
            ('1Y', 252), ('2Y', 504), ('5Y', -1)
        ]
        
        self.timeframe_buttons = {}
        for text, period in timeframes:
            if text == '1D':
                btn = tk.Button(
                    timeframe_frame, text=text, 
                    command=lambda: self.switch_to_hourly_mode(),
                    font=('Arial', 9), bg=self.BUTTON_COLOR, fg=self.BUTTON_TEXT_COLOR,
                    relief='flat', padx=8, pady=2, state='disabled'
                )
            else:
                btn = tk.Button(
                    timeframe_frame, text=text, 
                    command=lambda d=period: self.zoom_to_period(d),
                    font=('Arial', 9), bg=self.BUTTON_COLOR, fg=self.BUTTON_TEXT_COLOR,
                    relief='flat', padx=8, pady=2, state='disabled'
                )
            btn.pack(side='left', padx=1)
            self.timeframe_buttons[text] = btn
            
        # Cursor info display
        cursor_frame = tk.Frame(parent, bg=self.FRAME_COLOR)
        cursor_frame.pack(fill='x')
        
        self.cursor_info_text = tk.Text(
            cursor_frame, height=1, font=('Arial', 9),
            bg=self.FRAME_COLOR, fg=self.TEXT_COLOR, relief='flat', bd=0,
            highlightthickness=0, wrap='none', state='disabled'
        )
        self.cursor_info_text.pack(fill='x')
        
        # Configure text tags for colored output
        self.cursor_info_text.tag_config('green', foreground=self.SUCCESS_COLOR)
        self.cursor_info_text.tag_config('red', foreground=self.ERROR_COLOR)
        self.cursor_info_text.tag_config('neutral', foreground=self.TEXT_COLOR)
        
    def update_charts(self, event: Event):
        """Update charts with new stock data"""            
        stock_data = event.data.get('stock_data')
        if not stock_data:
            return
            
        self.current_stock_data = stock_data
        self.ticker_symbol = stock_data.ticker
        
        # Update chart title immediately if possible
        if hasattr(self, 'chart_title'):
            self.chart_title.config(text=f"{stock_data.ticker} - Interactive Chart with Live Updates")
        
        # Start live price updates
        self._start_live_price_updates()
        
        # If charts are already created, start the update process
        if self.charts_created:
            self._start_chart_update()
            
    def _update_existing_charts(self):
        """Update existing charts with current stock data"""
        if self.charts_created and self.current_stock_data:
            self._start_chart_update()
            
    def _start_chart_update(self):
        """Start the chart update process"""
        if not hasattr(self, 'chart_frame'):
            return
            
        # Show loading message
        self._show_loading_chart()
        
        # Fetch detailed OHLCV data in background
        if self.current_stock_data and hasattr(self.current_stock_data, 'ticker'):
            threading.Thread(
                target=self._fetch_and_update_chart, 
                args=(self.current_stock_data.ticker,), 
                daemon=True
            ).start()
            
    def _fetch_and_update_chart(self, ticker):
        """Fetch OHLCV data and update chart (runs in background thread)"""
        try:
            # Check if we're in hourly mode and should fetch hourly data
            if self.current_mode == 'hourly':
                success = self._fetch_hourly_data_internal(ticker)
                if success:
                    return
                # If hourly fetch fails, continue to daily data below
            
            # Fetch daily data (default or fallback)
            stock = yf.Ticker(ticker)
            hist_data = stock.history(period='5y', interval='1d', auto_adjust=True)
            
            if hist_data is not None and not hist_data.empty:
                # Clean the data
                if isinstance(hist_data.columns, pd.MultiIndex):
                    hist_data.columns = hist_data.columns.get_level_values(0)
                    
                # Ensure we have required columns
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                if all(col in hist_data.columns for col in required_columns):
                    # Clean numeric data
                    for col in required_columns:
                        hist_data[col] = pd.to_numeric(hist_data[col], errors='coerce')
                    
                    hist_data = hist_data.dropna()
                    
                    if len(hist_data) > 2:
                        self.chart_data = hist_data
                        
                        # Schedule chart creation on main thread
                        if hasattr(self, 'chart_frame'):
                            try:
                                root = self.chart_frame.winfo_toplevel()
                                root.after(0, self._create_sophisticated_chart)
                            except Exception as e:
                                print(f"Error scheduling chart creation: {e}")
                        return
                        
        except Exception as e:
            print(f"Error fetching chart data: {e}")
            
        # Fallback to simple chart if everything fails
        try:
            root = self.chart_frame.winfo_toplevel()
            root.after(0, self._show_chart_error)
        except Exception as e:
            print(f"Error showing error message: {e}")

    def _fetch_hourly_data_internal(self, ticker):
        """Internal method to fetch hourly data - Polygon only"""
        try:
            # Method 1: Try Polygon.io if we have a real API key
            if self.polygon_api_key != 'DEMO':
                if self._try_polygon_hourly(ticker):
                    return True
                    
            # Method 2: Fall back to yfinance only (no Alpha Vantage)
            periods_to_try = ['5d', '1mo', '2mo']
            
            for period in periods_to_try:
                try:
                    stock = yf.Ticker(ticker)
                    hist_data = stock.history(period=period, interval='1h', auto_adjust=True)
                    
                    if hist_data is not None and not hist_data.empty:
                        # Clean the data
                        if isinstance(hist_data.columns, pd.MultiIndex):
                            hist_data.columns = hist_data.columns.get_level_values(0)
                            
                        # Ensure we have required columns
                        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                        
                        if all(col in hist_data.columns for col in required_columns):
                            # Clean numeric data
                            for col in required_columns:
                                hist_data[col] = pd.to_numeric(hist_data[col], errors='coerce')
                            
                            hist_data = hist_data.dropna()
                            
                            # Filter to recent data if we got too much
                            if len(hist_data) > 200:
                                hist_data = hist_data.tail(200)
                            
                            if len(hist_data) > 10:  # Need at least 10 hours
                                self.chart_data = hist_data
                                
                                # Schedule chart creation on main thread
                                if hasattr(self, 'chart_frame'):
                                    try:
                                        root = self.chart_frame.winfo_toplevel()
                                        root.after(0, self._create_sophisticated_chart)
                                        return True
                                    except Exception as e:
                                        print(f"Error scheduling hourly chart: {e}")
                                        
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            print(f"Error in _fetch_hourly_data_internal: {e}")
            return False
            
    def _try_polygon_hourly(self, ticker):
        """Try to fetch hourly data from Polygon.io"""
        try:
            # Calculate date range (2 weeks back for extended hours)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=14)
            
            # Format dates for Polygon API
            from_date = start_date.strftime('%Y-%m-%d')
            to_date = end_date.strftime('%Y-%m-%d')
            
            # Polygon.io aggregates endpoint for hourly data
            url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/hour/{from_date}/{to_date}"
            params = {
                'adjusted': 'true',
                'sort': 'asc',
                'apikey': self.polygon_api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Accept both 'OK' and 'DELAYED' status
                if (data.get('status') in ['OK', 'DELAYED']) and 'results' in data and data['results']:
                    results = data['results']
                    
                    if len(results) > 10:
                        # Convert Polygon data to pandas DataFrame
                        df_data = []
                        for bar in results:
                            # Polygon timestamp is in milliseconds
                            dt = datetime.fromtimestamp(bar['t'] / 1000)
                            df_data.append({
                                'Open': bar['o'],
                                'High': bar['h'], 
                                'Low': bar['l'],
                                'Close': bar['c'],
                                'Volume': bar['v']
                            })
                        
                        # Create DataFrame with datetime index
                        hist_data = pd.DataFrame(df_data)
                        hist_data.index = [datetime.fromtimestamp(bar['t'] / 1000) for bar in results]
                        hist_data.index.name = 'Datetime'
                        
                        # Clean numeric data
                        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                            hist_data[col] = pd.to_numeric(hist_data[col], errors='coerce')
                        
                        hist_data = hist_data.dropna()
                        
                        if len(hist_data) > 10:
                            self.chart_data = hist_data
                            
                            # Schedule chart creation on main thread
                            if hasattr(self, 'chart_frame'):
                                try:
                                    root = self.chart_frame.winfo_toplevel()
                                    root.after(0, self._create_sophisticated_chart)
                                    return True
                                except Exception as e:
                                    print(f"Error scheduling Polygon chart: {e}")
                        
        except Exception as e:
            print(f"Error fetching from Polygon.io: {e}")
            
        return False
            
    def _show_loading_chart(self):
        """Show loading message in chart area"""
        if not hasattr(self, 'chart_frame'):
            return
            
        # Clear existing widgets
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        loading_label = tk.Label(
            self.chart_frame, 
            text=f"Loading {'hourly' if self.current_mode == 'hourly' else 'daily'} chart data for {self.ticker_symbol}...",
            font=('Arial', 12), bg=self.FRAME_COLOR, fg=self.TEXT_COLOR
        )
        loading_label.pack(expand=True)
        
    def _show_chart_error(self):
        """Show chart error message"""
        if not hasattr(self, 'chart_frame'):
            return
            
        # Clear existing widgets
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        error_label = tk.Label(
            self.chart_frame, 
            text=f"Failed to load chart data for {self.ticker_symbol}\n\nPlease try again or select a different stock.",
            font=('Arial', 12), bg=self.FRAME_COLOR, fg=self.ERROR_COLOR,
            justify='center'
        )
        error_label.pack(expand=True)
        
    def _create_sophisticated_chart(self):
        """Create sophisticated candlestick chart with RSI and live price indicator"""
        if not hasattr(self, 'chart_frame') or self.chart_data is None or self.chart_data.empty:
            return
            
        try:
            # Clear existing widgets
            for widget in self.chart_frame.winfo_children():
                widget.destroy()
                
            # Update chart title with current mode
            if hasattr(self, 'chart_title'):
                if self.current_mode == 'hourly':
                    self.chart_title.config(text=f"{self.ticker_symbol} - Hourly Chart with Live Updates")
                else:
                    self.chart_title.config(text=f"{self.ticker_symbol} - Daily Chart with Live Updates")
                
            # Create mplfinance style
            mc = mpf.make_marketcolors(
                up=self.SUCCESS_COLOR, down=self.ERROR_COLOR,
                edge='inherit', wick='inherit',
                volume={'up': self.SUCCESS_COLOR, 'down': self.ERROR_COLOR}
            )
            
            style = mpf.make_mpf_style(
                base_mpl_style="dark_background",
                marketcolors=mc,
                facecolor=self.FRAME_COLOR,
                gridcolor="#555555",
                y_on_right=True
            )
            
            # Create figure with volume and RSI subplots
            self.figure = mpf.figure(style=style, figsize=(12, 10), facecolor=self.FRAME_COLOR)
            gs = self.figure.add_gridspec(3, 1, hspace=0.05, height_ratios=[5.3, 1.35, 1.35])
            self.main_ax = self.figure.add_subplot(gs[0, 0])
            self.volume_ax = self.figure.add_subplot(gs[1, 0], sharex=self.main_ax)
            self.rsi_ax = self.figure.add_subplot(gs[2, 0], sharex=self.main_ax)
            
            # Configure axes - Y-axis on right side
            self.main_ax.spines['bottom'].set_visible(False)
            self.main_ax.yaxis.tick_right()
            self.main_ax.yaxis.set_label_position('right')
            
            self.volume_ax.tick_params(axis='x', labelbottom=False)
            self.volume_ax.yaxis.tick_right()
            self.volume_ax.yaxis.set_label_position('right')
            
            self.rsi_ax.tick_params(axis='x', labelbottom=True)
            self.rsi_ax.yaxis.tick_right()
            self.rsi_ax.yaxis.set_label_position('right')
            
            # Plot candlestick chart with moving averages
            mav_list = None
            if len(self.chart_data) > 200:
                mav_list = (20, 50, 200)
            elif len(self.chart_data) > 50:
                mav_list = (20, 50)
            elif len(self.chart_data) > 20:
                mav_list = (20,)
            
            # Create plot arguments
            plot_kwargs = {
                'type': 'candle',
                'ax': self.main_ax,
                'volume': self.volume_ax,
                'style': style,
                'warn_too_much_data': 2000
            }
            
            # Only add mav if we have valid periods
            if mav_list is not None:
                plot_kwargs['mav'] = mav_list
            
            mpf.plot(self.chart_data, **plot_kwargs)
            
            # Plot RSI
            self._plot_rsi()
            
            # Optimize y-axis scaling
            price_low = self.chart_data['Low'].min()
            price_high = self.chart_data['High'].max()
            price_range = price_high - price_low
            buffer = price_range * 0.02
            
            self.main_ax.set_ylim(price_low - buffer, price_high + buffer)
            
            # Optimize volume chart scaling
            volume_max = self.chart_data['Volume'].max()
            self.volume_ax.set_ylim(0, volume_max * 1.05)
            
            # Add moving average legend
            if mav_list and len(self.main_ax.get_lines()) > 1:
                ma_lines = self.main_ax.get_lines()[-len(mav_list):]
                ma_labels = [f'MA {m}' for m in mav_list]
                self.main_ax.legend(ma_lines, ma_labels, loc='upper left')
            
            # Setup interactive crosshair elements
            self._setup_crosshair_elements()
            
            # Setup live price indicator elements (NEW)
            self._setup_live_price_elements()
            
            # Style the axes
            self.figure.set_facecolor(self.FRAME_COLOR)
            for ax in [self.main_ax, self.volume_ax, self.rsi_ax]:
                ax.tick_params(colors=self.TEXT_COLOR)
                for label in (ax.get_xticklabels() + ax.get_yticklabels()):
                    label.set_color(self.TEXT_COLOR)
                ax.yaxis.label.set_color(self.TEXT_COLOR)
                ax.xaxis.label.set_color(self.TEXT_COLOR)
            
            # Remove x-axis labels for cleaner look (except RSI)
            self.main_ax.set_xticklabels([])
            self.volume_ax.set_xticklabels([])
            
            self.figure.subplots_adjust(left=0.02, right=0.92, top=0.98, bottom=0.02, hspace=0.15)
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill='both', expand=True)
            
            # Add navigation toolbar
            toolbar = NavigationToolbar2Tk(self.canvas, self.chart_frame, pack_toolbar=False)
            toolbar.config(background=self.FRAME_COLOR)
            toolbar.update()
            toolbar.pack(side='bottom', fill='x')
            
            # Connect interactive events
            self.canvas.mpl_connect('draw_event', self.on_draw)
            self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            
            # Add pan and zoom events
            self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
            self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
            self.canvas.mpl_connect('scroll_event', self.on_scroll)
            
            # Enable timeframe buttons
            for btn in self.timeframe_buttons.values():
                btn.config(state='normal')
            
            # Default zoom
            if self.current_mode == 'daily':
                self.zoom_to_period(252)  # 1 year default for daily
            
            # Publish chart ready event (NEW)
            self.event_bus.publish(Event(
                type=EventType.CHART_READY,
                data={
                    'ticker': self.ticker_symbol,
                    'chart_manager': self
                }
            ))
            
        except Exception as e:
            print(f"Error creating sophisticated chart: {e}")
            self._show_chart_error()
            
    def _setup_live_price_elements(self):
        """Setup live price indicator elements on the chart (NEW)"""
        try:
            if not self.main_ax:
                return
                
            # Create live price line (will be positioned when price data arrives)
            self.live_price_line = self.main_ax.axhline(
                y=0,  # Will be updated with actual price
                color=self.LIVE_PRICE_COLOR,
                linestyle='--',
                linewidth=2,
                alpha=0.8,
                visible=False,  # Hidden until we have price data
                zorder=100
            )
            
            # Reset live price text element
            self.live_price_text = None
            
        except Exception as e:
            print(f"Error setting up live price elements: {e}")
            
    def _start_live_price_updates(self):
        """Start live price updates for the current ticker (NEW)"""
        if not self.ticker_symbol:
            return
            
        self.live_update_active = True
        self._fetch_live_price_data()
        self._schedule_next_live_update()
        
    def _fetch_live_price_data(self):
        """Fetch live price data in background thread (NEW)"""
        if not self.ticker_symbol or not self.live_update_active:
            return
            
        threading.Thread(
            target=self._fetch_live_price_worker,
            daemon=True
        ).start()
        
    def _fetch_live_price_worker(self):
        """Worker thread to fetch live price data (NEW)"""
        try:
            # Get current market status
            market_status = self._get_market_status()
            
            # Fetch current price and 1-hour data
            current_price, price_1h_ago = self._fetch_price_comparison()
            
            if current_price is not None:
                # Calculate 1-hour change
                if price_1h_ago is not None:
                    price_change_1h = current_price - price_1h_ago
                    price_change_1h_percent = (price_change_1h / price_1h_ago) * 100 if price_1h_ago != 0 else 0
                else:
                    price_change_1h = 0
                    price_change_1h_percent = 0
                
                # Update live price data
                self.live_price_data = LivePriceData(
                    current_price=current_price,
                    price_change_1h=price_change_1h,
                    price_change_1h_percent=price_change_1h_percent,
                    market_status=market_status,
                    last_update=datetime.now()
                )
                
                # Update UI on main thread
                if hasattr(self, 'chart_frame'):
                    try:
                        root = self.chart_frame.winfo_toplevel()
                        root.after(0, self._update_live_price_display)
                    except:
                        pass
                        
                # Publish live price update event
                self.event_bus.publish(Event(
                    type=EventType.LIVE_PRICE_UPDATED,
                    data={
                        'ticker': self.ticker_symbol,
                        'live_data': self.live_price_data
                    }
                ))
                
        except Exception as e:
            print(f"Error fetching live price data: {e}")
            
    def _fetch_price_comparison(self) -> Tuple[Optional[float], Optional[float]]:
        """Fetch current price and 1-hour ago price (NEW)"""
        try:
            stock = yf.Ticker(self.ticker_symbol)
            
            # Get 1-day minute data to have current price and 1h ago
            minute_data = stock.history(period='1d', interval='1m')
            
            if minute_data.empty:
                return None, None
                
            current_price = minute_data['Close'].iloc[-1]
            
            # Get price from 1 hour ago (60 minutes)
            if len(minute_data) >= 60:
                price_1h_ago = minute_data['Close'].iloc[-60]
            else:
                # If we don't have 60 minutes, use the earliest available
                price_1h_ago = minute_data['Close'].iloc[0]
                
            return float(current_price), float(price_1h_ago)
            
        except Exception as e:
            print(f"Error fetching price comparison: {e}")
            return None, None
            
    def _get_market_status(self) -> str:
        """Determine current market status (NEW)"""
        try:
            # Get current Eastern time
            eastern_now = datetime.now(self.eastern_tz)
            current_time = eastern_now.time()
            current_weekday = eastern_now.weekday()  # 0=Monday, 6=Sunday
            
            # Market is closed on weekends
            if current_weekday >= 5:  # Saturday or Sunday
                return 'closed'
            
            # Define market hours (Eastern time)
            premarket_start = dt_time(4, 0)    # 4:00 AM
            market_open = dt_time(9, 30)       # 9:30 AM
            market_close = dt_time(16, 0)      # 4:00 PM
            afterhours_end = dt_time(20, 0)    # 8:00 PM
            
            if premarket_start <= current_time < market_open:
                return 'premarket'
            elif market_open <= current_time < market_close:
                return 'open'
            elif market_close <= current_time < afterhours_end:
                return 'afterhours'
            else:
                return 'closed'
                
        except Exception as e:
            print(f"Error determining market status: {e}")
            return 'closed'
            
    def _update_live_price_display(self):
        """Update live price display on chart and UI (NEW)"""
        try:
            if not self.live_price_data or not self.main_ax:
                return
                
            # Update market status label
            if hasattr(self, 'market_status_label'):
                status_text = f"MARKET: {self.live_price_data.market_status.upper()}"
                status_color = self._get_market_status_color()
                self.market_status_label.config(text=status_text, fg=status_color)
            
            # Update chart title with live price
            if hasattr(self, 'chart_title'):
                change_sign = "+" if self.live_price_data.price_change_1h >= 0 else ""
                title_text = (f"{self.ticker_symbol} - ${self.live_price_data.current_price:.2f} "
                            f"({change_sign}{self.live_price_data.price_change_1h_percent:.2f}%) "
                            f"[{self.live_price_data.market_status.upper()}]")
                
                # Color code the title based on price movement
                title_color = self._get_price_movement_color()
                self.chart_title.config(text=title_text, fg=title_color)
            
            # Update live price line on chart
            self._update_live_price_line()
            
            # Update live price text overlay
            self._update_live_price_text()
            
        except Exception as e:
            print(f"Error updating live price display: {e}")
            
    def _update_live_price_line(self):
        """Update the live price line on the chart (NEW)"""
        try:
            if not self.live_price_line or not self.live_price_data:
                return
                
            price = self.live_price_data.current_price
            
            # Update line position and color
            self.live_price_line.set_ydata([price, price])
            
            # Set color based on 1-hour movement
            line_color = self._get_price_movement_color()
            self.live_price_line.set_color(line_color)
            
            # Show the line
            self.live_price_line.set_visible(True)
            
            # Ensure the price is within the current chart view
            ylim = self.main_ax.get_ylim()
            if ylim[0] <= price <= ylim[1]:
                self.live_price_line.set_visible(True)
            else:
                self.live_price_line.set_visible(False)
                
        except Exception as e:
            print(f"Error updating live price line: {e}")
            
    def _update_live_price_text(self):
        """Update live price text overlay on chart (NEW)"""
        try:
            if not self.main_ax or not self.live_price_data:
                return
                
            # Remove old text if it exists
            if self.live_price_text:
                self.live_price_text.remove()
                
            # Get colors
            price_color = self._get_price_movement_color()
            status_color = self._get_market_status_color()
            
            # Format text
            change_sign = "+" if self.live_price_data.price_change_1h >= 0 else ""
            price_text = f"${self.live_price_data.current_price:.2f}"
            change_text = f"{change_sign}{self.live_price_data.price_change_1h:.2f} ({change_sign}{self.live_price_data.price_change_1h_percent:.2f}%)"
            status_text = self.live_price_data.market_status.upper()
            
            # Position on chart (top-right corner)
            xlim = self.main_ax.get_xlim()
            ylim = self.main_ax.get_ylim()
            
            x_pos = xlim[1] - (xlim[1] - xlim[0]) * 0.02  # 2% from right
            y_pos = ylim[1] - (ylim[1] - ylim[0]) * 0.05  # 5% from top
            
            # Create text element
            main_text = f"LIVE: {price_text} | {change_text} | {status_text}"
            
            self.live_price_text = self.main_ax.text(
                x_pos, y_pos,
                main_text,
                fontsize=10,
                fontweight='bold',
                color=price_color,
                bbox=dict(
                    boxstyle='round,pad=0.5',
                    facecolor=self.FRAME_COLOR,
                    edgecolor=status_color,
                    alpha=0.9,
                    linewidth=1.5
                ),
                zorder=101,
                verticalalignment='top',
                horizontalalignment='right'
            )
            
            # Redraw canvas
            if self.canvas:
                self.canvas.draw_idle()
                
        except Exception as e:
            print(f"Error updating live price text: {e}")
            
    def _get_price_movement_color(self) -> str:
        """Get color based on 1-hour price movement (NEW)"""
        if not self.live_price_data:
            return self.TEXT_COLOR
            
        if self.live_price_data.price_change_1h > 0:
            return self.SUCCESS_COLOR  # Green for gains
        elif self.live_price_data.price_change_1h < 0:
            return self.ERROR_COLOR    # Red for losses
        else:
            return self.TEXT_COLOR     # Neutral for no change
            
    def _get_market_status_color(self) -> str:
        """Get color based on market status (NEW)"""
        if not self.live_price_data:
            return self.MARKET_CLOSED_COLOR
            
        status_colors = {
            'open': self.MARKET_OPEN_COLOR,
            'closed': self.MARKET_CLOSED_COLOR,
            'premarket': self.PREMARKET_COLOR,
            'afterhours': self.AFTERHOURS_COLOR
        }
        return status_colors.get(self.live_price_data.market_status, self.TEXT_COLOR)
        
    def _schedule_next_live_update(self):
        """Schedule the next live price update (NEW)"""
        if not self.live_update_active:
            return
            
        # Update frequency based on market status
        if self.live_price_data and self.live_price_data.market_status == 'open':
            update_interval = 15000  # 15 seconds during market hours
        elif self.live_price_data and self.live_price_data.market_status in ['premarket', 'afterhours']:
            update_interval = 30000  # 30 seconds during extended hours
        else:
            update_interval = 60000  # 60 seconds when market is closed
            
        try:
            if hasattr(self, 'chart_frame'):
                root = self.chart_frame.winfo_toplevel()
                self.live_update_timer = root.after(update_interval, self._fetch_live_price_data)
        except:
            pass
            
    def _stop_live_updates(self):
        """Stop live price updates (NEW)"""
        self.live_update_active = False
        
        if self.live_update_timer:
            try:
                root = self.chart_frame.winfo_toplevel()
                root.after_cancel(self.live_update_timer)
                self.live_update_timer = None
            except:
                pass
                
        # Hide live price elements
        if self.live_price_line:
            self.live_price_line.set_visible(False)
        if self.live_price_text:
            self.live_price_text.set_visible(False)
            
        if self.canvas:
            self.canvas.draw_idle()

    # ... (keeping all the existing methods for RSI, crosshair, interactions, etc.)
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI (Relative Strength Index)"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss.replace(0, float('inf'))
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(prices), index=prices.index)
            
    def _plot_rsi(self):
        """Plot RSI indicator"""
        try:
            rsi_values = self._calculate_rsi(self.chart_data['Close'])
            x_pos = np.arange(len(self.chart_data))
            
            # Style RSI axis
            self.rsi_ax.set_facecolor(self.FRAME_COLOR)
            self.rsi_ax.set_ylabel('RSI', color=self.TEXT_COLOR, fontsize=10)
            self.rsi_ax.grid(True, alpha=0.3, color='#555555')
            self.rsi_ax.set_ylim(0, 100)
            
            # Add RSI reference lines
            self.rsi_ax.axhline(y=70, color=self.ERROR_COLOR, linestyle='--', alpha=0.7, linewidth=1)
            self.rsi_ax.axhline(y=30, color=self.SUCCESS_COLOR, linestyle='--', alpha=0.7, linewidth=1)
            self.rsi_ax.axhline(y=50, color=self.TEXT_COLOR, linestyle='-', alpha=0.4, linewidth=0.5)
            
            # Plot RSI line
            self.rsi_ax.plot(x_pos, rsi_values, color=self.HEADER_COLOR, linewidth=1.5, alpha=0.9)
            
            # Fill overbought/oversold areas
            self.rsi_ax.fill_between(x_pos, 70, 100, where=(rsi_values >= 70), 
                                    color=self.ERROR_COLOR, alpha=0.2, interpolate=True)
            self.rsi_ax.fill_between(x_pos, 0, 30, where=(rsi_values <= 30), 
                                    color=self.SUCCESS_COLOR, alpha=0.2, interpolate=True)
            
            self.rsi_ax.set_xlim(-0.5, len(self.chart_data) - 0.5)
            
        except Exception as e:
            print(f"Error plotting RSI: {e}")
            
    def _show_no_data_message(self):
        """Show message when no stock data is available"""
        if not hasattr(self, 'chart_frame'):
            return
            
        # Clear existing widgets
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        # Create instruction message
        message_frame = tk.Frame(self.chart_frame, bg=self.FRAME_COLOR)
        message_frame.pack(expand=True, fill='both')
        
        instruction_label = tk.Label(
            message_frame,
            text="📊 No Stock Data Loaded\n\n" +
                 "To view charts:\n" +
                 "1. Enter a stock ticker (e.g., AAPL, MSFT, GOOGL)\n" +
                 "2. Wait for data to load\n" +
                 "3. Charts will appear automatically with live price updates\n\n" +
                 "Features:\n" +
                 "• Live price line with color-coded movement\n" +
                 "• Market status indicator (Open/Closed/Premarket/Afterhours)\n" +
                 "• Real-time price updates in chart title\n" +
                 "• 1D: Hourly data / 1M-5Y: Daily data",
            font=('Arial', 12), 
            bg=self.FRAME_COLOR, 
            fg=self.TEXT_COLOR,
            justify='center'
        )
        instruction_label.pack(expand=True)
            
    def _setup_crosshair_elements(self):
        """Setup crosshair lines and annotations"""
        if not all([self.main_ax, self.volume_ax, self.rsi_ax]):
            return
            
        try:
            # Create crosshair lines
            self.horiz_line = self.main_ax.axhline(
                color='white', lw=0.5, ls='--', visible=False, animated=True
            )
            
            self.vert_line_main = self.main_ax.axvline(
                color='white', lw=0.5, ls='--', visible=False, animated=True
            )
            self.vert_line_volume = self.volume_ax.axvline(
                color='white', lw=0.5, ls='--', visible=False, animated=True
            )
            self.vert_line_rsi = self.rsi_ax.axvline(
                color='white', lw=0.5, ls='--', visible=False, animated=True
            )
            
            # Create annotations
            self.price_annotation = self.main_ax.annotate(
                '', xy=(0, 0), xytext=(-8, 0), textcoords='offset points',
                ha='right', va='center',
                bbox=dict(boxstyle='round', fc=self.FRAME_COLOR, ec=self.HEADER_COLOR, lw=0.5, alpha=0.9),
                color=self.TEXT_COLOR, fontsize=9, visible=False, animated=True
            )
            
            self.date_annotation = self.main_ax.annotate(
                '', xy=(0, 0), xytext=(0, -20), textcoords='offset points',
                bbox=dict(boxstyle='round', fc=self.FRAME_COLOR, ec=self.HEADER_COLOR, lw=0.5, alpha=0.9),
                color=self.TEXT_COLOR, fontsize=9, ha='center', visible=False, animated=True
            )
            
        except Exception as e:
            print(f"Could not setup crosshair elements: {e}")

    def on_draw(self, event):
        """Callback for draw events"""
        try:
            if all([self.main_ax, self.volume_ax, self.rsi_ax]):
                self.main_background = self.canvas.copy_from_bbox(self.main_ax.bbox)
                self.volume_background = self.canvas.copy_from_bbox(self.volume_ax.bbox)
                self.rsi_background = self.canvas.copy_from_bbox(self.rsi_ax.bbox)
        except:
            pass
            
    def on_mouse_move(self, event):
        """Handle mouse movement for crosshair, panning, and Y-axis dragging"""
        try:
            # Handle Y-axis dragging if active
            if self.y_drag_active and self.y_drag_start_y is not None and event.ydata is not None:
                self._handle_y_drag(event.ydata)
                return
                
            # Handle X-axis panning if active
            if self.pan_active and self.pan_start_x is not None and event.xdata is not None:
                self._handle_pan(event.xdata)
                return
                
            # Show special cursor when hovering over Y-axis area
            if self._is_y_axis_click(event):
                self.canvas.get_tk_widget().config(cursor="sb_v_double_arrow")
            else:
                self.canvas.get_tk_widget().config(cursor="")
                
            # Handle crosshair if not dragging/panning
            if not self.main_ax or not event.inaxes:
                self._hide_crosshair()
                return
                
            if event.inaxes not in [self.main_ax, self.volume_ax, self.rsi_ax]:
                self._hide_crosshair()
                return
                
            x, y = event.xdata, event.ydata
            if x is None or y is None:
                return
                
            # For volume and RSI charts, map to main chart y-coordinate
            if event.inaxes == self.main_ax:
                main_y = y
            else:
                main_ylim = self.main_ax.get_ylim()
                main_y = (main_ylim[0] + main_ylim[1]) / 2
                
            self._show_crosshair(x, main_y)
            self._update_cursor_info(x, main_y)
            
        except Exception as e:
            print(f"Error in mouse move: {e}")
            
    def on_mouse_press(self, event):
        """Handle mouse press for panning and Y-axis dragging"""
        try:
            if event.button == 1:  # Left click
                # Check if click is on Y-axis area (right side of charts)
                if self._is_y_axis_click(event):
                    self._start_y_drag(event)
                elif event.inaxes in [self.main_ax, self.volume_ax, self.rsi_ax]:
                    self._start_x_pan(event)
                    
        except Exception as e:
            print(f"Error in mouse press: {e}")
            
    def on_mouse_release(self, event):
        """Handle mouse release to stop panning and Y-dragging"""
        try:
            if event.button == 1:  # Left click release
                self.pan_active = False
                self.pan_start_x = None
                self.pan_start_xlim = None
                
                self.y_drag_active = False
                self.y_drag_start_y = None
                self.y_drag_start_ylim = None
                self.y_drag_chart = None
                
                # Reset cursor
                self.canvas.get_tk_widget().config(cursor="")
                
        except Exception as e:
            print(f"Error in mouse release: {e}")
            
    def on_scroll(self, event):
        """Handle scroll wheel for horizontal zoom anchored to right side"""
        try:
            if not event.inaxes or event.inaxes not in [self.main_ax, self.volume_ax, self.rsi_ax]:
                return
                
            # Get current limits
            xlim = self.main_ax.get_xlim()
            x_right = xlim[1]  # Keep right side anchored
            x_range = xlim[1] - xlim[0]
            
            # Calculate zoom factor
            if event.step > 0:  # Scroll up - zoom in (show fewer candlesticks)
                zoom_factor = 1 - self.zoom_sensitivity
            else:  # Scroll down - zoom out (show more candlesticks)
                zoom_factor = 1 + self.zoom_sensitivity
                
            # Calculate new range
            new_range = x_range * zoom_factor
            
            # Apply limits to prevent zooming too far
            data_length = len(self.chart_data) if self.chart_data is not None else 100
            min_range = 10  # Minimum 10 candlesticks visible
            max_range = data_length  # Maximum all data visible
            
            new_range = max(min_range, min(max_range, new_range))
            
            # Calculate new limits with RIGHT SIDE ANCHORED
            new_xlim = [x_right - new_range, x_right]
            
            # Ensure we don't go beyond left data bound
            if new_xlim[0] < -0.5:
                new_xlim[0] = -0.5
                new_xlim[1] = new_xlim[0] + new_range
                
            # Apply zoom to all charts
            self._apply_zoom(new_xlim)
            
        except Exception as e:
            print(f"Error in scroll: {e}")
            
    def _is_y_axis_click(self, event):
        """Check if click is in the Y-axis region for dragging"""
        if not event.inaxes:
            return False
            
        # Check if click is in the right 15% of the chart (Y-axis region)
        if event.inaxes in [self.main_ax, self.volume_ax, self.rsi_ax]:
            # Convert event coordinates to axis coordinates
            inv = event.inaxes.transAxes.inverted()
            ax_x, ax_y = inv.transform((event.x, event.y))
            
            # Check if click is in the rightmost 15% of the axis
            return ax_x > 0.85
            
        return False
        
    def _start_y_drag(self, event):
        """Start Y-axis dragging"""
        self.y_drag_active = True
        self.y_drag_start_y = event.ydata
        self.y_drag_chart = event.inaxes
        
        if event.inaxes == self.main_ax:
            self.y_drag_start_ylim = self.main_ax.get_ylim()
        elif event.inaxes == self.volume_ax:
            self.y_drag_start_ylim = self.volume_ax.get_ylim()
        elif event.inaxes == self.rsi_ax:
            self.y_drag_start_ylim = self.rsi_ax.get_ylim()
            
        # Hide crosshair while dragging
        self._hide_crosshair()
        
        # Change cursor to indicate vertical dragging
        self.canvas.get_tk_widget().config(cursor="sb_v_double_arrow")
        
    def _start_x_pan(self, event):
        """Start X-axis panning"""
        self.pan_active = True
        self.pan_start_x = event.xdata
        self.pan_start_xlim = self.main_ax.get_xlim()
        
        # Hide crosshair while panning
        self._hide_crosshair()
        
        # Change cursor to indicate panning
        self.canvas.get_tk_widget().config(cursor="fleur")
        
    def _handle_y_drag(self, current_y):
        """Handle Y-axis scaling/zooming logic"""
        try:
            if (self.y_drag_start_y is None or self.y_drag_start_ylim is None or 
                self.y_drag_chart is None):
                return
                
            # Calculate drag distance as a percentage of the original range
            original_range = self.y_drag_start_ylim[1] - self.y_drag_start_ylim[0]
            drag_distance = self.y_drag_start_y - current_y
            
            # Convert drag to zoom factor (drag up = zoom in, drag down = zoom out)
            zoom_sensitivity = 2.0  # Increased sensitivity
            zoom_factor = 1 + (drag_distance / original_range) * zoom_sensitivity
            
            # Limit zoom factor to reasonable bounds
            zoom_factor = max(0.1, min(10.0, zoom_factor))
            
            # Calculate new range
            new_range = original_range * zoom_factor
            
            # Get the center of the original view to zoom around
            center = (self.y_drag_start_ylim[0] + self.y_drag_start_ylim[1]) / 2
            
            # Calculate new limits centered on the original center
            new_ylim = [center - new_range/2, center + new_range/2]
            
            # Apply chart-specific constraints
            if self.y_drag_chart == self.main_ax:
                # For main chart, ensure we don't zoom too far from data
                if self.chart_data is not None and not self.chart_data.empty:
                    data_min = self.chart_data['Low'].min()
                    data_max = self.chart_data['High'].max()
                    data_center = (data_min + data_max) / 2
                    
                    # If zoomed out too far, recenter on data
                    if new_range > (data_max - data_min) * 20:  # Max 20x data range
                        new_range = (data_max - data_min) * 20
                        new_ylim = [data_center - new_range/2, data_center + new_range/2]
                    # If zoomed in too far, set minimum range
                    elif new_range < (data_max - data_min) * 0.01:  # Min 1% of data range
                        new_range = (data_max - data_min) * 0.01
                        new_ylim = [center - new_range/2, center + new_range/2]
                        
                self.main_ax.set_ylim(new_ylim)
                
            elif self.y_drag_chart == self.volume_ax:
                # Volume chart - ensure bottom doesn't go below 0
                if new_ylim[0] < 0:
                    # Shift the range up to keep bottom at 0
                    offset = -new_ylim[0]
                    new_ylim[0] += offset
                    new_ylim[1] += offset
                    
                # Minimum volume range
                if new_range < 1000:
                    new_range = 1000
                    new_ylim = [0, new_range]
                    
                self.volume_ax.set_ylim(new_ylim)
                
            elif self.y_drag_chart == self.rsi_ax:
                # RSI chart - keep it reasonable around 0-100
                rsi_center = 50  # Always center RSI around 50
                
                # Minimum range of 20 (e.g., 40-60), maximum of 150 (e.g., -25 to 125)
                min_rsi_range = 20
                max_rsi_range = 150
                
                new_range = max(min_rsi_range, min(max_rsi_range, new_range))
                new_ylim = [rsi_center - new_range/2, rsi_center + new_range/2]
                
                self.rsi_ax.set_ylim(new_ylim)
                
            # Redraw canvas
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"Error in Y-axis zoom handling: {e}")
            
    def _handle_pan(self, current_x):
        """Handle panning logic"""
        try:
            if self.pan_start_x is None or self.pan_start_xlim is None:
                return
                
            # Calculate pan distance
            pan_distance = self.pan_start_x - current_x
            
            # Calculate new limits
            new_xlim = [
                self.pan_start_xlim[0] + pan_distance,
                self.pan_start_xlim[1] + pan_distance
            ]
            
            # Ensure we don't pan beyond data bounds
            data_length = len(self.chart_data) if self.chart_data is not None else 100
            
            if new_xlim[0] < -0.5:
                offset = -0.5 - new_xlim[0]
                new_xlim[0] += offset
                new_xlim[1] += offset
            elif new_xlim[1] > data_length - 0.5:
                offset = new_xlim[1] - (data_length - 0.5)
                new_xlim[0] -= offset
                new_xlim[1] -= offset
                
            # Apply pan to all charts
            self._apply_zoom(new_xlim)
            
        except Exception as e:
            print(f"Error in pan handling: {e}")
            
    def _apply_zoom(self, xlim):
        """Apply zoom/pan to all synchronized charts"""
        try:
            # Apply to main chart
            self.main_ax.set_xlim(xlim)
            
            # Apply to volume chart
            if self.volume_ax:
                self.volume_ax.set_xlim(xlim)
                
            # Apply to RSI chart
            if self.rsi_ax:
                self.rsi_ax.set_xlim(xlim)
                
            # Adjust y-axis for visible data range
            if self.chart_data is not None and not self.chart_data.empty:
                start_idx = max(0, int(xlim[0]))
                end_idx = min(len(self.chart_data), int(xlim[1]) + 1)
                
                if start_idx < end_idx:
                    visible_data = self.chart_data.iloc[start_idx:end_idx]
                    
                    if not visible_data.empty:
                        # Adjust main chart y-axis
                        min_price = visible_data['Low'].min()
                        max_price = visible_data['High'].max()
                        price_range = max_price - min_price
                        buffer = price_range * 0.05 if price_range > 0 else 1
                        
                        self.main_ax.set_ylim(min_price - buffer, max_price + buffer)
                        
                        # Adjust volume chart y-axis
                        if self.volume_ax:
                            max_volume = visible_data['Volume'].max()
                            self.volume_ax.set_ylim(0, max_volume * 1.05)
                            
            # Redraw canvas
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"Error applying zoom: {e}")
            
    def _show_crosshair(self, x, y):
        """Show crosshair at given coordinates"""
        try:
            if not all([self.vert_line_main, self.horiz_line, self.price_annotation]):
                return
                
            if not all([self.main_background, self.volume_background, self.rsi_background]):
                return
                
            # Restore backgrounds
            self.canvas.restore_region(self.main_background)
            self.canvas.restore_region(self.volume_background)
            self.canvas.restore_region(self.rsi_background)
            
            # Update vertical lines
            self.vert_line_main.set_xdata([x])
            self.vert_line_main.set_visible(True)
            
            if self.vert_line_volume:
                self.vert_line_volume.set_xdata([x])
                self.vert_line_volume.set_visible(True)
                
            if self.vert_line_rsi:
                self.vert_line_rsi.set_xdata([x])
                self.vert_line_rsi.set_visible(True)
            
            # Update horizontal line
            self.horiz_line.set_ydata([y])
            self.horiz_line.set_visible(True)
            
            # Update price annotation
            xlim = self.main_ax.get_xlim()
            self.price_annotation.xy = (xlim[1], y)
            self.price_annotation.set_text(f' {y:.2f} ')
            self.price_annotation.set_visible(True)
            
            # Update date annotation
            if self.date_annotation and self.chart_data is not None and len(self.chart_data) > 0:
                index = min(max(0, math.floor(x + 0.5)), len(self.chart_data) - 1)
                if 0 <= index < len(self.chart_data):
                    data_point = self.chart_data.iloc[index]
                    
                    if self.current_mode == 'hourly':
                        date_str = data_point.name.strftime('%Y-%m-%d')
                        day_of_week = data_point.name.strftime('%A')[:3]
                        hour_str = data_point.name.strftime('%H:%M')
                        display_text = f' {date_str} ({day_of_week}) {hour_str} '
                    else:
                        date_str = data_point.name.strftime('%Y-%m-%d')
                        day_of_week = data_point.name.strftime('%A')[:3]
                        display_text = f' {date_str} ({day_of_week}) '
                    
                    ylim = self.main_ax.get_ylim()
                    chart_height = ylim[1] - ylim[0]
                    self.date_annotation.xy = (x, ylim[1] - (chart_height * 0.05))
                    self.date_annotation.set_text(display_text)
                    self.date_annotation.set_visible(True)
            
            # Draw elements
            self.main_ax.draw_artist(self.vert_line_main)
            self.main_ax.draw_artist(self.horiz_line)
            self.main_ax.draw_artist(self.price_annotation)
            self.main_ax.draw_artist(self.date_annotation)
            
            if self.volume_ax and self.vert_line_volume:
                self.volume_ax.draw_artist(self.vert_line_volume)
                
            if self.rsi_ax and self.vert_line_rsi:
                self.rsi_ax.draw_artist(self.vert_line_rsi)
            
            # Blit all areas
            self.canvas.blit(self.main_ax.bbox)
            if self.volume_ax:
                self.canvas.blit(self.volume_ax.bbox)
            if self.rsi_ax:
                self.canvas.blit(self.rsi_ax.bbox)
            
        except Exception as e:
            print(f"Error showing crosshair: {e}")
            
    def _hide_crosshair(self):
        """Hide crosshair elements"""
        try:
            if (self.vert_line_main and self.vert_line_main.get_visible()):
                self.vert_line_main.set_visible(False)
                if self.vert_line_volume:
                    self.vert_line_volume.set_visible(False)
                if self.vert_line_rsi:
                    self.vert_line_rsi.set_visible(False)
                    
                if self.horiz_line:
                    self.horiz_line.set_visible(False)
                if self.price_annotation:
                    self.price_annotation.set_visible(False)
                if self.date_annotation:
                    self.date_annotation.set_visible(False)
                
                self._clear_cursor_info()
                
                if self.main_background:
                    self.canvas.restore_region(self.main_background)
                    self.canvas.blit(self.main_ax.bbox)
                    
                if self.volume_ax and self.volume_background:
                    self.canvas.restore_region(self.volume_background)
                    self.canvas.blit(self.volume_ax.bbox)
                    
                if self.rsi_ax and self.rsi_background:
                    self.canvas.restore_region(self.rsi_background)
                    self.canvas.blit(self.rsi_ax.bbox)
                    
        except Exception as e:
            print(f"Error hiding crosshair: {e}")
            
    def _update_cursor_info(self, x, y):
        """Update cursor info display with OHLCV and RSI data"""
        try:
            if self.chart_data is None or len(self.chart_data) == 0:
                return
                
            index = min(max(0, math.floor(x + 0.5)), len(self.chart_data) - 1)
            if 0 <= index < len(self.chart_data):
                data_point = self.chart_data.iloc[index]
                
                self.cursor_info_text.config(state='normal')
                self.cursor_info_text.delete(1.0, 'end')
                
                # Determine color
                color_tag = 'green' if data_point['Close'] >= data_point['Open'] else 'red'
                
                # Calculate RSI for this point
                rsi_values = self._calculate_rsi(self.chart_data['Close'])
                current_rsi = rsi_values.iloc[index] if index < len(rsi_values) else 50
                
                # Format display with RSI
                if self.current_mode == 'hourly':
                    date_str = data_point.name.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = data_point.name.strftime('%Y-%m-%d')
                    
                self.cursor_info_text.insert('end', f"Time: {date_str} | ")
                self.cursor_info_text.insert('end', f"O: {data_point['Open']:.2f}", color_tag)
                self.cursor_info_text.insert('end', f" | H: {data_point['High']:.2f} | L: {data_point['Low']:.2f} | ")
                self.cursor_info_text.insert('end', f"C: {data_point['Close']:.2f}", color_tag)
                self.cursor_info_text.insert('end', f" | Vol: {self._format_volume(data_point['Volume'])}")
                self.cursor_info_text.insert('end', f" | RSI: {current_rsi:.1f}")
                
                self.cursor_info_text.config(state='disabled')
        except:
            pass
            
    def _format_volume(self, volume):
        """Format volume numbers"""
        try:
            if volume >= 1e9:
                return f"{volume/1e9:.1f}B"
            elif volume >= 1e6:
                return f"{volume/1e6:.1f}M"
            elif volume >= 1e3:
                return f"{volume/1e3:.0f}K"
            else:
                return f"{volume:.0f}"
        except:
            return "N/A"
            
    def _clear_cursor_info(self):
        """Clear cursor info display"""
        try:
            self.cursor_info_text.config(state='normal')
            self.cursor_info_text.delete(1.0, 'end')
            self.cursor_info_text.config(state='disabled')
        except:
            pass
        
    def switch_to_hourly_mode(self):
        """Switch to hourly mode with live updates"""
        try:
            if not self.ticker_symbol:
                return
                
            # Stop any existing live updates
            self._stop_live_updates()
            
            # Set to hourly mode
            self.current_mode = 'hourly'
            
            # Update title
            if hasattr(self, 'chart_title'):
                self.chart_title.config(text=f"{self.ticker_symbol} - Loading Hourly Chart...")
            
            # Show loading message
            self._show_loading_chart()
            
            # Fetch hourly data in background
            threading.Thread(
                target=self._fetch_and_update_chart, 
                args=(self.ticker_symbol,), 
                daemon=True
            ).start()
            
        except Exception as e:
            print(f"Error switching to hourly mode: {e}")
    
    def zoom_to_period(self, num_days):
        """Zoom chart to specific time period"""
        try:
            # Switch back to daily mode when using other timeframes
            if self.current_mode == 'hourly':
                self._stop_live_updates()
                self.current_mode = 'daily'
                
                # Update title back to daily
                if hasattr(self, 'chart_title'):
                    self.chart_title.config(text=f"{self.ticker_symbol} - Loading Daily Chart...")
                
                # Reload daily data
                if self.current_stock_data:
                    threading.Thread(
                        target=self._fetch_and_update_chart, 
                        args=(self.current_stock_data.ticker,), 
                        daemon=True
                    ).start()
                    return
            
            if not self.main_ax or self.chart_data is None or self.chart_data.empty:
                return
                
            end_index = len(self.chart_data)
            start_index = max(0, end_index - num_days if num_days > 0 else 0)
            
            self.main_ax.set_xlim(start_index, end_index)
            
            # Also zoom volume and RSI charts
            if self.volume_ax:
                self.volume_ax.set_xlim(start_index, end_index)
            if self.rsi_ax:
                self.rsi_ax.set_xlim(start_index, end_index)
            
            # Adjust y-axis for price chart
            period_data = self.chart_data.iloc[start_index:end_index]
            if not period_data.empty:
                min_price = period_data['Low'].min()
                max_price = period_data['High'].max()
                buffer = (max_price - min_price) * 0.05
                self.main_ax.set_ylim(min_price - buffer, max_price + buffer)
                
                # Adjust volume y-axis for the visible period
                if self.volume_ax:
                    period_volume_max = period_data['Volume'].max()
                    self.volume_ax.set_ylim(0, period_volume_max * 1.05)
            
            if self.canvas:
                self.canvas.draw_idle()
                
        except Exception as e:
            print(f"Error zooming: {e}")


# Backward compatibility alias
ChartManager = EnhancedChartManager