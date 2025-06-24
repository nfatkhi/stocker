# components/charts/cashflow_chart.py - Streamlined FCF chart with enhanced trackpad scrolling

import tkinter as tk
from tkinter import ttk
import math
from typing import List, Dict, Any, Tuple, NamedTuple

try:
    from .base_chart import FinancialBarChart
except ImportError:
    from .base_chart import FinancialBarChart

try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {'font_family': 'Arial', 'font_size': 10}


class CashflowDataPoint(NamedTuple):
    """Financial quarter data with YoY metrics"""
    quarter_label: str
    date: str
    fcf_dollars: float
    yoy_change_pct: float = float('nan')
    yoy_label: str = "N/A"
    yoy_description: str = "No previous year quarter"


class CashFlowChart(FinancialBarChart):
    """FCF chart with YoY analysis and enhanced scrolling"""
    
    MAX_QUARTERS = 12
    YOY_CAP = 500
    
    COLORS = {
        'positive': '#4CAF50', 'negative': '#F44336', 'neutral': '#9E9E9E',
        'yoy_growth': '#00C851', 'yoy_decline': '#FF4444', 'yoy_neutral': '#33B5E5'
    }

    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        super().__init__(parent_frame, ticker, **kwargs)
    
    def get_chart_title(self) -> str:
        return "Free Cash Flow Analysis"
    
    def get_y_label(self) -> str:
        return "Free Cash Flow (Millions $)"

    def create_chart(self, financial_data: List[Any]) -> bool:
        """Create 3-section scrollable FCF analysis with enhanced scrolling"""
        if not financial_data:
            return self._show_error("No financial data provided")
        
        processed_data = self._process_data(financial_data)
        if not processed_data:
            return self._show_error("No meaningful FCF data available")
        
        return self._create_scrollable_layout(processed_data)
    
    def _process_data(self, raw_data: List[Any]) -> List[CashflowDataPoint]:
        """Process raw data into structured format with YoY calculations"""
        data_points = []
        
        # Extract FCF data
        for financial in reversed(raw_data[:self.MAX_QUARTERS]):
            fcf = float(financial.cash) if hasattr(financial, 'cash') and financial.cash != 0 else float('nan')
            data_points.append(CashflowDataPoint(
                quarter_label=self.parse_quarter_label(financial.date),
                date=financial.date,
                fcf_dollars=fcf
            ))
        
        # Calculate YoY changes (compare with same quarter previous year)
        processed = []
        for i, dp in enumerate(data_points):
            # Look for same quarter previous year (4 quarters back)
            yoy_index = i - 4
            if yoy_index >= 0 and yoy_index < len(data_points):
                prev_year_val = data_points[yoy_index].fcf_dollars
                curr_val = dp.fcf_dollars
                
                if math.isnan(curr_val) or math.isnan(prev_year_val):
                    yoy_pct, yoy_label, yoy_desc = float('nan'), "N/A", "Insufficient data"
                elif prev_year_val == 0:
                    yoy_pct, yoy_label, yoy_desc = float('inf'), "New+", f"${curr_val/1e6:.1f}M from $0"
                else:
                    yoy_pct = ((curr_val - prev_year_val) / abs(prev_year_val)) * 100
                    yoy_label = f"{yoy_pct:+.1f}%" if abs(yoy_pct) <= 999 else f"{yoy_pct/100:+.0f}x"
                    prev_fmt = f"${prev_year_val/1e6:.1f}M"
                    curr_fmt = f"${curr_val/1e6:.1f}M"
                    yoy_desc = f"{prev_fmt} → {curr_fmt} (vs {data_points[yoy_index].quarter_label})"
                
                processed.append(dp._replace(
                    yoy_change_pct=yoy_pct,
                    yoy_label=yoy_label,
                    yoy_description=yoy_desc
                ))
            else:
                processed.append(dp)
        
        return [d for d in processed if not math.isnan(d.fcf_dollars)]
    
    def _create_scrollable_layout(self, data: List[CashflowDataPoint]) -> bool:
        """Create scrollable 3-section layout using enhanced base chart scrolling"""
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Use base chart's enhanced scrollable container with trackpad support
        canvas, scrollbar, content_frame = self.create_scrollable_container(self.parent_frame)
        
        # Create the three sections in the content frame
        self._create_summary_section(content_frame, data)
        self._create_fcf_section(content_frame, data)
        self._create_yoy_section(content_frame, data)
        
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
            return "break"  # Prevent event from propagating
        
        def bind_to_widget_and_children(widget):
            """Recursively bind scroll events to widget and all children"""
            try:
                widget.bind("<MouseWheel>", scroll_handler)
                widget.bind("<Button-4>", scroll_handler) 
                widget.bind("<Button-5>", scroll_handler)
                
                # Bind to all children recursively
                for child in widget.winfo_children():
                    bind_to_widget_and_children(child)
            except tk.TclError:
                pass
        
        # Apply to all content
        bind_to_widget_and_children(content_frame)
    
    def _create_summary_section(self, parent: tk.Frame, data: List[CashflowDataPoint]):
        """Create summary cards"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=100)
        frame.pack(fill='x', pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=f"{self.ticker} - FCF Summary", font=(UI_CONFIG['font_family'], 12, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(5, 0))
        
        cards_frame = tk.Frame(frame, bg=self.colors['frame'])
        cards_frame.pack(fill='both', expand=True, padx=10, pady=(0, 5))
        
        latest_fcf = data[-1].fcf_dollars if data else 0
        avg_fcf = sum(d.fcf_dollars for d in data) / len(data) if data else 0
        recent_count = len([d for d in data if d.date.startswith(('2024', '2025'))])
        
        # Calculate growth if we have YoY data
        recent_growth = "N/A"
        if data:
            recent_yoy_data = [d for d in data[-4:] if not math.isnan(d.yoy_change_pct) and not math.isinf(d.yoy_change_pct)]
            if recent_yoy_data:
                avg_yoy = sum(d.yoy_change_pct for d in recent_yoy_data) / len(recent_yoy_data)
                recent_growth = f"{avg_yoy:+.1f}%"
        
        metrics = [
            ("Data Source", "Polygon.io", '#1976D2'),
            ("Latest FCF", f"${latest_fcf/1e6:.1f}M", self.colors['success']),
            ("Average FCF", f"${avg_fcf/1e6:.1f}M", self.colors['accent']),
            ("YoY Growth", recent_growth, '#2E7D32' if recent_growth != "N/A" and "+" in recent_growth else self.colors['warning'])
        ]
        
        for label, value, color in metrics:
            card = tk.Frame(cards_frame, bg=self.colors['bg'], relief='raised', bd=1)
            card.pack(side='left', fill='both', expand=True, padx=3)
            tk.Label(card, text=label, font=(UI_CONFIG['font_family'], 8), 
                    bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(3, 1))
            tk.Label(card, text=value, font=(UI_CONFIG['font_family'], 9, 'bold'), 
                    bg=self.colors['bg'], fg=color).pack(pady=(0, 3))
    
    def _create_fcf_section(self, parent: tk.Frame, data: List[CashflowDataPoint]):
        """Create main FCF chart"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=400)
        frame.pack(fill='both', expand=True, pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Free Cash Flow Trend", font=(UI_CONFIG['font_family'], 14, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        values = [d.fcf_dollars for d in data]
        quarters = [d.quarter_label for d in data]
        
        self.create_interactive_chart(content, values, quarters, f"{self.ticker} Free Cash Flow", 
                                     "Free Cash Flow", self.COLORS['positive'], "FCF")
    
    def _create_yoy_section(self, parent: tk.Frame, data: List[CashflowDataPoint]):
        """Create YoY analysis chart with consistent dark theme formatting"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=350)
        frame.pack(fill='both', expand=True)
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Year-over-Year FCF Analysis", 
                font=(UI_CONFIG['font_family'], 14, 'bold'), 
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        yoy_data = [d for d in data if not math.isnan(d.yoy_change_pct) and not math.isinf(d.yoy_change_pct)]
        
        if yoy_data:
            self._create_yoy_chart(content, yoy_data)
        else:
            tk.Label(content, text="❌ No YoY Data Available\nNeed at least 4 consecutive quarters for year-over-year comparison",
                    font=(UI_CONFIG['font_family'], 14), bg=self.colors['bg'], 
                    fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _create_yoy_chart(self, parent: tk.Frame, yoy_data: List[CashflowDataPoint]):
        """Create YoY matplotlib chart with consistent dark theme formatting"""
        try:
            values = [d.yoy_change_pct for d in yoy_data]
            quarters = [d.quarter_label for d in yoy_data]
            display_values = [max(-self.YOY_CAP, min(self.YOY_CAP, v)) for v in values]
            
            # Get sizing and fonts to match FCF chart
            chart_width, chart_height, _, _ = self.get_responsive_size()
            font_sizes = self.get_dynamic_font_sizes(chart_width)
            
            # Create figure with dark theme
            fig, ax = self.create_matplotlib_figure(chart_width, chart_height)
            
            # Color bars based on change - use consistent color scheme
            colors = [self.COLORS['yoy_growth'] if v > 5 else 
                     self.COLORS['yoy_decline'] if v < -5 else 
                     self.COLORS['yoy_neutral'] for v in values]
            
            bars = ax.bar(range(len(quarters)), display_values, color=colors, alpha=0.8, width=0.8)
            
            # Style chart to match FCF chart formatting
            ax.set_title(f'{self.ticker} Year-over-Year FCF Changes', 
                        color=self.colors['header'], fontweight='bold', fontsize=font_sizes['title'])
            ax.set_ylabel('YoY Change (%)', color=self.colors['text'], fontweight='bold', fontsize=font_sizes['label'])
            ax.set_xlabel('Quarter', color=self.colors['text'], fontweight='bold', fontsize=font_sizes['label'])
            
            # Set labels with consistent rotation
            rotation_angle = 45 if len(quarters) > 8 else 30
            ax.set_xticks(range(len(quarters)))
            ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right',
                              color=self.colors['text'], fontsize=font_sizes['tick'])
            
            # Reference lines with consistent styling (50% for FCF since it's more volatile)
            ax.axhline(y=0, color=self.colors['text'], linestyle='--', alpha=0.5, linewidth=2)
            ax.axhline(y=50, color=self.COLORS['yoy_growth'], linestyle=':', alpha=0.4)
            ax.axhline(y=-50, color=self.COLORS['yoy_decline'], linestyle=':', alpha=0.4)
            
            # Value labels with consistent styling
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
                text="💰 Select a stock to view Free Cash Flow analysis\n\n📊 Features:\n• FCF trend chart\n• Year-over-Year analysis\n• Interactive tooltips\n• Enhanced scrolling support",
                font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'], fg=self.colors['text'], 
                justify='center').pack(expand=True)


print("📊 Enhanced CashFlow Chart loaded with YoY analysis and optimized scrolling")