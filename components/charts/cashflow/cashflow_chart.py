# components/charts/cashflow/cashflow_chart.py - FCF chart with separated data processing

import tkinter as tk
from tkinter import ttk
import math
from typing import List, Dict, Any, Tuple

try:
    from ..base_chart import FinancialBarChart
except ImportError:
    try:
        from .base_chart import FinancialBarChart
    except ImportError:
        from components.charts.base_chart import FinancialBarChart

try:
    from .cashflow_data_processor import process_cashflow_data, CashflowDataPoint, CashflowMetrics
except ImportError:
    # Fallback for standalone testing
    print("⚠️ CashflowDataProcessor not available - using basic processing")
    
    class CashflowDataPoint:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class CashflowMetrics:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    def process_cashflow_data(data, max_quarters=12):
        return [], CashflowMetrics(latest_fcf=0, average_fcf=0, total_quarters=0, 
                                  recent_growth="N/A", data_quality="No Processor", 
                                  conversion_success=False)

try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {'font_family': 'Arial', 'font_size': 10}


class CashFlowChart(FinancialBarChart):
    """FCF chart with separated data processing and enhanced UI"""
    
    COLORS = {
        'positive': '#4CAF50', 'negative': '#F44336', 'neutral': '#9E9E9E',
        'yoy_growth': '#00C851', 'yoy_decline': '#FF4444', 'yoy_neutral': '#33B5E5'
    }

    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        super().__init__(parent_frame, ticker, **kwargs)
        self.data_processor_available = True
        try:
            from .cashflow_data_processor import CashflowDataProcessor
        except ImportError:
            self.data_processor_available = False
    
    def get_chart_title(self) -> str:
        return "Free Cash Flow Analysis"
    
    def get_y_label(self) -> str:
        return "Free Cash Flow (Millions $)"

    def create_chart(self, financial_data: List[Any]) -> bool:
        """Create FCF analysis using data processor"""
        if not financial_data:
            return self._show_error("No financial data provided")
        
        # Process data using separated processor
        try:
            data_points, metrics = process_cashflow_data(financial_data, max_quarters=12)
        except Exception as e:
            print(f"❌ Data processing failed: {e}")
            return self._show_error(f"Data processing error: {str(e)}")
        
        if not data_points:
            return self._show_error("No meaningful FCF data available")
        
        # Store for UI rendering
        self.data_points = data_points
        self.metrics = metrics
        
        return self._create_scrollable_layout()
    
    def _create_scrollable_layout(self) -> bool:
        """Create scrollable 3-section layout using enhanced base chart scrolling"""
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Use base chart's enhanced scrollable container
        canvas, scrollbar, content_frame = self.create_scrollable_container(self.parent_frame)
        
        # Create the three sections in the content frame
        self._create_summary_section(content_frame)
        self._create_fcf_section(content_frame)
        self._create_yoy_section(content_frame)
        
        # Update scroll region after content is added
        self.parent_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Ensure scrolling works anywhere over the content area
        self._ensure_all_widgets_scroll(content_frame, canvas)
        
        return True
    
    def _ensure_all_widgets_scroll(self, content_frame: tk.Frame, canvas: tk.Canvas):
        """Ensure all widgets in the content frame can scroll the canvas"""
        def scroll_handler(event):
            """Handle scroll events from any widget"""
            if hasattr(event, 'delta'):
                if abs(event.delta) < 50:
                    delta = -1 * (event.delta / 8)
                elif abs(event.delta) < 120:
                    delta = -1 * (event.delta / 20)
                else:
                    delta = -1 * (event.delta / 60)
            else:
                delta = -3 if event.num == 4 else 3
            
            scroll_amount = max(1, abs(int(delta)))
            direction = 1 if delta > 0 else -1
            canvas.yview_scroll(direction * scroll_amount, "units")
            return "break"
        
        def bind_to_widget_and_children(widget):
            """Recursively bind scroll events to widget and all children"""
            try:
                widget.bind("<MouseWheel>", scroll_handler)
                widget.bind("<Button-4>", scroll_handler) 
                widget.bind("<Button-5>", scroll_handler)
                
                for child in widget.winfo_children():
                    bind_to_widget_and_children(child)
            except tk.TclError:
                pass
        
        bind_to_widget_and_children(content_frame)
    
    def _create_summary_section(self, parent: tk.Frame):
        """Create summary cards using processed metrics"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=100)
        frame.pack(fill='x', pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=f"{self.ticker} - FCF Summary", 
                font=(UI_CONFIG['font_family'], 12, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(5, 0))
        
        cards_frame = tk.Frame(frame, bg=self.colors['frame'])
        cards_frame.pack(fill='both', expand=True, padx=10, pady=(0, 5))
        
        # Use processed metrics
        latest_fcf = self.metrics.latest_fcf
        avg_fcf = self.metrics.average_fcf
        recent_growth = self.metrics.recent_growth
        data_quality = self.metrics.data_quality
        
        # Determine data source description
        data_source_desc = "Cache + Processor"
        if self.metrics.conversion_success:
            data_source_desc += " (Actual Q)"
        
        metrics = [
            ("Data Source", data_source_desc, '#1976D2'),
            ("Latest FCF", f"${latest_fcf/1e6:.1f}M", self.colors['success']),
            ("Average FCF", f"${avg_fcf/1e6:.1f}M", self.colors['accent']),
            ("YoY Growth", recent_growth, '#2E7D32' if "+" in recent_growth else self.colors['warning'])
        ]
        
        for label, value, color in metrics:
            card = tk.Frame(cards_frame, bg=self.colors['bg'], relief='raised', bd=1)
            card.pack(side='left', fill='both', expand=True, padx=3)
            tk.Label(card, text=label, font=(UI_CONFIG['font_family'], 8), 
                    bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(3, 1))
            tk.Label(card, text=value, font=(UI_CONFIG['font_family'], 9, 'bold'), 
                    bg=self.colors['bg'], fg=color).pack(pady=(0, 3))
    
    def _create_fcf_section(self, parent: tk.Frame):
        """Create main FCF chart using processed data"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=400)
        frame.pack(fill='both', expand=True, pady=(0, 10))
        frame.pack_propagate(False)
        
        # Title with data quality indicator
        title_suffix = f"({self.metrics.data_quality} Data Quality)"
        
        tk.Label(frame, text=f"Free Cash Flow Trend {title_suffix}", 
                font=(UI_CONFIG['font_family'], 14, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Extract chart data
        values = [dp.fcf_dollars for dp in self.data_points]
        quarters = [dp.quarter_label for dp in self.data_points]
        
        self.create_interactive_chart(content, values, quarters, f"{self.ticker} Free Cash Flow", 
                                     "Free Cash Flow", self.COLORS['positive'], "FCF")
    
    def _create_yoy_section(self, parent: tk.Frame):
        """Create YoY analysis chart using processed data"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=350)
        frame.pack(fill='both', expand=True)
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Year-over-Year FCF Analysis", 
                font=(UI_CONFIG['font_family'], 14, 'bold'), 
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Filter to data points with YoY information
        yoy_data = [dp for dp in self.data_points 
                   if not math.isnan(dp.yoy_change_pct) and not math.isinf(dp.yoy_change_pct)]
        
        if yoy_data:
            self._create_yoy_chart(content, yoy_data)
        else:
            tk.Label(content, text="❌ No YoY Data Available\nNeed at least 4 consecutive quarters for comparison",
                    font=(UI_CONFIG['font_family'], 14), bg=self.colors['bg'], 
                    fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _create_yoy_chart(self, parent: tk.Frame, yoy_data: List[CashflowDataPoint]):
        """Create YoY matplotlib chart with consistent formatting"""
        try:
            values = [dp.yoy_change_pct for dp in yoy_data]
            quarters = [dp.quarter_label for dp in yoy_data]
            
            # Cap extreme values for visualization
            YOY_CAP = 500
            display_values = [max(-YOY_CAP, min(YOY_CAP, v)) for v in values]
            
            # Get sizing and fonts from base chart
            chart_width, chart_height, _, _ = self.get_responsive_size()
            font_sizes = self.get_dynamic_font_sizes(chart_width)
            
            # Create figure with dark theme
            fig, ax = self.create_matplotlib_figure(chart_width, chart_height)
            
            # Color bars based on change
            colors = [self.COLORS['yoy_growth'] if v > 5 else 
                     self.COLORS['yoy_decline'] if v < -5 else 
                     self.COLORS['yoy_neutral'] for v in values]
            
            bars = ax.bar(range(len(quarters)), display_values, color=colors, alpha=0.8, width=0.8)
            
            # Style chart consistently
            ax.set_title(f'{self.ticker} Year-over-Year FCF Changes', 
                        color=self.colors['header'], fontweight='bold', fontsize=font_sizes['title'])
            ax.set_ylabel('YoY Change (%)', color=self.colors['text'], fontweight='bold', fontsize=font_sizes['label'])
            ax.set_xlabel('Quarter', color=self.colors['text'], fontweight='bold', fontsize=font_sizes['label'])
            
            # Set labels
            rotation_angle = 45 if len(quarters) > 8 else 30
            ax.set_xticks(range(len(quarters)))
            ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right',
                              color=self.colors['text'], fontsize=font_sizes['tick'])
            
            # Reference lines
            ax.axhline(y=0, color=self.colors['text'], linestyle='--', alpha=0.5, linewidth=2)
            ax.axhline(y=50, color=self.COLORS['yoy_growth'], linestyle=':', alpha=0.4)
            ax.axhline(y=-50, color=self.COLORS['yoy_decline'], linestyle=':', alpha=0.4)
            
            # Value labels
            for bar, dp in zip(bars, yoy_data):
                height = bar.get_height()
                label_y = height + (8 if height >= 0 else -12)
                ax.text(bar.get_x() + bar.get_width()/2., label_y,
                       dp.yoy_label, ha='center', va='bottom' if height >= 0 else 'top',
                       color=self.colors['text'], fontsize=font_sizes['value'], fontweight='bold')
            
            # Apply consistent axis styling
            self.style_axis(ax, font_sizes)
            
            # Set figure colors to match dark theme
            ax.set_facecolor(self.colors['frame'])
            fig.patch.set_facecolor(self.colors['frame'])
            
            canvas = self.create_canvas(fig, parent)
            canvas.get_tk_widget().pack(fill='both', expand=True, pady=5)
            
        except Exception as e:
            self._show_yoy_fallback(parent, yoy_data, str(e))
    
    def _show_yoy_fallback(self, parent: tk.Frame, yoy_data: List[CashflowDataPoint], error: str):
        """Show text-based YoY display with consistent dark theme"""
        text = f"📊 YoY Analysis - {len(yoy_data)} Quarters\n\n"
        if yoy_data:
            latest = yoy_data[-1]
            text += f"Latest: {latest.quarter_label} - {latest.yoy_label}\n\n"
            text += "Recent Changes:\n" + "-"*30 + "\n"
            for dp in yoy_data[-5:]:
                text += f"{dp.quarter_label}: {dp.yoy_label}\n"
        
        tk.Label(parent, text=text, font=(UI_CONFIG['font_family'], 10), 
                bg=self.colors['bg'], fg=self.colors['text'],
                justify='left', anchor='nw').pack(fill='both', expand=True, padx=10, pady=10)
    
    def _show_error(self, message: str) -> bool:
        """Show error message"""
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        tk.Label(self.parent_frame, text=f"❌ {message}", font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['frame'], fg=self.colors['error'], justify='center').pack(expand=True)
        return True


class CashFlowTab:
    """FCF tab container with enhanced scrolling support"""
    
    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        self.parent_frame = parent_frame
        self.ticker = ticker
        self.colors = {'bg': '#2b2b2b', 'text': '#ffffff', 'error': '#F44336'}
        self.data_loaded = False

    def update_data(self, financial_data: List[Any], ticker: str = None, data_source_info: Dict = None):
        """Update with financial data"""
        if ticker:
            self.ticker = ticker
        
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        try:
            chart = CashFlowChart(self.parent_frame, self.ticker)
            self.data_loaded = chart.create_chart(financial_data)
        except Exception as e:
            tk.Label(self.parent_frame, text=f"❌ FCF Error\n\n{e}",
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                    fg=self.colors['error'], justify='center').pack(expand=True)

    def show_placeholder(self):
        """Show placeholder"""
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.parent_frame, 
                text="💰 Select a stock to view Free Cash Flow analysis\n\n📊 Features:\n• Separated data processing\n• Operating CF - CapEx calculation\n• Year-over-Year analysis\n• Interactive tooltips\n• Enhanced scrolling support",
                font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'], fg=self.colors['text'], 
                justify='center').pack(expand=True)


print("📊 Enhanced CashFlow Chart loaded with separated data processing")