# components/live_price_indicator.py
import tkinter as tk
from datetime import datetime, time as dt_time
import pytz
import yfinance as yf
import threading
import requests
from typing import Optional, Dict, Tuple
from core.event_system import EventBus, Event, EventType
from dataclasses import dataclass


@dataclass
class LivePriceData:
    """Data structure for live price information"""
    current_price: float
    price_change_1h: float
    price_change_1h_percent: float
    market_status: str  # 'open', 'closed', 'premarket', 'afterhours'
    last_update: datetime
    volume_1h: Optional[int] = None


class LivePriceIndicator:
    """
    Modular live price indicator that overlays on charts
    Shows current price, 1-hour movement, and market status with color coding
    """
    
    def __init__(self, event_bus: EventBus, theme_colors: Dict[str, str] = None):
        self.event_bus = event_bus
        self.colors = theme_colors or self._default_colors()
        
        # State tracking
        self.ticker_symbol = None
        self.live_data = None
        self.update_active = False
        self.update_timer = None
        
        # Chart integration
        self.chart_manager = None
        self.price_indicator_elements = {}  # Store chart elements
        
        # Market timezone (Eastern)
        self.eastern_tz = pytz.timezone('US/Eastern')
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.on_stock_data_received)
        self.event_bus.subscribe(EventType.CHART_READY, self.on_chart_ready)
        
    def _default_colors(self) -> Dict[str, str]:
        """Default theme colors matching Stocker app"""
        return {
            'bg': '#333333',
            'frame': '#444444',
            'text': '#e0e0e0',
            'success': '#5a9c5a',    # Green for gains
            'error': '#d16a6a',      # Red for losses
            'warning': '#d8a062',    # Orange for warnings
            'header': '#6ea3d8',     # Blue for headers
            'live_price': '#00ff00', # Bright green for live price line
            'market_open': '#5a9c5a',    # Green when market is open
            'market_closed': '#8a8a8a',  # Gray when market is closed
            'premarket': '#d8a062',      # Orange for premarket
            'afterhours': '#6ea3d8'      # Blue for after hours
        }
    
    def set_chart_manager(self, chart_manager):
        """Set reference to chart manager for integration"""
        self.chart_manager = chart_manager
        
    def on_stock_data_received(self, event: Event):
        """Handle new stock data"""
        stock_data = event.data.get('stock_data')
        if stock_data and hasattr(stock_data, 'ticker'):
            self.ticker_symbol = stock_data.ticker
            self.start_live_updates()
            
    def on_chart_ready(self, event: Event):
        """Handle chart ready event"""
        if self.ticker_symbol and self.live_data:
            self.update_chart_indicator()
            
    def start_live_updates(self):
        """Start live price updates"""
        if not self.ticker_symbol:
            return
            
        self.update_active = True
        self._fetch_initial_live_data()
        self._schedule_next_update()
        
    def stop_live_updates(self):
        """Stop live price updates"""
        self.update_active = False
        if self.update_timer:
            try:
                # Cancel the timer if possible
                self.update_timer = None
            except:
                pass
                
    def _fetch_initial_live_data(self):
        """Fetch initial live price data in background"""
        if not self.ticker_symbol:
            return
            
        threading.Thread(
            target=self._fetch_live_data_worker,
            daemon=True
        ).start()
        
    def _fetch_live_data_worker(self):
        """Worker thread to fetch live price data"""
        try:
            # Get current market status
            market_status = self._get_market_status()
            
            # Fetch current price and 1-hour data
            current_price, price_1h_ago = self._fetch_price_data()
            
            if current_price is not None:
                # Calculate 1-hour change
                if price_1h_ago is not None:
                    price_change_1h = current_price - price_1h_ago
                    price_change_1h_percent = (price_change_1h / price_1h_ago) * 100
                else:
                    price_change_1h = 0
                    price_change_1h_percent = 0
                
                # Create live data object
                self.live_data = LivePriceData(
                    current_price=current_price,
                    price_change_1h=price_change_1h,
                    price_change_1h_percent=price_change_1h_percent,
                    market_status=market_status,
                    last_update=datetime.now()
                )
                
                # Publish live price update event
                self.event_bus.publish(Event(
                    type=EventType.LIVE_PRICE_UPDATED,
                    data={
                        'ticker': self.ticker_symbol,
                        'live_data': self.live_data
                    }
                ))
                
                # Update chart indicator if chart manager is available
                if self.chart_manager:
                    try:
                        # Schedule on main thread
                        root = self.chart_manager.chart_frame.winfo_toplevel()
                        root.after(0, self.update_chart_indicator)
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error fetching live price data: {e}")
            
    def _fetch_price_data(self) -> Tuple[Optional[float], Optional[float]]:
        """Fetch current price and 1-hour ago price"""
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
            print(f"Error fetching price data: {e}")
            return None, None
            
    def _get_market_status(self) -> str:
        """Determine current market status"""
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
            
    def update_chart_indicator(self):
        """Update the live price indicator on the chart"""
        if not self.chart_manager or not self.live_data:
            return
            
        try:
            # Only update if we have a main chart axis
            if not hasattr(self.chart_manager, 'main_ax') or not self.chart_manager.main_ax:
                return
                
            # Remove old indicator elements
            self._remove_old_indicator()
            
            # Add live price line
            self._add_live_price_line()
            
            # Add price and status text overlay
            self._add_price_text_overlay()
            
            # Redraw canvas
            if self.chart_manager.canvas:
                self.chart_manager.canvas.draw_idle()
                
        except Exception as e:
            print(f"Error updating chart indicator: {e}")
            
    def _remove_old_indicator(self):
        """Remove previous indicator elements"""
        try:
            for element_type, element in self.price_indicator_elements.items():
                if element and hasattr(element, 'remove'):
                    element.remove()
            self.price_indicator_elements.clear()
        except:
            pass
            
    def _add_live_price_line(self):
        """Add horizontal line showing current live price"""
        try:
            price = self.live_data.current_price
            
            # Get color based on 1-hour movement
            if self.live_data.price_change_1h > 0:
                line_color = self.colors['success']  # Green for up
            elif self.live_data.price_change_1h < 0:
                line_color = self.colors['error']    # Red for down
            else:
                line_color = self.colors['text']     # Neutral for no change
                
            # Create horizontal line
            line = self.chart_manager.main_ax.axhline(
                y=price,
                color=line_color,
                linestyle='--',
                linewidth=1.5,
                alpha=0.8,
                zorder=100  # High zorder to show on top
            )
            
            self.price_indicator_elements['price_line'] = line
            
        except Exception as e:
            print(f"Error adding live price line: {e}")
            
    def _add_price_text_overlay(self):
        """Add text overlay showing price and status"""
        try:
            # Determine colors
            price_color = self._get_price_movement_color()
            status_color = self._get_market_status_color()
            
            # Format price change
            change_sign = "+" if self.live_data.price_change_1h >= 0 else ""
            price_text = f"${self.live_data.current_price:.2f}"
            change_text = f"{change_sign}{self.live_data.price_change_1h:.2f} ({change_sign}{self.live_data.price_change_1h_percent:.2f}%)"
            status_text = f"{self.live_data.market_status.upper()}"
            
            # Get chart position (top-left corner)
            xlim = self.chart_manager.main_ax.get_xlim()
            ylim = self.chart_manager.main_ax.get_ylim()
            
            # Position for live price display (top-left of chart)
            x_pos = xlim[0] + (xlim[1] - xlim[0]) * 0.02  # 2% from left
            y_pos = ylim[1] - (ylim[1] - ylim[0]) * 0.05  # 5% from top
            
            # Create text elements
            main_text = f"LIVE: {price_text} | {change_text} | {status_text}"
            
            text_element = self.chart_manager.main_ax.text(
                x_pos, y_pos,
                main_text,
                fontsize=10,
                fontweight='bold',
                color=price_color,
                bbox=dict(
                    boxstyle='round,pad=0.5',
                    facecolor=self.colors['frame'],
                    edgecolor=status_color,
                    alpha=0.9,
                    linewidth=1.5
                ),
                zorder=101,
                verticalalignment='top'
            )
            
            self.price_indicator_elements['price_text'] = text_element
            
        except Exception as e:
            print(f"Error adding price text overlay: {e}")
            
    def _get_price_movement_color(self) -> str:
        """Get color based on 1-hour price movement"""
        if self.live_data.price_change_1h > 0:
            return self.colors['success']  # Green for gains
        elif self.live_data.price_change_1h < 0:
            return self.colors['error']    # Red for losses
        else:
            return self.colors['text']     # Neutral for no change
            
    def _get_market_status_color(self) -> str:
        """Get color based on market status"""
        status_colors = {
            'open': self.colors['market_open'],
            'closed': self.colors['market_closed'],
            'premarket': self.colors['premarket'],
            'afterhours': self.colors['afterhours']
        }
        return status_colors.get(self.live_data.market_status, self.colors['text'])
        
    def _schedule_next_update(self):
        """Schedule the next live update"""
        if not self.update_active:
            return
            
        # Update frequency based on market status
        if self.live_data and self.live_data.market_status == 'open':
            update_interval = 15000  # 15 seconds during market hours
        elif self.live_data and self.live_data.market_status in ['premarket', 'afterhours']:
            update_interval = 30000  # 30 seconds during extended hours
        else:
            update_interval = 60000  # 60 seconds when market is closed
            
        try:
            if self.chart_manager and hasattr(self.chart_manager, 'chart_frame'):
                root = self.chart_manager.chart_frame.winfo_toplevel()
                self.update_timer = root.after(update_interval, self._fetch_initial_live_data)
        except:
            pass


