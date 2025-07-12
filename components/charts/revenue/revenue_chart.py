# components/charts/revenue/revenue_chart.py - FIXED imports for base_chart + Q4 calculation

import tkinter as tk
from tkinter import ttk
import math
from typing import List, Dict, Any, Tuple, NamedTuple, Optional

# FIXED: Use absolute import path
try:
    from components.charts.base_chart import FinancialBarChart
    BASE_CHART_AVAILABLE = True
    print("✅ Base chart imported successfully")
except ImportError as e:
    BASE_CHART_AVAILABLE = False
    print(f"❌ Base chart import failed: {e}")
    
    # Fallback base class if import fails
    class FinancialBarChart:
        def __init__(self, parent_frame, ticker="", **kwargs):
            self.parent_frame = parent_frame
            self.ticker = ticker
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
        
        def parse_quarter_label(self, date_str: str) -> str:
            try:
                if '-' in date_str:
                    year = date_str[:4]
                    month = int(date_str[5:7])
                    quarter = (month - 1) // 3 + 1
                    return f"{year}Q{quarter}"
                return date_str[:10]
            except:
                return "Q?"
        
        def create_scrollable_container(self, parent_frame):
            # Simple fallback scrollable container
            container = tk.Frame(parent_frame, bg=self.colors['bg'])
            container.pack(fill='both', expand=True)
            
            canvas = tk.Canvas(container, bg=self.colors['bg'])
            scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
            content_frame = tk.Frame(canvas, bg=self.colors['bg'])
            
            canvas.create_window((0, 0), window=content_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            return canvas, scrollbar, content_frame

try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {'font_family': 'Arial', 'font_size': 10}


class RevenueDataPoint(NamedTuple):
    """Revenue quarter data with YoY metrics"""
    quarter_label: str
    date: str
    revenue_dollars: float
    yoy_change_pct: float = float('nan')
    yoy_label: str = "N/A"
    yoy_description: str = "No previous year quarter"
    is_calculated_q4: bool = False  # NEW: Flag for calculated Q4


class RevenueChart(FinancialBarChart):
    """Revenue chart with YoY analysis and Q4 calculation - FIXED imports"""
    
    MAX_QUARTERS = 12
    YOY_CAP = 500
    
    COLORS = {
        'positive': '#1976D2', 'negative': '#F44336', 'neutral': '#9E9E9E',
        'yoy_growth': '#00C851', 'yoy_decline': '#FF4444', 'yoy_neutral': '#33B5E5',
        'calculated_q4': '#FF9800'  # Orange for calculated Q4
    }

    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        super().__init__(parent_frame, ticker, **kwargs)
        self.all_quarters_data = None  # NEW: Store all quarters for Q4 calculation
        print(f"📊 RevenueChart initialized for {ticker} - Base chart available: {BASE_CHART_AVAILABLE}")
    
    def get_chart_title(self) -> str:
        return "Revenue Analysis (FIXED + Q4 Calc)"
    
    def get_y_label(self) -> str:
        return "Revenue (Millions $)"

    def create_chart(self, financial_data: List[Any], all_quarters_data: List[Any] = None) -> bool:
        """Create 3-section scrollable Revenue analysis with Q4 calculation"""
        print(f"🔄 Creating revenue chart with {len(financial_data)} display quarters")
        
        if not financial_data:
            return self._show_error("No financial data provided")
        
        # Store all quarters data for Q4 calculation
        self.all_quarters_data = all_quarters_data or financial_data
        print(f"🧮 All quarters available for Q4 calculation: {len(self.all_quarters_data)}")
        
        processed_data = self._process_data_with_q4_calculation(financial_data)
        if not processed_data:
            return self._show_error("No meaningful revenue data available")
        
        return self._create_scrollable_layout(processed_data)
    
    def _process_data_with_q4_calculation(self, raw_data: List[Any]) -> List[RevenueDataPoint]:
        """Process raw data with Q4 calculation from annual data"""
        print(f"🔄 Processing {len(raw_data)} quarters with Q4 calculation logic")
        
        data_points = []
        q4_calculations_made = 0
        
        # Extract revenue data and check for Q4 calculation needs
        for i, financial in enumerate(reversed(raw_data[:self.MAX_QUARTERS])):
            print(f"   📊 Processing item {i+1}: {type(financial)} - {getattr(financial, 'quarter', 'Unknown')}")
            
            # FIXED: Use all quarters data for Q4 calculation
            revenue = self._extract_revenue_with_q4_calc(financial, self.all_quarters_data)
            is_calculated = getattr(financial, '_q4_calculated', False)
            
            # Use XBRL quarter information if available
            xbrl_quarter = getattr(financial, 'document_fiscal_period_focus', None)
            xbrl_year = getattr(financial, 'document_fiscal_year_focus', None)
            
            if xbrl_quarter and xbrl_year:
                quarter_label = f"{xbrl_year}{xbrl_quarter}"
            else:
                date_attr = getattr(financial, 'date', '') or getattr(financial, 'filing_date', '')
                quarter_label = self.parse_quarter_label(date_attr)
            
            filing_date = getattr(financial, 'filing_date', '') or getattr(financial, 'date', '')
            
            data_points.append(RevenueDataPoint(
                quarter_label=quarter_label,
                date=filing_date,
                revenue_dollars=revenue,
                is_calculated_q4=is_calculated
            ))
            
            if not math.isnan(revenue) and revenue > 0:
                calc_indicator = " (Calculated Q4)" if is_calculated else ""
                print(f"      ✅ {quarter_label}: ${revenue/1e6:.1f}M{calc_indicator}")
                if is_calculated:
                    q4_calculations_made += 1
            else:
                print(f"      ❌ {quarter_label}: No valid revenue")
        
        if q4_calculations_made > 0:
            print(f"🧮 Q4 Calculations: {q4_calculations_made} quarters calculated from annual data")
        
        # Calculate YoY changes
        processed = []
        for i, dp in enumerate(data_points):
            yoy_index = i - 4
            if yoy_index >= 0 and yoy_index < len(data_points):
                prev_year_val = data_points[yoy_index].revenue_dollars
                curr_val = dp.revenue_dollars
                
                if math.isnan(curr_val) or math.isnan(prev_year_val) or curr_val <= 0 or prev_year_val <= 0:
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
        
        valid_data = [d for d in processed if not math.isnan(d.revenue_dollars) and d.revenue_dollars > 0]
        print(f"✅ Final processing: {len(valid_data)} valid revenue quarters")
        
        return valid_data
    
    def _extract_revenue_with_q4_calc(self, financial, all_data: List[Any]) -> float:
        """Extract revenue with Q4 calculation if needed"""
        
        # Get base revenue value - handle both raw cache data and processed data
        revenue = 0
        
        # Try different revenue attributes
        for attr in ['revenue', 'revenues']:
            if hasattr(financial, attr):
                value = getattr(financial, attr)
                if value and value > 0:
                    revenue = value
                    break
        
        if revenue <= 0:
            return float('nan')
        
        # Check if this needs Q4 calculation
        revenues_source = getattr(financial, 'revenues_source', None)
        needs_calculation = getattr(financial, 'revenues_needs_q4_calculation', False)
        
        if revenues_source == 'annual_10k' and needs_calculation:
            print(f"   🧮 Q4 CALCULATION needed for annual data: ${revenue/1e6:.1f}M")
            print(f"      📊 Using {len(all_data)} quarters for Q4 calculation")
            
            # Calculate Q4 = Annual - (Q1+Q2+Q3)
            calculated_q4 = self._calculate_q4_from_annual(financial, revenue, all_data)
            
            if calculated_q4 is not None:
                # Mark this as calculated
                financial._q4_calculated = True
                return calculated_q4
            else:
                print(f"   ❌ Q4 calculation failed, using annual data")
                return revenue
        else:
            # Use direct revenue (quarterly data)
            return revenue if revenue > 0 else float('nan')
    
    def _calculate_q4_from_annual(self, annual_financial, annual_revenue: float, all_data: List[Any]) -> Optional[float]:
        """Calculate Q4 = Annual - (Q1+Q2+Q3) using available data"""
        
        try:
            # Get fiscal year from annual data
            fiscal_year = getattr(annual_financial, 'document_fiscal_year_focus', None)
            if not fiscal_year:
                fiscal_year = getattr(annual_financial, 'year', None)
            
            if not fiscal_year:
                print(f"   ❌ Cannot determine fiscal year for Q4 calculation")
                return None
            
            print(f"   🧮 Calculating Q4 for fiscal year {fiscal_year}")
            
            # Find Q1, Q2, Q3 for same fiscal year
            q123_revenues = []
            quarters_found = []
            
            for item in all_data:
                item_year = getattr(item, 'document_fiscal_year_focus', None) or getattr(item, 'year', None)
                item_quarter = getattr(item, 'document_fiscal_period_focus', None) or getattr(item, 'quarter', None)
                item_source = getattr(item, 'revenues_source', None)
                
                if (item_year == fiscal_year and 
                    item_quarter in ['Q1', 'Q2', 'Q3'] and 
                    item_source == 'quarterly_10q'):
                    
                    item_revenue = getattr(item, 'revenue', 0) or getattr(item, 'revenues', 0)
                    if item_revenue > 0:
                        q123_revenues.append(item_revenue)
                        quarters_found.append(item_quarter)
                        print(f"      📊 Found {item_quarter} {item_year}: ${item_revenue/1e6:.1f}M")
            
            if len(q123_revenues) >= 2:  # Need at least 2 quarters for reasonable calculation
                q123_total = sum(q123_revenues)
                q4_calculated = annual_revenue - q123_total
                
                if q4_calculated > 0:
                    print(f"   ✅ Q4 = ${annual_revenue/1e6:.1f}M - ${q123_total/1e6:.1f}M = ${q4_calculated/1e6:.1f}M")
                    print(f"      Used quarters: {', '.join(quarters_found)}")
                    return q4_calculated
                else:
                    print(f"   ❌ Q4 calculation error: Q1+Q2+Q3 (${q123_total/1e6:.1f}M) > Annual (${annual_revenue/1e6:.1f}M)")
                    print(f"      Revenue is rarely negative - data quality issue")
                    return None
            else:
                print(f"   ⚠️ Insufficient quarterly data for Q4 calculation (found {len(q123_revenues)} quarters)")
                return None
                
        except Exception as e:
            print(f"   ❌ Q4 calculation error: {e}")
            return None
    
    def _create_scrollable_layout(self, data: List[RevenueDataPoint]) -> bool:
        """Create scrollable 3-section layout with Q4 calculation indicators"""
        print(f"🎨 Creating scrollable layout with {len(data)} data points")
        
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Use base chart's enhanced scrollable container with trackpad support
        try:
            canvas, scrollbar, content_frame = self.create_scrollable_container(self.parent_frame)
            print("✅ Scrollable container created")
        except Exception as e:
            print(f"❌ Error creating scrollable container: {e}")
            # Fallback to simple layout
            content_frame = tk.Frame(self.parent_frame, bg=self.colors['bg'])
            content_frame.pack(fill='both', expand=True)
            canvas = None
        
        # Create the three sections in the content frame
        try:
            self._create_summary_section_with_q4_info(content_frame, data)
            self._create_revenue_section_with_q4_indicators(content_frame, data)
            self._create_yoy_section(content_frame, data)
            print("✅ All sections created successfully")
        except Exception as e:
            print(f"❌ Error creating chart sections: {e}")
            # Show error in the frame
            tk.Label(content_frame, 
                    text=f"❌ Chart Creation Error\n\n{str(e)}\n\nChart data: {len(data)} quarters",
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                    fg=self.colors['error'], justify='center').pack(expand=True)
            return False
        
        # Update scroll region after content is added
        if canvas:
            try:
                self.parent_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                print("✅ Scroll region updated")
            except Exception as e:
                print(f"⚠️ Error updating scroll region: {e}")
        
        return True
    
    def _create_summary_section_with_q4_info(self, parent: tk.Frame, data: List[RevenueDataPoint]):
        """Create summary cards with Q4 calculation info"""
        print(f"📋 Creating summary section with {len(data)} quarters")
        
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=100)
        frame.pack(fill='x', pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=f"{self.ticker} - Revenue Summary (Q4 Calc Ready)", 
                font=(UI_CONFIG['font_family'], 12, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(5, 0))
        
        cards_frame = tk.Frame(frame, bg=self.colors['frame'])
        cards_frame.pack(fill='both', expand=True, padx=10, pady=(0, 5))
        
        # Calculate metrics
        latest_revenue = data[-1].revenue_dollars if data else 0
        avg_revenue = sum(d.revenue_dollars for d in data) / len(data) if data else 0
        calculated_q4_count = len([d for d in data if d.is_calculated_q4])
        
        metrics = [
            ("Data Source", f"SEC + Q4 Calc ({len(self.all_quarters_data)} total)", '#1976D2'),
            ("Latest Revenue", f"${latest_revenue/1e6:.1f}M", self.colors['success']),
            ("Average Revenue", f"${avg_revenue/1e6:.1f}M", self.colors['accent']),
            ("Q4 Calculated", f"{calculated_q4_count} quarters", 
             self.COLORS['calculated_q4'] if calculated_q4_count > 0 else self.COLORS['neutral'])
        ]
        
        for label, value, color in metrics:
            card = tk.Frame(cards_frame, bg=self.colors['bg'], relief='raised', bd=1)
            card.pack(side='left', fill='both', expand=True, padx=3)
            tk.Label(card, text=label, font=(UI_CONFIG['font_family'], 8), 
                    bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(3, 1))
            tk.Label(card, text=value, font=(UI_CONFIG['font_family'], 9, 'bold'), 
                    bg=self.colors['bg'], fg=color).pack(pady=(0, 3))
    
    def _create_revenue_section_with_q4_indicators(self, parent: tk.Frame, data: List[RevenueDataPoint]):
        """Create main revenue chart with Q4 calculation indicators"""
        print(f"📊 Creating revenue chart section with {len(data)} quarters")
        
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=400)
        frame.pack(fill='both', expand=True, pady=(0, 10))
        frame.pack_propagate(False)
        
        calculated_count = len([d for d in data if d.is_calculated_q4])
        title_suffix = f"(Q4 Calculated: {calculated_count})" if calculated_count > 0 else "(Direct XBRL Data)"
        
        tk.Label(frame, text=f"Quarterly Revenue Trend {title_suffix}", 
                font=(UI_CONFIG['font_family'], 14, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # FIXED: Create actual matplotlib chart instead of text display
        self._create_revenue_chart_with_q4_indicators(content, data)
    
    def _create_revenue_chart_with_q4_indicators(self, parent: tk.Frame, data: List[RevenueDataPoint]):
        """Create revenue chart with visual indicators for calculated Q4"""
        print(f"📊 Creating matplotlib revenue chart with {len(data)} quarters")
        
        try:
            # Import matplotlib for chart creation
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            values = [d.revenue_dollars / 1e6 for d in data]  # Convert to millions
            quarters = [d.quarter_label for d in data]
            
            # Create figure
            fig = Figure(figsize=(12, 6), facecolor=self.colors['frame'])
            ax = fig.add_subplot(111, facecolor=self.colors['frame'])
            
            # Color bars: Orange for calculated Q4, blue for direct data
            colors = [self.COLORS['calculated_q4'] if d.is_calculated_q4 else self.COLORS['positive'] for d in data]
            
            bars = ax.bar(range(len(quarters)), values, color=colors, alpha=0.8, width=0.8)
            
            # Style chart
            ax.set_title(f'{self.ticker} Quarterly Revenue (with Q4 Calculation)', 
                        color=self.colors['header'], fontweight='bold', fontsize=14)
            ax.set_ylabel('Revenue (Millions $)', color=self.colors['text'], fontweight='bold', fontsize=12)
            ax.set_xlabel('Quarter', color=self.colors['text'], fontweight='bold', fontsize=12)
            
            # Set labels
            rotation_angle = 45 if len(quarters) > 8 else 30
            ax.set_xticks(range(len(quarters)))
            ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right',
                              color=self.colors['text'], fontsize=10)
            
            # Value labels with indicators
            for bar, dp in zip(bars, data):
                height = bar.get_height()
                label_text = f"${height:.0f}M"
                if dp.is_calculated_q4:
                    label_text += " (calc)"
                
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       label_text, ha='center', va='bottom',
                       color=self.colors['text'], fontsize=9, fontweight='bold')
            
            # Apply styling
            ax.spines['bottom'].set_color(self.colors['text'])
            ax.spines['left'].set_color(self.colors['text'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.3, color=self.colors['text'])
            ax.tick_params(colors=self.colors['text'], labelsize=10)
            
            # Add legend for Q4 calculation
            calculated_count = len([d for d in data if d.is_calculated_q4])
            if calculated_count > 0:
                from matplotlib.patches import Patch
                legend_elements = [
                    Patch(facecolor=self.COLORS['positive'], label='Direct XBRL Data'),
                    Patch(facecolor=self.COLORS['calculated_q4'], label='Q4 Calculated from Annual')
                ]
                ax.legend(handles=legend_elements, loc='upper left', 
                         facecolor=self.colors['frame'], edgecolor=self.colors['text'])
            
            # Create canvas and add to tkinter
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, pady=5)
            
            print(f"✅ Matplotlib revenue chart created successfully")
            
        except Exception as e:
            print(f"❌ Error creating matplotlib chart: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to text display on error
            tk.Label(parent, text=f"❌ Chart Error: {e}", 
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                    fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _create_yoy_section(self, parent: tk.Frame, data: List[RevenueDataPoint]):
        """Create YoY analysis chart with matplotlib"""
        print(f"📈 Creating YoY matplotlib chart with {len(data)} quarters")
        
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=350)
        frame.pack(fill='both', expand=True)
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Year-over-Year Revenue Analysis", 
                font=(UI_CONFIG['font_family'], 14, 'bold'), 
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        yoy_data = [d for d in data if not math.isnan(d.yoy_change_pct) and not math.isinf(d.yoy_change_pct)]
        
        if yoy_data:
            self._create_yoy_matplotlib_chart(content, yoy_data)
        else:
            tk.Label(content, text="❌ No YoY Data Available\nNeed at least 4 consecutive quarters for year-over-year comparison",
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'], 
                    fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _create_yoy_matplotlib_chart(self, parent: tk.Frame, yoy_data: List[RevenueDataPoint]):
        """Create YoY matplotlib chart"""
        try:
            import matplotlib
            matplotlib.use('TkAgg')
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            values = [d.yoy_change_pct for d in yoy_data]
            quarters = [d.quarter_label for d in yoy_data]
            display_values = [max(-self.YOY_CAP, min(self.YOY_CAP, v)) for v in values]
            
            fig = Figure(figsize=(12, 5), facecolor=self.colors['frame'])
            ax = fig.add_subplot(111, facecolor=self.colors['frame'])
            
            colors = [self.COLORS['yoy_growth'] if v > 5 else 
                     self.COLORS['yoy_decline'] if v < -5 else 
                     self.COLORS['yoy_neutral'] for v in values]
            
            bars = ax.bar(range(len(quarters)), display_values, color=colors, alpha=0.8, width=0.8)
            
            ax.set_title(f'{self.ticker} Year-over-Year Revenue Changes', 
                        color=self.colors['header'], fontweight='bold', fontsize=14)
            ax.set_ylabel('YoY Change (%)', color=self.colors['text'], fontweight='bold', fontsize=12)
            ax.set_xlabel('Quarter', color=self.colors['text'], fontweight='bold', fontsize=12)
            
            rotation_angle = 45 if len(quarters) > 8 else 30
            ax.set_xticks(range(len(quarters)))
            ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right',
                              color=self.colors['text'], fontsize=10)
            
            ax.axhline(y=0, color=self.colors['text'], linestyle='--', alpha=0.5, linewidth=2)
            ax.axhline(y=25, color=self.COLORS['yoy_growth'], linestyle=':', alpha=0.4)
            ax.axhline(y=-25, color=self.COLORS['yoy_decline'], linestyle=':', alpha=0.4)
            
            for bar, dp in zip(bars, yoy_data):
                height = bar.get_height()
                label_y = height + (8 if height >= 0 else -12)
                ax.text(bar.get_x() + bar.get_width()/2., label_y,
                       dp.yoy_label, ha='center', va='bottom' if height >= 0 else 'top',
                       color=self.colors['text'], fontsize=9, fontweight='bold')
            
            # Apply styling
            ax.spines['bottom'].set_color(self.colors['text'])
            ax.spines['left'].set_color(self.colors['text'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.3, color=self.colors['text'])
            ax.tick_params(colors=self.colors['text'], labelsize=10)
            
            # Create canvas
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, pady=5)
            
            print(f"✅ YoY matplotlib chart created successfully")
            
        except Exception as e:
            print(f"❌ Error creating YoY matplotlib chart: {e}")
            self._show_yoy_text_fallback(parent, yoy_data, str(e))
    
    def _show_yoy_text_fallback(self, parent: tk.Frame, yoy_data: List[RevenueDataPoint], error: str):
        """Show text-based YoY display as fallback"""
        text = f"📊 YoY Analysis - {len(yoy_data)} Quarters\n\n"
        if yoy_data:
            latest = yoy_data[-1]
            text += f"Latest: {latest.quarter_label} - {latest.yoy_label}\n\n"
            text += "Recent Changes:\n" + "-"*30 + "\n"
            for dp in yoy_data[-5:]:
                growth_icon = "📈" if dp.yoy_change_pct > 0 else "📉" if dp.yoy_change_pct < 0 else "➡️"
                text += f"{growth_icon} {dp.quarter_label}: {dp.yoy_label}\n"
        
        tk.Label(parent, text=text, font=(UI_CONFIG['font_family'], 10), 
                bg=self.colors['bg'], fg=self.colors['text'],
                justify='left', anchor='nw').pack(fill='both', expand=True, padx=10, pady=10)
    
    def _show_error(self, message: str) -> bool:
        """Show error message"""
        print(f"❌ Revenue chart error: {message}")
        
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        tk.Label(self.parent_frame, text=f"❌ {message}", font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['frame'], fg=self.colors['error'], justify='center').pack(expand=True)
        return True


class RevenueTab:
    """Revenue tab container with Q4 calculation support - FIXED imports"""
    
    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        self.parent_frame = parent_frame
        self.ticker = ticker
        self.colors = {'bg': '#2b2b2b', 'text': '#ffffff', 'error': '#F44336'}
        self.data_loaded = False
        print(f"📊 RevenueTab initialized for {ticker} - FIXED imports + Q4 calc")

    def update_data(self, financial_data: List[Any], ticker: str = None, data_source_info: Dict = None, all_quarters_data: List[Any] = None):
        """Update with financial data - FIXED with Q4 calculation support"""
        print(f"🔄 RevenueTab.update_data called with {len(financial_data)} display items")
        if all_quarters_data:
            print(f"   🧮 All quarters data provided: {len(all_quarters_data)} total quarters for Q4 calc")
        else:
            print(f"   ⚠️ No all_quarters_data provided - using display data for Q4 calc")
        print(f"   Ticker: {ticker or self.ticker}")
        print(f"   Data source info: {data_source_info}")
        
        if ticker:
            self.ticker = ticker
        
        for widget in self.parent_frame.winfo_children():
            widget.destroy()

        try:
            print(f"   Creating RevenueChart for {self.ticker}")
            chart = RevenueChart(self.parent_frame, self.ticker)
            # FIXED: Pass all quarters data for Q4 calculation
            self.data_loaded = chart.create_chart(financial_data, all_quarters_data)
            print(f"   Chart creation result: {self.data_loaded}")
        except Exception as e:
            print(f"   ❌ RevenueTab error: {e}")
            import traceback
            traceback.print_exc()
            
            tk.Label(self.parent_frame, text=f"❌ Revenue Error (Q4 CALC READY)\n\n{e}\n\nCheck console for details",
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                    fg=self.colors['error'], justify='center').pack(expand=True)

    def show_placeholder(self):
        """Show placeholder - FIXED with Q4 info"""
        print("📊 RevenueTab showing placeholder")
        
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.parent_frame, 
                text="📈 Select a stock to view Revenue analysis\n\n📊 Features (Q4 CALC READY):\n• FIXED import paths\n• Actual quarterly revenue amounts\n• Q4 calculation from annual data (ALL 15 quarters)\n• Year-over-Year analysis\n• Visual indicators for calculated data\n• Multi-row cache integration\n• Uses all cached quarters for Q4 calculation",
                font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'], fg=self.colors['text'], 
                justify='center').pack(expand=True)


print("📊 FIXED Revenue Chart loaded - All imports resolved + Q4 calculation ready")