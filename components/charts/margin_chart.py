# components/charts/margin_chart.py - Triple margin analysis with YoY trends

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


class MarginDataPoint(NamedTuple):
    """Margin data for one quarter with YoY metrics"""
    quarter_label: str
    date: str
    # Revenue and profit amounts
    revenue_dollars: float
    gross_profit_dollars: float
    operating_income_dollars: float
    net_income_dollars: float
    # Calculated margin percentages
    gross_margin_pct: float
    operating_margin_pct: float
    net_margin_pct: float
    # YoY changes for gross margin
    gross_margin_yoy_change: float = float('nan')
    gross_margin_yoy_label: str = "N/A"


class MarginChart(FinancialBarChart):
    """Triple margin chart showing Gross, Operating, and Net margins with trends"""
    
    MAX_QUARTERS = 12
    
    COLORS = {
        'gross_margin': '#4CAF50',     # Green - highest margin
        'operating_margin': '#2196F3', # Blue - middle margin  
        'net_margin': '#FF9800',       # Orange - lowest margin
        'yoy_growth': '#00C851',
        'yoy_decline': '#FF4444',
        'yoy_neutral': '#33B5E5',
        'background': '#2b2b2b',
        'text': '#ffffff'
    }

    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        super().__init__(parent_frame, ticker, **kwargs)
    
    def get_chart_title(self) -> str:
        return "Profitability Margin Analysis"
    
    def get_y_label(self) -> str:
        return "Margin Percentage (%)"

    def create_chart(self, financial_data: List[Any]) -> bool:
        """Create 3-section scrollable margin analysis"""
        if not financial_data:
            return self._show_error("No financial data provided")
        
        processed_data = self._process_data(financial_data)
        if not processed_data:
            return self._show_error("No meaningful margin data available")
        
        return self._create_scrollable_layout(processed_data)
    
    def _process_data(self, raw_data: List[Any]) -> List[MarginDataPoint]:
        """Process raw data into margin analysis with YoY calculations"""
        print(f"🔄 Processing {len(raw_data)} quarters - Converting to margin analysis")
        
        # Convert cumulative quarterly data to actual quarterly amounts
        conversion_success = False
        try:
            from .quarterly_converter import convert_financial_data_to_actual_quarters
            converted_data = convert_financial_data_to_actual_quarters(raw_data[:self.MAX_QUARTERS])
            conversion_success = True
            print(f"✅ Converted cumulative data to actual quarterly amounts")
        except ImportError:
            print(f"⚠️ Quarterly converter not available, using raw data (may be cumulative)")
            converted_data = raw_data[:self.MAX_QUARTERS]
        
        # Pass conversion success to chart creation
        self.conversion_success = conversion_success
        
        data_points = []
        
        # Extract margin data from converted (actual quarterly) data
        for financial in reversed(converted_data):
            # Use XBRL quarter information if available, otherwise parse date
            xbrl_quarter = getattr(financial, 'document_fiscal_period_focus', None)
            xbrl_year = getattr(financial, 'document_fiscal_year_focus', None)
            
            if xbrl_quarter and xbrl_year:
                quarter_label = f"{xbrl_year}{xbrl_quarter}"
                print(f"   📋 Using XBRL quarter: {quarter_label}")
            else:
                quarter_label = self.parse_quarter_label(financial.date)
                print(f"   📅 Using parsed quarter: {quarter_label}")
            
            # Extract financial amounts - use standard QuarterlyFinancials fields
            revenue = self._safe_float(financial.revenue)
            gross_profit = self._safe_float(getattr(financial, 'gross_profit', 0))
            operating_income = self._safe_float(getattr(financial, 'operating_income', 0))
            net_income = self._safe_float(financial.net_income)
            
            # Debug the extraction
            print(f"   📊 Extracted: Revenue ${revenue/1e6:.1f}M, Gross ${gross_profit/1e6:.1f}M, Operating ${operating_income/1e6:.1f}M, Net ${net_income/1e6:.1f}M")
            
            # Calculate margin percentages
            gross_margin_pct = (gross_profit / revenue * 100) if revenue > 0 else float('nan')
            operating_margin_pct = (operating_income / revenue * 100) if revenue > 0 else float('nan')
            net_margin_pct = (net_income / revenue * 100) if revenue > 0 else float('nan')
            
            data_points.append(MarginDataPoint(
                quarter_label=quarter_label,
                date=financial.date,
                revenue_dollars=revenue,
                gross_profit_dollars=gross_profit,
                operating_income_dollars=operating_income,
                net_income_dollars=net_income,
                gross_margin_pct=gross_margin_pct,
                operating_margin_pct=operating_margin_pct,
                net_margin_pct=net_margin_pct
            ))
            
            if not math.isnan(gross_margin_pct):
                print(f"   📊 {quarter_label}: Gross {gross_margin_pct:.1f}%, Operating {operating_margin_pct:.1f}%, Net {net_margin_pct:.1f}%")
        
        # Calculate YoY changes for gross margin (most important)
        processed = []
        for i, dp in enumerate(data_points):
            # Look for same quarter previous year (4 quarters back)
            yoy_index = i - 4
            if yoy_index >= 0 and yoy_index < len(data_points):
                prev_year_margin = data_points[yoy_index].gross_margin_pct
                curr_margin = dp.gross_margin_pct
                
                if math.isnan(curr_margin) or math.isnan(prev_year_margin):
                    yoy_change, yoy_label = float('nan'), "N/A"
                else:
                    yoy_change = curr_margin - prev_year_margin  # Percentage point change
                    yoy_label = f"{yoy_change:+.1f}pp"  # pp = percentage points
                
                processed.append(dp._replace(
                    gross_margin_yoy_change=yoy_change,
                    gross_margin_yoy_label=yoy_label
                ))
            else:
                processed.append(dp)
        
        return [d for d in processed if not math.isnan(d.gross_margin_pct)]
    
    def _safe_float(self, value, default=0.0):
        """Safely convert value to float"""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _create_scrollable_layout(self, data: List[MarginDataPoint]) -> bool:
        """Create scrollable 3-section layout for margin analysis"""
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Use base chart's enhanced scrollable container
        canvas, scrollbar, content_frame = self.create_scrollable_container(self.parent_frame)
        
        # Create the three sections
        self._create_summary_section(content_frame, data)
        self._create_margin_trends_section(content_frame, data)
        self._create_margin_yoy_section(content_frame, data)
        
        # Update scroll region
        self.parent_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Ensure scrolling works everywhere
        self._ensure_all_widgets_scroll(content_frame, canvas)
        
        return True
    
    def _ensure_all_widgets_scroll(self, content_frame: tk.Frame, canvas: tk.Canvas):
        """Ensure all widgets can scroll the canvas"""
        def scroll_handler(event):
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
            try:
                widget.bind("<MouseWheel>", scroll_handler)
                widget.bind("<Button-4>", scroll_handler) 
                widget.bind("<Button-5>", scroll_handler)
                
                for child in widget.winfo_children():
                    bind_to_widget_and_children(child)
            except tk.TclError:
                pass
        
        bind_to_widget_and_children(content_frame)
    
    def _create_summary_section(self, parent: tk.Frame, data: List[MarginDataPoint]):
        """Create margin summary cards"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=100)
        frame.pack(fill='x', pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=f"{self.ticker} - Profitability Summary", 
                font=(UI_CONFIG['font_family'], 12, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(5, 0))
        
        cards_frame = tk.Frame(frame, bg=self.colors['frame'])
        cards_frame.pack(fill='both', expand=True, padx=10, pady=(0, 5))
        
        if data:
            latest = data[-1]
            avg_gross = sum(d.gross_margin_pct for d in data if not math.isnan(d.gross_margin_pct)) / len(data)
            avg_operating = sum(d.operating_margin_pct for d in data if not math.isnan(d.operating_margin_pct)) / len(data)
            avg_net = sum(d.net_margin_pct for d in data if not math.isnan(d.net_margin_pct)) / len(data)
            
            metrics = [
                ("Latest Gross", f"{latest.gross_margin_pct:.1f}%", self.COLORS['gross_margin']),
                ("Latest Operating", f"{latest.operating_margin_pct:.1f}%", self.COLORS['operating_margin']),
                ("Latest Net", f"{latest.net_margin_pct:.1f}%", self.COLORS['net_margin']),
                ("Avg Gross", f"{avg_gross:.1f}%", self.colors['text'])
            ]
        else:
            metrics = [("No Data", "N/A", self.colors['warning'])]
        
        for label, value, color in metrics:
            card = tk.Frame(cards_frame, bg=self.colors['bg'], relief='raised', bd=1)
            card.pack(side='left', fill='both', expand=True, padx=3)
            tk.Label(card, text=label, font=(UI_CONFIG['font_family'], 8), 
                    bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(3, 1))
            tk.Label(card, text=value, font=(UI_CONFIG['font_family'], 9, 'bold'), 
                    bg=self.colors['bg'], fg=color).pack(pady=(0, 3))
    
    def _create_margin_trends_section(self, parent: tk.Frame, data: List[MarginDataPoint]):
        """Create triple margin trend chart"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=400)
        frame.pack(fill='both', expand=True, pady=(0, 10))
        frame.pack_propagate(False)
        
        conversion_success = getattr(self, 'conversion_success', False)
        title_suffix = "(Actual Amounts)" if conversion_success else "(Raw Data - May Be Cumulative)"
        
        tk.Label(frame, text=f"Triple Margin Trends {title_suffix}", 
                font=(UI_CONFIG['font_family'], 14, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self._create_triple_margin_chart(content, data)
    
    def _create_triple_margin_chart(self, parent: tk.Frame, data: List[MarginDataPoint]):
        """Create matplotlib chart showing all three margins"""
        try:
            quarters = [d.quarter_label for d in data]
            gross_margins = [d.gross_margin_pct for d in data]
            operating_margins = [d.operating_margin_pct for d in data]
            net_margins = [d.net_margin_pct for d in data]
            
            # Get sizing and fonts
            chart_width, chart_height, _, _ = self.get_responsive_size()
            font_sizes = self.get_dynamic_font_sizes(chart_width)
            
            # Create figure with dark theme
            fig, ax = self.create_matplotlib_figure(chart_width, chart_height)
            
            # Create line chart for margins
            x_positions = range(len(quarters))
            
            # Plot the three margin lines
            ax.plot(x_positions, gross_margins, 
                   color=self.COLORS['gross_margin'], linewidth=3, marker='o', 
                   markersize=6, label='Gross Margin', alpha=0.9)
            ax.plot(x_positions, operating_margins, 
                   color=self.COLORS['operating_margin'], linewidth=3, marker='s', 
                   markersize=6, label='Operating Margin', alpha=0.9)
            ax.plot(x_positions, net_margins, 
                   color=self.COLORS['net_margin'], linewidth=3, marker='^', 
                   markersize=6, label='Net Margin', alpha=0.9)
            
            # Style chart
            ax.set_title(f'{self.ticker} Profitability Margins Over Time', 
                        color=self.colors['header'], fontweight='bold', fontsize=font_sizes['title'])
            ax.set_ylabel('Margin Percentage (%)', color=self.colors['text'], 
                         fontweight='bold', fontsize=font_sizes['label'])
            ax.set_xlabel('Quarter', color=self.colors['text'], 
                         fontweight='bold', fontsize=font_sizes['label'])
            
            # Set x-axis labels
            rotation_angle = 45 if len(quarters) > 8 else 30
            ax.set_xticks(x_positions)
            ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right',
                              color=self.colors['text'], fontsize=font_sizes['tick'])
            
            # Add legend
            ax.legend(loc='upper left', fancybox=True, shadow=True, 
                     facecolor=self.colors['frame'], edgecolor=self.colors['text'])
            
            # Add grid
            ax.grid(True, alpha=0.3, color=self.colors['text'])
            
            # Style axis
            self.style_axis(ax, font_sizes)
            
            # Set figure colors
            ax.set_facecolor(self.colors['frame'])
            fig.patch.set_facecolor(self.colors['frame'])
            
            # Create canvas
            canvas = self.create_canvas(fig, parent)
            canvas.get_tk_widget().pack(fill='both', expand=True, pady=5)
            
        except Exception as e:
            self._show_margin_error(parent, str(e))
    
    def _create_margin_yoy_section(self, parent: tk.Frame, data: List[MarginDataPoint]):
        """Create YoY gross margin change analysis"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=300)
        frame.pack(fill='both', expand=True)
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Gross Margin Year-over-Year Changes", 
                font=(UI_CONFIG['font_family'], 14, 'bold'), 
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        yoy_data = [d for d in data if not math.isnan(d.gross_margin_yoy_change)]
        
        if yoy_data:
            self._create_margin_yoy_chart(content, yoy_data)
        else:
            tk.Label(content, text="❌ No YoY Margin Data Available\nNeed at least 4 consecutive quarters",
                    font=(UI_CONFIG['font_family'], 14), bg=self.colors['bg'], 
                    fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _create_margin_yoy_chart(self, parent: tk.Frame, yoy_data: List[MarginDataPoint]):
        """Create YoY margin change bar chart"""
        try:
            quarters = [d.quarter_label for d in yoy_data]
            yoy_changes = [d.gross_margin_yoy_change for d in yoy_data]
            
            # Get sizing and fonts
            chart_width, chart_height, _, _ = self.get_responsive_size()
            font_sizes = self.get_dynamic_font_sizes(chart_width)
            
            # Create figure
            fig, ax = self.create_matplotlib_figure(chart_width, chart_height)
            
            # Color bars based on change
            colors = [self.COLORS['yoy_growth'] if change > 0 else 
                     self.COLORS['yoy_decline'] if change < 0 else 
                     self.COLORS['yoy_neutral'] for change in yoy_changes]
            
            bars = ax.bar(range(len(quarters)), yoy_changes, color=colors, alpha=0.8)
            
            # Style chart
            ax.set_title(f'{self.ticker} Gross Margin YoY Changes (Percentage Points)', 
                        color=self.colors['header'], fontweight='bold', fontsize=font_sizes['title'])
            ax.set_ylabel('Change (Percentage Points)', color=self.colors['text'], 
                         fontweight='bold', fontsize=font_sizes['label'])
            ax.set_xlabel('Quarter', color=self.colors['text'], 
                         fontweight='bold', fontsize=font_sizes['label'])
            
            # Set labels
            rotation_angle = 45 if len(quarters) > 8 else 30
            ax.set_xticks(range(len(quarters)))
            ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right',
                              color=self.colors['text'], fontsize=font_sizes['tick'])
            
            # Add zero line
            ax.axhline(y=0, color=self.colors['text'], linestyle='--', alpha=0.5, linewidth=2)
            
            # Add value labels
            for bar, dp in zip(bars, yoy_data):
                height = bar.get_height()
                label_y = height + (0.5 if height >= 0 else -0.8)
                ax.text(bar.get_x() + bar.get_width()/2., label_y,
                       dp.gross_margin_yoy_label, ha='center', 
                       va='bottom' if height >= 0 else 'top',
                       color=self.colors['text'], fontsize=font_sizes['value'], fontweight='bold')
            
            # Apply styling
            self.style_axis(ax, font_sizes)
            ax.set_facecolor(self.colors['frame'])
            fig.patch.set_facecolor(self.colors['frame'])
            
            canvas = self.create_canvas(fig, parent)
            canvas.get_tk_widget().pack(fill='both', expand=True, pady=5)
            
        except Exception as e:
            self._show_yoy_fallback(parent, yoy_data, str(e))
    
    def _show_margin_error(self, parent: tk.Frame, error_message: str):
        """Show margin chart error"""
        tk.Label(parent, text=f"❌ Margin Chart Error\n\n{error_message}",
                font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _show_yoy_fallback(self, parent: tk.Frame, yoy_data: List[MarginDataPoint], error: str):
        """Show text-based YoY display"""
        text = f"📊 Gross Margin YoY Changes - {len(yoy_data)} Quarters\n\n"
        if yoy_data:
            latest = yoy_data[-1]
            text += f"Latest: {latest.quarter_label} - {latest.gross_margin_yoy_label}\n\n"
            text += "Recent Changes:\n" + "-"*30 + "\n"
            for dp in yoy_data[-5:]:
                text += f"{dp.quarter_label}: {dp.gross_margin_yoy_label}\n"
        
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


class MarginTab:
    """Margin analysis tab container"""
    
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
            chart = MarginChart(self.parent_frame, self.ticker)
            self.data_loaded = chart.create_chart(financial_data)
        except Exception as e:
            tk.Label(self.parent_frame, text=f"❌ Margin Analysis Error\n\n{e}",
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                    fg=self.colors['error'], justify='center').pack(expand=True)

    def show_placeholder(self):
        """Show placeholder"""
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.parent_frame, 
                text="📊 Select a stock to view Margin analysis\n\n📈 Features:\n• Gross, Operating, Net margin trends\n• Year-over-Year margin changes\n• Profitability insights\n• Interactive trend lines",
                font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'], fg=self.colors['text'], 
                justify='center').pack(expand=True)


print("📊 Triple Margin Chart loaded with profitability analysis")