class LivePriceIntegration:
    """Helper class for integrating live price indicator with existing components"""
    
    @staticmethod
    def create_for_chart_manager(event_bus: EventBus, chart_manager, theme_colors: Dict[str, str] = None):
        """Create and integrate live price indicator with chart manager"""
        indicator = LivePriceIndicator(event_bus, theme_colors)
        indicator.set_chart_manager(chart_manager)
        return indicator
        
    @staticmethod
    def add_live_price_events():
        """Add new event types for live price updates"""
        # Add to EventType enum if needed
        if not hasattr(EventType, 'LIVE_PRICE_UPDATED'):
            EventType.LIVE_PRICE_UPDATED = 'live_price_updated'
        if not hasattr(EventType, 'CHART_READY'):
            EventType.CHART_READY = 'chart_ready'


# Usage example for integration:
"""
# In your main application or chart manager:

# 1. Import the component
from components.live_price_indicator import LivePriceIndicator, LivePriceIntegration

# 2. Create and integrate with chart manager
theme_colors = {
    'bg': '#333333',
    'frame': '#444444', 
    'text': '#e0e0e0',
    'success': '#5a9c5a',
    'error': '#d16a6a',
    'warning': '#d8a062',
    'header': '#6ea3d8'
}

live_price_indicator = LivePriceIntegration.create_for_chart_manager(
    event_bus, 
    chart_manager, 
    theme_colors
)

# 3. The indicator will automatically start when stock data is received
# and update the chart with live price information
"""