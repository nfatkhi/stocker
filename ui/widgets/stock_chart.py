# ui/widgets/stock_chart.py - Enhanced version with candlestick support
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import mplfinance as mpf
import pandas as pd
import numpy as np
from datetime import datetime
import math

class EnhancedStockChart(ttk.Frame):
    """Enhanced widget for displaying sophisticated stock charts with candlesticks and interactivity"""
    
    def __init__(self, parent, title="Stock Price", chart_type='candlestick', **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.chart_type = chart_type  # 'candlestick', 'ohlc', 'line'
        self.chart_data = None
        
        # Theme colors
        self.BG_COLOR = '#333333'
        self.FRAME_COLOR = '#444444'
        self.TEXT_COLOR = '#e0e0e0'
        self.HEADER_COLOR = '#6ea3d8'
        self.SUCCESS_COLOR = '#5a9c5a'
        self.ERROR_COLOR = '#d16a6a'
        
        # Interactive elements
        self.canvas = None
        self.main_ax = None
        self.volume_ax = None
        self.rsi_ax = None
        self.horiz_line = None
        self.vert_line = None
        self.price_annotation = None
        self.date_annotation = None
        self.ax_background = None
        
        # Create the chart
        self._create_chart()
        
    def _create_chart(self):
        """Create sophisticated matplotlib chart with dark theme"""
        # Create figure with dark theme
        self.figure = Figure(figsize=(10, 10), dpi=100, facecolor=self.FRAME_COLOR)
        
        # Create subplots - main chart, volume, and RSI
        gs = self.figure.add_gridspec(6, 1, hspace=0.1, height_ratios=[4, 1, 1, 0.2, 1, 0.2])
        self.main_ax = self.figure.add_subplot(gs[0, 0])
        self.volume_ax = self.figure.add_subplot(gs[2, 0], sharex=self.main_ax)
        self.rsi_ax = self.figure.add_subplot(gs[4, 0], sharex=self.main_ax)
        
        # Style main axis
        self.main_ax.set_facecolor(self.FRAME_COLOR)
        self.main_ax.tick_params(colors=self.TEXT_COLOR, labelsize=9)
        self.main_ax.set_title(self.title, color=self.HEADER_COLOR, fontsize=12, fontweight='bold')
        self.main_ax.set_ylabel('Price ($)', color=self.TEXT_COLOR)
        self.main_ax.grid(True, alpha=0.3, color='#555555')
        
        # Style volume axis
        self.volume_ax.set_facecolor(self.FRAME_COLOR)
        self.volume_ax.tick_params(colors=self.TEXT_COLOR, labelsize=8)
        self.volume_ax.set_ylabel('Volume', color=self.TEXT_COLOR)
        self.volume_ax.grid(True, alpha=0.3, color='#555555')
        
        # Style RSI axis
        self.rsi_ax.set_facecolor(self.FRAME_COLOR)
        self.rsi_ax.tick_params(colors=self.TEXT_COLOR, labelsize=8)
        self.rsi_ax.set_ylabel('RSI', color=self.TEXT_COLOR)
        self.rsi_ax.grid(True, alpha=0.3, color='#555555')
        self.rsi_ax.set_ylim(0, 100)
        
        # Add RSI reference lines
        self.rsi_ax.axhline(y=70, color=self.ERROR_COLOR, linestyle='--', alpha=0.5, linewidth=1)
        self.rsi_ax.axhline(y=30, color=self.SUCCESS_COLOR, linestyle='--', alpha=0.5, linewidth=1)
        self.rsi_ax.axhline(y=50, color=self.TEXT_COLOR, linestyle='-', alpha=0.3, linewidth=0.5)
        
        # Style spines
        for ax in [self.main_ax, self.volume_ax, self.rsi_ax]:
            for spine in ax.spines.values():
                spine.set_color(self.TEXT_COLOR)
                
        # Remove top and right spines
        for ax in [self.main_ax, self.volume_ax, self.rsi_ax]:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
        # Hide x-axis labels on main chart and volume chart
        self.main_ax.set_xticklabels([])
        self.volume_ax.set_xticklabels([])
        
        # Setup interactive elements
        self._setup_crosshair()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Add navigation toolbar
        self._add_toolbar()
        
        # Connect events
        self.canvas.mpl_connect('draw_event', self.on_draw)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # Show placeholder
        self._show_placeholder()
        
    def _setup_crosshair(self):
        """Setup crosshair lines and annotations"""
        # Crosshair lines
        self.horiz_line = self.main_ax.axhline(
            color='white', lw=0.7, ls='--', alpha=0.8, visible=False, animated=True
        )
        self.vert_line = self.main_ax.axvline(
            color='white', lw=0.7, ls='--', alpha=0.8, visible=False, animated=True
        )
        
        # Price annotation (right side)
        self.price_annotation = self.main_ax.annotate(
            '', xy=(0, 0), xytext=(-8, 0), textcoords='offset points',
            ha='right', va='center',
            bbox=dict(boxstyle='round,pad=0.3', fc=self.FRAME_COLOR, ec=self.HEADER_COLOR, alpha=0.9),
            color=self.TEXT_COLOR, fontsize=9, visible=False, animated=True
        )
        
        # Date annotation (bottom)
        self.date_annotation = self.main_ax.annotate(
            '', xy=(0, 0), xytext=(0, 8), textcoords='offset points',
            ha='center', va='bottom',
            bbox=dict(boxstyle='round,pad=0.3', fc=self.FRAME_COLOR, ec=self.HEADER_COLOR, alpha=0.9),
            color=self.TEXT_COLOR, fontsize=9, visible=False, animated=True
        )
        
    def _add_toolbar(self):
        """Add navigation toolbar with dark theme"""
        toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        toolbar.config(background=self.FRAME_COLOR)
        if hasattr(toolbar, '_message_label'):
            toolbar._message_label.config(background=self.FRAME_COLOR, foreground=self.TEXT_COLOR)
        
        # Style toolbar buttons
        for button in toolbar.winfo_children():
            if hasattr(button, 'config'):
                button.config(background=self.FRAME_COLOR)
        
        toolbar.update()
        toolbar.pack(side='bottom', fill='x')
        
    def _show_placeholder(self):
        """Show placeholder text"""
        self.main_ax.text(0.5, 0.5, 'Waiting for stock data...', 
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.main_ax.transAxes, fontsize=14, color=self.TEXT_COLOR)
        self.canvas.draw()
        
    def update_data_ohlcv(self, ohlcv_data, ticker_symbol=None):
        """Update chart with OHLCV data for candlestick/OHLC charts"""
        print(f"Updating chart with OHLCV data: {len(ohlcv_data)} periods")
        
        if ohlcv_data is None or ohlcv_data.empty:
            self._show_no_data()
            return
            
        self.chart_data = ohlcv_data
        
        # Update title
        title = f"{ticker_symbol} - {self.title}" if ticker_symbol else self.title
        self.main_ax.set_title(title, color=self.HEADER_COLOR, fontsize=12, fontweight='bold')
        
        # Clear axes
        self.main_ax.clear()
        self.volume_ax.clear()
        self.rsi_ax.clear()
        self.rsi_ax.clear()
        
        # Re-apply styling after clear
        self._style_axes()
        
        try:
            if self.chart_type == 'candlestick':
                self._plot_candlestick(ohlcv_data)
            elif self.chart_type == 'ohlc':
                self._plot_ohlc(ohlcv_data)
            else:  # line chart
                self._plot_line(ohlcv_data)
                
            # Plot volume and RSI
            self._plot_volume(ohlcv_data)
            self._plot_rsi(ohlcv_data)
            
            # Re-setup crosshair after clearing
            self._setup_crosshair()
            
            # Adjust layout
            self.figure.tight_layout()
            
            # Redraw
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error plotting chart: {e}")
            self._show_error(f"Chart error: {str(e)}")
            
    def _style_axes(self):
        """Apply styling to axes after clearing"""
        # Style main axis
        self.main_ax.set_facecolor(self.FRAME_COLOR)
        self.main_ax.tick_params(colors=self.TEXT_COLOR, labelsize=9)
        self.main_ax.set_ylabel('Price ($)', color=self.TEXT_COLOR)
        self.main_ax.grid(True, alpha=0.3, color='#555555')
        
        # Style volume axis
        self.volume_ax.set_facecolor(self.FRAME_COLOR)
        self.volume_ax.tick_params(colors=self.TEXT_COLOR, labelsize=8)
        self.volume_ax.set_ylabel('Volume', color=self.TEXT_COLOR)
        self.volume_ax.grid(True, alpha=0.3, color='#555555')
        
        # Style RSI axis
        self.rsi_ax.set_facecolor(self.FRAME_COLOR)
        self.rsi_ax.tick_params(colors=self.TEXT_COLOR, labelsize=8)
        self.rsi_ax.set_ylabel('RSI', color=self.TEXT_COLOR)
        self.rsi_ax.grid(True, alpha=0.3, color='#555555')
        self.rsi_ax.set_ylim(0, 100)
        
        # Add RSI reference lines
        self.rsi_ax.axhline(y=70, color=self.ERROR_COLOR, linestyle='--', alpha=0.5, linewidth=1)
        self.rsi_ax.axhline(y=30, color=self.SUCCESS_COLOR, linestyle='--', alpha=0.5, linewidth=1)
        self.rsi_ax.axhline(y=50, color=self.TEXT_COLOR, linestyle='-', alpha=0.3, linewidth=0.5)
        
        # Style spines
        for ax in [self.main_ax, self.volume_ax, self.rsi_ax]:
            for spine in ax.spines.values():
                spine.set_color(self.TEXT_COLOR)
                
        # Remove top and right spines
        for ax in [self.main_ax, self.volume_ax, self.rsi_ax]:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
        # Hide x-axis labels on main chart and volume chart
        self.main_ax.set_xticklabels([])
        self.volume_ax.set_xticklabels([])
        
    def _plot_candlestick(self, data):
        """Plot candlestick chart using custom implementation"""
        # Create candlestick plot manually for better control
        opens = data['Open'].values
        highs = data['High'].values
        lows = data['Low'].values
        closes = data['Close'].values
        
        # Create x-axis positions
        x_pos = np.arange(len(data))
        
        # Plot high-low lines
        for i in range(len(data)):
            self.main_ax.plot([i, i], [lows[i], highs[i]], 
                             color=self.TEXT_COLOR, linewidth=1, alpha=0.8)
            
        # Plot candlestick bodies
        for i in range(len(data)):
            open_price = opens[i]
            close_price = closes[i]
            
            # Determine color
            if close_price >= open_price:
                color = self.SUCCESS_COLOR
                bottom = open_price
                height = close_price - open_price
            else:
                color = self.ERROR_COLOR
                bottom = close_price
                height = open_price - close_price
                
            # Draw rectangle for body
            rect = plt.Rectangle((i - 0.3, bottom), 0.6, height, 
                               facecolor=color, edgecolor=color, alpha=0.8)
            self.main_ax.add_patch(rect)
            
        # Add moving averages if enough data
        if len(data) > 20:
            ma20 = data['Close'].rolling(20).mean()
            self.main_ax.plot(x_pos, ma20, color='#FFA500', linewidth=1.5, 
                             alpha=0.8, label='MA 20')
            
        if len(data) > 50:
            ma50 = data['Close'].rolling(50).mean()
            self.main_ax.plot(x_pos, ma50, color='#FF69B4', linewidth=1.5, 
                             alpha=0.8, label='MA 50')
            
        # Add legend if we have moving averages
        if len(data) > 20:
            self.main_ax.legend(loc='upper left', facecolor=self.FRAME_COLOR, 
                               edgecolor=self.TEXT_COLOR, labelcolor=self.TEXT_COLOR)
            
        # Set x-axis limits
        self.main_ax.set_xlim(-0.5, len(data) - 0.5)
        
    def _plot_ohlc(self, data):
        """Plot OHLC bars"""
        x_pos = np.arange(len(data))
        
        for i in range(len(data)):
            open_price = data['Open'].iloc[i]
            high_price = data['High'].iloc[i]
            low_price = data['Low'].iloc[i]
            close_price = data['Close'].iloc[i]
            
            # High-low line
            self.main_ax.plot([i, i], [low_price, high_price], 
                             color=self.TEXT_COLOR, linewidth=1)
            
            # Open tick (left)
            self.main_ax.plot([i - 0.1, i], [open_price, open_price], 
                             color=self.TEXT_COLOR, linewidth=1)
            
            # Close tick (right) - colored based on direction
            close_color = self.SUCCESS_COLOR if close_price >= open_price else self.ERROR_COLOR
            self.main_ax.plot([i, i + 0.1], [close_price, close_price], 
                             color=close_color, linewidth=2)
                             
        self.main_ax.set_xlim(-0.5, len(data) - 0.5)
        
    def _plot_line(self, data):
        """Plot simple line chart"""
        x_pos = np.arange(len(data))
        self.main_ax.plot(x_pos, data['Close'], color=self.HEADER_COLOR, 
                         linewidth=2, marker='o', markersize=2)
        self.main_ax.set_xlim(-0.5, len(data) - 0.5)
        
    def _plot_volume(self, data):
        """Plot volume bars"""
        x_pos = np.arange(len(data))
        
        # Color volume bars based on price direction
        colors = []
        for i in range(len(data)):
            if data['Close'].iloc[i] >= data['Open'].iloc[i]:
                colors.append(self.SUCCESS_COLOR)
            else:
                colors.append(self.ERROR_COLOR)
                
        self.volume_ax.bar(x_pos, data['Volume'], color=colors, alpha=0.7)
        self.volume_ax.set_xlim(-0.5, len(data) - 0.5)
        
        # Format volume y-axis
        self.volume_ax.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
        
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI (Relative Strength Index)"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # Avoid division by zero
            rs = gain / loss.replace(0, float('inf'))
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)  # Fill NaN with neutral 50
        except Exception as e:
            print(f"Error calculating RSI: {e}")
            return pd.Series([50] * len(prices), index=prices.index)
    
    def _plot_rsi(self, data):
        """Plot RSI indicator"""
        try:
            x_pos = np.arange(len(data))
            
            # Calculate RSI
            rsi_values = self._calculate_rsi(data['Close'])
            
            # Plot RSI line
            self.rsi_ax.plot(x_pos, rsi_values, color=self.HEADER_COLOR, linewidth=1.5, alpha=0.8)
            
            # Fill overbought/oversold areas
            self.rsi_ax.fill_between(x_pos, 70, 100, where=(rsi_values >= 70), 
                                    color=self.ERROR_COLOR, alpha=0.2, interpolate=True, label='Overbought')
            self.rsi_ax.fill_between(x_pos, 0, 30, where=(rsi_values <= 30), 
                                    color=self.SUCCESS_COLOR, alpha=0.2, interpolate=True, label='Oversold')
            
            # Set limits and styling
            self.rsi_ax.set_xlim(-0.5, len(data) - 0.5)
            self.rsi_ax.set_ylim(0, 100)
            
            # Add text labels for reference levels
            self.rsi_ax.text(0.01, 0.95, '70', transform=self.rsi_ax.transAxes, 
                           color=self.ERROR_COLOR, fontsize=8, va='top')
            self.rsi_ax.text(0.01, 0.35, '30', transform=self.rsi_ax.transAxes, 
                           color=self.SUCCESS_COLOR, fontsize=8, va='top')
            
        except Exception as e:
            print(f"Error plotting RSI: {e}")
            # Show placeholder if RSI calculation fails
            self.rsi_ax.text(0.5, 0.5, 'RSI calculation failed', 
                           horizontalalignment='center', verticalalignment='center',
                           transform=self.rsi_ax.transAxes, fontsize=10, color=self.ERROR_COLOR)
        
    def update_data_simple(self, dates, prices, label='Price'):
        """Update chart with simple date/price data (backward compatibility)"""
        print(f"Updating chart with simple data: {len(dates)} dates, {len(prices)} prices")
        
        if not dates or not prices:
            self._show_no_data()
            return
            
        # Clear axes
        self.main_ax.clear()
        self.volume_ax.clear()
        
        # Re-apply styling
        self._style_axes()
        
        # Plot simple line
        self.main_ax.plot(dates, prices, label=label, linewidth=2, 
                         color=self.HEADER_COLOR, marker='o', markersize=3)
        
        # Style
        self.main_ax.set_title(self.title, color=self.HEADER_COLOR, fontsize=12, fontweight='bold')
        self.main_ax.legend(facecolor=self.FRAME_COLOR, edgecolor=self.TEXT_COLOR, 
                           labelcolor=self.TEXT_COLOR)
        
        # Format dates
        self.figure.autofmt_xdate()
        
        # Hide volume and RSI charts for simple data
        self.volume_ax.set_visible(False)
        self.rsi_ax.set_visible(False)
        
        # Re-setup crosshair
        self._setup_crosshair()
        
        # Redraw
        self.canvas.draw()
        
    def on_draw(self, event):
        """Capture background for efficient blitting"""
        if self.main_ax:
            self.ax_background = self.canvas.copy_from_bbox(self.main_ax.bbox)
            
    def on_mouse_move(self, event):
        """Handle mouse movement for crosshair and info display"""
        if not self.main_ax or not hasattr(self, 'ax_background') or self.ax_background is None:
            return
            
        if not event.inaxes or event.inaxes != self.main_ax:
            self._hide_crosshair()
            return
            
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
            
        # Restore background for efficient redraw
        self.canvas.restore_region(self.ax_background)
        
        # Update crosshair
        self._show_crosshair(x, y)
        
        # Draw updated elements
        if self.horiz_line and self.vert_line:
            self.main_ax.draw_artist(self.horiz_line)
            self.main_ax.draw_artist(self.vert_line)
            
        if self.price_annotation:
            self.main_ax.draw_artist(self.price_annotation)
            
        if self.date_annotation:
            self.main_ax.draw_artist(self.date_annotation)
            
        self.canvas.blit(self.main_ax.bbox)
        
    def _show_crosshair(self, x, y):
        """Show crosshair at given coordinates"""
        if not all([self.horiz_line, self.vert_line, self.price_annotation, self.date_annotation]):
            return
            
        # Update line positions
        self.horiz_line.set_ydata([y])
        self.vert_line.set_xdata([x])
        self.horiz_line.set_visible(True)
        self.vert_line.set_visible(True)
        
        # Update price annotation
        xlim = self.main_ax.get_xlim()
        self.price_annotation.xy = (xlim[1], y)
        self.price_annotation.set_text(f' ${y:.2f} ')
        self.price_annotation.set_visible(True)
        
        # Update date annotation with OHLCV data if available
        if self.chart_data is not None and len(self.chart_data) > 0:
            index = min(max(0, math.floor(x + 0.5)), len(self.chart_data) - 1)
            if 0 <= index < len(self.chart_data):
                data_point = self.chart_data.iloc[index]
                
                if hasattr(data_point.name, 'strftime'):
                    date_str = data_point.name.strftime('%Y-%m-%d')
                    day_of_week = data_point.name.strftime('%A')[:3]
                else:
                    date_str = str(data_point.name)
                    day_of_week = ""
                
                ylim = self.main_ax.get_ylim()
                self.date_annotation.xy = (x, ylim[0])
                self.date_annotation.set_text(f' {date_str} ({day_of_week}) ')
                self.date_annotation.set_visible(True)
        
    def _hide_crosshair(self):
        """Hide crosshair elements"""
        if self.vert_line and self.vert_line.get_visible():
            self.vert_line.set_visible(False)
            self.horiz_line.set_visible(False)
            self.price_annotation.set_visible(False)
            self.date_annotation.set_visible(False)
            
            if hasattr(self, 'ax_background') and self.ax_background:
                self.canvas.restore_region(self.ax_background)
                self.canvas.blit(self.main_ax.bbox)
                
    def _show_no_data(self):
        """Show no data message"""
        self.main_ax.clear()
        self.volume_ax.clear()
        self.rsi_ax.clear()
        self._style_axes()
        
        self.main_ax.text(0.5, 0.5, 'No data available', 
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.main_ax.transAxes, fontsize=14, color=self.TEXT_COLOR)
        self.canvas.draw()
        
    def _show_error(self, message):
        """Show error message"""
        self.main_ax.clear()
        self.volume_ax.clear()
        self.rsi_ax.clear()
        self._style_axes()
        
        self.main_ax.text(0.5, 0.5, message, 
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.main_ax.transAxes, fontsize=12, color=self.ERROR_COLOR,
                         wrap=True)
        self.canvas.draw()
        
    def clear(self):
        """Clear the chart"""
        self.main_ax.clear()
        self.volume_ax.clear()
        self.rsi_ax.clear()
        self._style_axes()
        self._show_placeholder()
        self.chart_data = None
        
    def set_chart_type(self, chart_type):
        """Change chart type and redraw if data exists"""
        self.chart_type = chart_type
        if self.chart_data is not None:
            self.update_data_ohlcv(self.chart_data)


# Backward compatibility alias
StockChart = EnhancedStockChart