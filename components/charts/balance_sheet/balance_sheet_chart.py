# components/charts/balance_sheet/balance_sheet_chart.py - Balance sheet chart with financial ratios

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
    from .balance_sheet_data_processor import process_balance_sheet_data, BalanceSheetDataPoint, BalanceSheetMetrics
except ImportError:
    # Fallback for standalone testing
    print("⚠️ BalanceSheetDataProcessor not available - using basic processing")
    
    class BalanceSheetDataPoint:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class BalanceSheetMetrics:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    def process_balance_sheet_data(data, max_quarters=12):
        return [], BalanceSheetMetrics(latest_total_assets=0, latest_equity=0, latest_debt=0,
                                      latest_current_ratio=0, latest_debt_to_equity=0,
                                      avg_current_ratio=0, avg_debt_to_equity=0,
                                      total_quarters=0, data_quality="No Processor", 
                                      financial_strength="Unknown")

try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {'font_family': 'Arial', 'font_size': 10}


class BalanceSheetChart(FinancialBarChart):
    """Balance sheet chart with financial ratios and liquidity analysis"""
    
    COLORS = {
        'strong': '#4CAF50', 'moderate': '#FF9800', 'weak': '#F44336',
        'assets': '#2196F3', 'liabilities': '#FF5722', 'equity': '#4CAF50',
        'ratio_good': '#4CAF50', 'ratio_warning': '#FF9800', 'ratio_poor': '#F44336'
    }

    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        super().__init__(parent_frame, ticker, **kwargs)
        self.data_processor_available = True
        try:
            from .balance_sheet_data_processor import BalanceSheetDataProcessor
        except ImportError:
            self.data_processor_available = False
    
    def get_chart_title(self) -> str:
        return "Balance Sheet Analysis"
    
    def get_y_label(self) -> str:
        return "Value (Millions $)"

    def create_chart(self, financial_data: List[Any]) -> bool:
        """Create balance sheet analysis using data processor"""
        if not financial_data:
            return self._show_error("No financial data provided")
        
        # Process data using separated processor
        try:
            data_points, metrics = process_balance_sheet_data(financial_data, max_quarters=12)
        except Exception as e:
            print(f"❌ Balance sheet data processing failed: {e}")
            return self._show_error(f"Data processing error: {str(e)}")
        
        if not data_points:
            return self._show_error("No meaningful balance sheet data available")
        
        # Store for UI rendering
        self.data_points = data_points
        self.metrics = metrics
        
        return self._create_scrollable_layout()
    
    def _create_scrollable_layout(self) -> bool:
        """Create scrollable 4-section layout for balance sheet analysis"""
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Use base chart's enhanced scrollable container
        canvas, scrollbar, content_frame = self.create_scrollable_container(self.parent_frame)
        
        # Create the four sections in the content frame
        self._create_summary_section(content_frame)
        self._create_assets_section(content_frame)
        self._create_ratios_section(content_frame)
        self._create_trends_section(content_frame)
        
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
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=120)
        frame.pack(fill='x', pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text=f"{self.ticker} - Balance Sheet Summary", 
                font=(UI_CONFIG['font_family'], 12, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(5, 0))
        
        cards_frame = tk.Frame(frame, bg=self.colors['frame'])
        cards_frame.pack(fill='both', expand=True, padx=10, pady=(0, 5))
        
        # Use processed metrics
        latest_assets = self.metrics.latest_total_assets
        latest_equity = self.metrics.latest_equity
        latest_current_ratio = self.metrics.latest_current_ratio
        financial_strength = self.metrics.financial_strength
        data_quality = self.metrics.data_quality
        
        # Determine strength color
        strength_color = self.COLORS['strong'] if financial_strength == "Strong" else \
                        self.COLORS['moderate'] if financial_strength == "Moderate" else \
                        self.COLORS['weak']
        
        metrics = [
            ("Total Assets", f"${latest_assets/1e9:.1f}B", self.COLORS['assets']),
            ("Equity", f"${latest_equity/1e9:.1f}B", self.COLORS['equity']),
            ("Current Ratio", f"{latest_current_ratio:.2f}" if not math.isnan(latest_current_ratio) else "N/A", 
             self.COLORS['ratio_good'] if latest_current_ratio >= 1.5 else self.COLORS['ratio_warning']),
            ("Financial Strength", financial_strength, strength_color),
            ("Data Quality", data_quality, self.colors['success'])
        ]
        
        for label, value, color in metrics:
            card = tk.Frame(cards_frame, bg=self.colors['bg'], relief='raised', bd=1)
            card.pack(side='left', fill='both', expand=True, padx=2)
            tk.Label(card, text=label, font=(UI_CONFIG['font_family'], 8), 
                    bg=self.colors['bg'], fg=self.colors['text']).pack(pady=(3, 1))
            tk.Label(card, text=value, font=(UI_CONFIG['font_family'], 9, 'bold'), 
                    bg=self.colors['bg'], fg=color).pack(pady=(0, 3))
    
    def _create_assets_section(self, parent: tk.Frame):
        """Create asset composition chart"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=400)
        frame.pack(fill='both', expand=True, pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Asset Composition Over Time", 
                font=(UI_CONFIG['font_family'], 14, 'bold'),
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Extract chart data
        values = [dp.total_assets for dp in self.data_points]
        quarters = [dp.quarter_label for dp in self.data_points]
        
        self.create_interactive_chart(content, values, quarters, f"{self.ticker} Total Assets", 
                                     "Total Assets", self.COLORS['assets'], "Assets")
    
    def _create_ratios_section(self, parent: tk.Frame):
        """Create financial ratios chart"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=500)
        frame.pack(fill='both', expand=True, pady=(0, 10))
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Key Financial Ratios", 
                font=(UI_CONFIG['font_family'], 14, 'bold'), 
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Filter to data points with ratio information
        ratio_data = [dp for dp in self.data_points 
                     if not math.isnan(dp.current_ratio) or not math.isnan(dp.debt_to_equity)]
        
        if ratio_data:
            self._create_ratios_chart(content, ratio_data)
        else:
            tk.Label(content, text="❌ No Ratio Data Available\nNeed complete balance sheet data for ratio calculations",
                    font=(UI_CONFIG['font_family'], 14), bg=self.colors['bg'], 
                    fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _create_ratios_chart(self, parent: tk.Frame, ratio_data: List[BalanceSheetDataPoint]):
        """Create financial ratios matplotlib chart - FIXED VERSION"""
        try:
            print(f"🔄 Creating ratios chart with {len(ratio_data)} data points")
            
            quarters = [dp.quarter_label for dp in ratio_data]
            current_ratios = [dp.current_ratio if not math.isnan(dp.current_ratio) else 0 for dp in ratio_data]
            debt_equity_ratios = [dp.debt_to_equity if not math.isnan(dp.debt_to_equity) else 0 for dp in ratio_data]
            
            print(f"   Data prepared: {len(quarters)} quarters")
            
            # Try to import matplotlib directly
            try:
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                print("   ✅ Matplotlib imported successfully")
            except ImportError as e:
                print(f"   ❌ Matplotlib import failed: {e}")
                raise Exception(f"Matplotlib not available: {e}")
            
            # Create figure with proper spacing
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            fig.patch.set_facecolor('#2b2b2b')
            
            # Add spacing between subplots
            plt.subplots_adjust(hspace=0.4)  # Increase vertical spacing
            
            print("   📊 Creating Current Ratio chart")
            
            # Current Ratio chart
            bars1 = ax1.bar(range(len(quarters)), current_ratios, 
                           color=[self.COLORS['ratio_good'] if r >= 1.5 else 
                                 self.COLORS['ratio_warning'] if r >= 1.0 else 
                                 self.COLORS['ratio_poor'] for r in current_ratios], 
                           alpha=0.8, width=0.8)
            
            ax1.set_title('Current Ratio (Higher is Better)', color='white', fontweight='bold', fontsize=12)
            ax1.set_ylabel('Current Ratio', color='white', fontsize=10)
            ax1.axhline(y=1.5, color=self.COLORS['ratio_good'], linestyle='--', alpha=0.5)
            ax1.axhline(y=1.0, color=self.COLORS['ratio_warning'], linestyle='--', alpha=0.5)
            ax1.set_facecolor('#3c3c3c')
            
            print("   📊 Creating Debt-to-Equity chart")
            
            # Debt-to-Equity Ratio chart
            bars2 = ax2.bar(range(len(quarters)), debt_equity_ratios,
                           color=[self.COLORS['ratio_good'] if r <= 0.3 else 
                                 self.COLORS['ratio_warning'] if r <= 0.6 else 
                                 self.COLORS['ratio_poor'] for r in debt_equity_ratios], 
                           alpha=0.8, width=0.8)
            
            ax2.set_title('Debt-to-Equity Ratio (Lower is Better)', color='white', fontweight='bold', fontsize=12)
            ax2.set_ylabel('D/E Ratio', color='white', fontsize=10)
            ax2.set_xlabel('Quarter', color='white', fontsize=10)
            ax2.axhline(y=0.3, color=self.COLORS['ratio_good'], linestyle='--', alpha=0.5)
            ax2.axhline(y=0.6, color=self.COLORS['ratio_warning'], linestyle='--', alpha=0.5)
            ax2.set_facecolor('#3c3c3c')
            
            print("   🏷️ Setting axis labels")
            
            # Set x-axis labels for both charts
            for ax, bars, values in [(ax1, bars1, current_ratios), (ax2, bars2, debt_equity_ratios)]:
                rotation_angle = 45 if len(quarters) > 8 else 30
                ax.set_xticks(range(len(quarters)))
                ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right', color='white', fontsize=9)
                
                # Value labels on bars
                for bar, value in zip(bars, values):
                    if value > 0:  # Only show non-zero values
                        height = bar.get_height()
                        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.02,
                               f'{value:.2f}', ha='center', va='bottom', color='white', fontsize=8)
                
                # Style the axis
                ax.tick_params(colors='white')
                ax.spines['bottom'].set_color('white')
                ax.spines['top'].set_color('white')
                ax.spines['right'].set_color('white')
                ax.spines['left'].set_color('white')
            
            print("   🎨 Applying styling and layout")
            
            # Adjust layout
            plt.tight_layout()
            
            # Create canvas and embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, pady=5)
            
            print("   ✅ Ratios chart created successfully")
            
        except Exception as e:
            print(f"   ❌ Chart creation failed: {e}")
            import traceback
            traceback.print_exc()
            self._show_ratios_fallback(parent, ratio_data, str(e))
    
    def _create_trends_section(self, parent: tk.Frame):
        """Create balance sheet trends analysis"""
        frame = tk.Frame(parent, bg=self.colors['frame'], relief='solid', bd=2, height=350)
        frame.pack(fill='both', expand=True)
        frame.pack_propagate(False)
        
        tk.Label(frame, text="Balance Sheet Health Trends", 
                font=(UI_CONFIG['font_family'], 14, 'bold'), 
                bg=self.colors['frame'], fg=self.colors['header']).pack(pady=(10, 5))
        
        content = tk.Frame(frame, bg=self.colors['bg'])
        content.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create trends analysis
        self._create_trends_analysis(content)
    
    def _create_trends_analysis(self, parent: tk.Frame):
        """Create text-based trends analysis"""
        try:
            # Calculate trends
            trends_text = self._analyze_balance_sheet_trends()
            
            # Create scrollable text widget
            text_frame = tk.Frame(parent, bg=self.colors['bg'])
            text_frame.pack(fill='both', expand=True)
            
            text_widget = tk.Text(text_frame, 
                                 bg=self.colors['frame'], 
                                 fg=self.colors['text'],
                                 font=(UI_CONFIG['font_family'], 10),
                                 wrap=tk.WORD,
                                 relief='flat',
                                 padx=10, pady=10)
            text_widget.pack(fill='both', expand=True)
            
            text_widget.insert('1.0', trends_text)
            text_widget.config(state='disabled')  # Make read-only
            
        except Exception as e:
            tk.Label(parent, text=f"❌ Trends Analysis Error\n{str(e)}",
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                    fg=self.colors['error'], justify='center').pack(expand=True)
    
    def _analyze_balance_sheet_trends(self) -> str:
        """Analyze balance sheet trends and return formatted text"""
        if not self.data_points or len(self.data_points) < 2:
            return "📊 Insufficient data for trend analysis\n\nNeed at least 2 quarters of balance sheet data."
        
        latest = self.data_points[-1]
        previous = self.data_points[-2] if len(self.data_points) >= 2 else None
        
        analysis = f"📊 Balance Sheet Analysis for {self.ticker}\n"
        analysis += "=" * 50 + "\n\n"
        
        # Latest position
        analysis += f"📈 Latest Quarter: {latest.quarter_label}\n"
        analysis += f"   Total Assets: ${latest.total_assets/1e9:.1f}B\n"
        analysis += f"   Stockholders' Equity: ${latest.stockholders_equity/1e9:.1f}B\n"
        analysis += f"   Long-term Debt: ${latest.long_term_debt/1e9:.1f}B\n\n"
        
        # Ratios analysis
        analysis += "📊 Key Financial Ratios:\n"
        if not math.isnan(latest.current_ratio):
            ratio_status = "Strong" if latest.current_ratio >= 1.5 else "Adequate" if latest.current_ratio >= 1.0 else "Weak"
            analysis += f"   Current Ratio: {latest.current_ratio:.2f} ({ratio_status})\n"
        
        if not math.isnan(latest.debt_to_equity):
            debt_status = "Low" if latest.debt_to_equity <= 0.3 else "Moderate" if latest.debt_to_equity <= 0.6 else "High"
            analysis += f"   Debt-to-Equity: {latest.debt_to_equity:.2f} ({debt_status})\n"
        
        if not math.isnan(latest.equity_ratio):
            analysis += f"   Equity Ratio: {latest.equity_ratio:.1%}\n"
        
        if not math.isnan(latest.cash_ratio):
            analysis += f"   Cash Ratio: {latest.cash_ratio:.1%}\n"
        
        analysis += "\n"
        
        # Quarter-over-quarter changes
        if previous:
            analysis += f"📈 Quarter-over-Quarter Changes:\n"
            
            if not math.isnan(latest.total_assets) and not math.isnan(previous.total_assets):
                asset_change = ((latest.total_assets - previous.total_assets) / previous.total_assets) * 100
                analysis += f"   Assets: {asset_change:+.1f}% ({previous.quarter_label} → {latest.quarter_label})\n"
            
            if not math.isnan(latest.stockholders_equity) and not math.isnan(previous.stockholders_equity):
                equity_change = ((latest.stockholders_equity - previous.stockholders_equity) / previous.stockholders_equity) * 100
                analysis += f"   Equity: {equity_change:+.1f}%\n"
            
            if (not math.isnan(latest.current_ratio) and not math.isnan(previous.current_ratio) and 
                previous.current_ratio != 0):
                ratio_change = ((latest.current_ratio - previous.current_ratio) / previous.current_ratio) * 100
                analysis += f"   Current Ratio: {ratio_change:+.1f}%\n"
        
        # Financial strength assessment
        analysis += f"\n💪 Overall Financial Strength: {self.metrics.financial_strength}\n"
        
        strength_explanation = {
            "Strong": "Excellent liquidity, low debt levels, strong equity position",
            "Moderate": "Adequate financial position with some areas for improvement", 
            "Weak": "Concerning financial metrics, potential liquidity or leverage issues",
            "Unknown": "Insufficient data for comprehensive assessment"
        }
        
        analysis += f"   {strength_explanation.get(self.metrics.financial_strength, 'Assessment pending')}\n\n"
        
        # Data quality note
        analysis += f"📊 Data Quality: {self.metrics.data_quality} ({self.metrics.total_quarters} quarters)\n"
        analysis += f"📁 Source: Multi-row XBRL cache with automated ratio calculations\n"
        
        return analysis
    
    def _show_ratios_fallback(self, parent: tk.Frame, ratio_data: List[BalanceSheetDataPoint], error: str):
        """Show text-based ratios display"""
        text = f"📊 Financial Ratios - {len(ratio_data)} Quarters\n\n"
        if ratio_data:
            latest = ratio_data[-1]
            text += f"Latest: {latest.quarter_label}\n"
            text += f"Current Ratio: {latest.current_ratio:.2f}\n" if not math.isnan(latest.current_ratio) else "Current Ratio: N/A\n"
            text += f"Debt-to-Equity: {latest.debt_to_equity:.2f}\n" if not math.isnan(latest.debt_to_equity) else "Debt-to-Equity: N/A\n"
            text += f"\nRecent Quarters:\n" + "-"*20 + "\n"
            for dp in ratio_data[-4:]:
                text += f"{dp.quarter_label}: CR {dp.current_ratio:.2f}, D/E {dp.debt_to_equity:.2f}\n"
        
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


class BalanceSheetTab:
    """Balance sheet tab container with enhanced analysis"""
    
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
            chart = BalanceSheetChart(self.parent_frame, self.ticker)
            self.data_loaded = chart.create_chart(financial_data)
        except Exception as e:
            tk.Label(self.parent_frame, text=f"❌ Balance Sheet Error\n\n{e}",
                    font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'],
                    fg=self.colors['error'], justify='center').pack(expand=True)

    def show_placeholder(self):
        """Show placeholder"""
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.parent_frame, 
                text="📊 Select a stock to view Balance Sheet analysis\n\n📈 Features:\n• Asset composition tracking\n• Financial ratio calculations\n• Liquidity analysis\n• Debt-to-equity trends\n• Financial strength assessment",
                font=(UI_CONFIG['font_family'], 12), bg=self.colors['bg'], fg=self.colors['text'], 
                justify='center').pack(expand=True)


print("📊 Balance Sheet Chart loaded with financial ratios and liquidity analysis")