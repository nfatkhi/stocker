# components/financials_manager.py - Fixed imports for existing project structure

import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Optional, Dict, Tuple
from datetime import datetime

from core.event_system import EventBus, Event, EventType

# Try to import models from different possible locations
try:
    from models import QuarterlyFinancials
except ImportError:
    try:
        from core.models import QuarterlyFinancials
    except ImportError:
        # Create basic model if none exists
        from dataclasses import dataclass
        
        @dataclass
        class QuarterlyFinancials:
            date: str
            revenue: float
            net_income: float
            gross_profit: float
            operating_income: float
            assets: float
            liabilities: float
            cash: float
            debt: float
            eps: float

# Try to import config
try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {
        'font_family': 'Arial',
        'font_size': 10,
        'chart_height': 400,
        'metric_card_width': 200,
        'status_bar_height': 30,
    }


class FinancialsManager:
    """
    Basic Financial Analysis Manager that integrates with existing Stocker architecture
    
    Displays quarterly financial data in a simple, clean interface
    """
    
    def __init__(self, parent=None, event_bus=None, **kwargs):
        """Initialize with flexible arguments to match existing interface"""
        # Handle different argument patterns
        self.parent_frame = parent or kwargs.get('parent_frame')
        self.event_bus = event_bus or kwargs.get('event_bus')
        
        if not self.parent_frame or not self.event_bus:
            raise ValueError("FinancialsManager requires both parent and event_bus arguments")
        
        self.current_ticker = ""
        self.current_financials = []
        
        # Color scheme for consistency
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
        
        # Subscribe to events
        self.event_bus.subscribe(EventType.DATA_RECEIVED, self.on_data_received)
        
        # Setup UI
        self._setup_ui()
        
        print("📊 Financials Manager initialized")
    
    def _setup_ui(self):
        """Setup the financial analysis UI"""
        # Clear existing content
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        
        # Main container
        main_frame = tk.Frame(self.parent_frame, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Header
        header_label = tk.Label(
            main_frame,
            text="📊 Financial Analysis",
            font=(UI_CONFIG['font_family'], 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['header']
        )
        header_label.pack(pady=(0, 20))
        
        # Content area
        self.content_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        self.content_frame.pack(fill='both', expand=True)
        
        # Initially show placeholder
        self._show_placeholder()
    
    def _show_placeholder(self):
        """Show placeholder when no data is loaded"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        placeholder = tk.Label(
            self.content_frame,
            text="📊 Select a stock to view financial analysis\n\nEnhanced with SEC EDGAR data integration",
            font=(UI_CONFIG['font_family'], 14),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            justify='center'
        )
        placeholder.pack(expand=True)
    
    def on_data_received(self, event):
        """Handle new financial data received"""
        stock_data = event.data['stock_data']
        data_source = event.data.get('data_source', 'Unknown')
        
        self.current_ticker = stock_data.ticker
        self.current_financials = stock_data.quarterly_financials
        
        print(f"📊 Financials Manager: Data received for {self.current_ticker} from {data_source}")
        
        if self.current_financials:
            self._update_financial_display()
        else:
            self._show_no_data_message()
    
    def _update_financial_display(self):
        """Update the financial display with new data"""
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        try:
            # Create header with ticker and data source info
            header_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
            header_frame.pack(fill='x', pady=(0, 20))
            
            title_label = tk.Label(
                header_frame,
                text=f"{self.current_ticker} - Financial Overview",
                font=(UI_CONFIG['font_family'], 16, 'bold'),
                bg=self.colors['bg'],
                fg=self.colors['header']
            )
            title_label.pack(side='left')
            
            # Create financial summary
            self._create_financial_summary()
            
            # Create revenue chart
            self._create_revenue_chart()
            
        except Exception as e:
            print(f"❌ Error updating financial display: {e}")
            self._show_error_message(str(e))
    
    def _create_financial_summary(self):
        """Create financial summary cards"""
        if not self.current_financials:
            return
        
        summary_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        summary_frame.pack(fill='x', pady=(0, 20))
        
        # Calculate summary metrics
        revenues = [f.revenue for f in self.current_financials if f.revenue > 0]
        net_incomes = [f.net_income for f in self.current_financials if f.net_income != 0]
        
        if revenues:
            latest_revenue = revenues[0]
            avg_revenue = sum(revenues) / len(revenues)
            
            # Create metric cards
            metrics = [
                ("Quarters Available", f"{len(self.current_financials)}", self.colors['accent']),
                ("Latest Revenue", f"${latest_revenue/1e9:.2f}B", self.colors['success']),
                ("Average Revenue", f"${avg_revenue/1e9:.2f}B", self.colors['accent']),
                ("Revenue Range", f"${min(revenues)/1e9:.1f}B - ${max(revenues)/1e9:.1f}B", self.colors['text'])
            ]
            
            for i, (label, value, color) in enumerate(metrics):
                card_frame = tk.Frame(summary_frame, bg=self.colors['frame'], relief='raised', bd=1)
                card_frame.pack(side='left', fill='both', expand=True, padx=5)
                
                tk.Label(
                    card_frame,
                    text=label,
                    font=(UI_CONFIG['font_family'], 10),
                    bg=self.colors['frame'],
                    fg=self.colors['text']
                ).pack(pady=(10, 5))
                
                tk.Label(
                    card_frame,
                    text=value,
                    font=(UI_CONFIG['font_family'], 12, 'bold'),
                    bg=self.colors['frame'],
                    fg=color
                ).pack(pady=(0, 10))
    
    def _create_revenue_chart(self):
        """Create a simple revenue chart"""
        if not self.current_financials:
            return
        
        chart_frame = tk.Frame(self.content_frame, bg=self.colors['frame'], relief='sunken', bd=2)
        chart_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        try:
            # Prepare data
            revenues = []
            quarters = []
            
            for financial in reversed(self.current_financials[-8:]):  # Last 8 quarters
                if financial.revenue > 0:
                    revenues.append(financial.revenue / 1e9)  # Convert to billions
                    quarters.append(self._get_quarter_label(financial.date))
            
            if not revenues:
                tk.Label(
                    chart_frame,
                    text="No revenue data available for chart",
                    bg=self.colors['frame'],
                    fg=self.colors['warning'],
                    font=(UI_CONFIG['font_family'], 12)
                ).pack(expand=True)
                return
            
            # Create matplotlib figure
            fig = Figure(figsize=(10, 6), facecolor=self.colors['frame'])
            ax = fig.add_subplot(111, facecolor=self.colors['frame'])
            
            # Create bar chart
            bars = ax.bar(range(len(quarters)), revenues, color=self.colors['accent'], alpha=0.8)
            
            # Customize chart
            ax.set_xlabel('Quarter', color=self.colors['text'], fontweight='bold')
            ax.set_ylabel('Revenue (Billions $)', color=self.colors['text'], fontweight='bold')
            ax.set_title(f'{self.current_ticker} Quarterly Revenue', 
                        color=self.colors['header'], fontweight='bold')
            
            # Set labels
            ax.set_xticks(range(len(quarters)))
            ax.set_xticklabels(quarters, rotation=45, ha='right', color=self.colors['text'])
            ax.tick_params(colors=self.colors['text'])
            
            # Add value labels on bars
            for bar, value in zip(bars, revenues):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(revenues) * 0.01,
                       f'${value:.2f}B', ha='center', va='bottom', color=self.colors['text'])
            
            # Style the chart
            ax.spines['bottom'].set_color(self.colors['text'])
            ax.spines['left'].set_color(self.colors['text'])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.3, color=self.colors['text'])
            
            # Create canvas
            canvas = FigureCanvasTkAgg(fig, chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=10)
            
            print(f"📊 Revenue chart created with {len(revenues)} quarters")
            
        except Exception as e:
            print(f"❌ Error creating revenue chart: {e}")
            tk.Label(chart_frame, text=f"Error creating chart: {str(e)}", 
                    bg=self.colors['frame'], fg=self.colors['error']).pack(expand=True)
    
    def _get_quarter_label(self, date_str: str) -> str:
        """Convert date string to quarter label"""
        try:
            if ' ' in date_str:
                date_part = date_str.split(' ')[0]
            else:
                date_part = date_str
            
            date_obj = datetime.strptime(date_part, '%Y-%m-%d')
            year = date_obj.year
            quarter = (date_obj.month - 1) // 3 + 1
            return f"{year}Q{quarter}"
        except:
            return date_str[:7]  # Fallback to YYYY-MM
    
    def _show_no_data_message(self):
        """Show message when no financial data is available"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        no_data_label = tk.Label(
            self.content_frame,
            text=f"📊 No financial data available for {self.current_ticker}\n\nThis may be a new stock or not publicly traded",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['warning'],
            justify='center'
        )
        no_data_label.pack(expand=True)
    
    def _show_error_message(self, error_message: str):
        """Show error message"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        error_label = tk.Label(
            self.content_frame,
            text=f"❌ Error displaying financial data\n\n{error_message}",
            font=(UI_CONFIG['font_family'], 12),
            bg=self.colors['bg'],
            fg=self.colors['error'],
            justify='center'
        )
        error_label.pack(expand=True)
    
    def set_container(self, container_frame: tk.Frame):
        """Set the container frame for the financials manager"""
        self.parent_frame = container_frame
        self._setup_ui()
        print("📊 Financials Manager container updated")


if __name__ == "__main__":
    # Test the financials manager
    root = tk.Tk()
    root.title("Financials Manager Test")
    root.geometry("800x600")
    root.configure(bg='#2b2b2b')
    
    from core.event_system import EventBus
    
    event_bus = EventBus()
    manager = FinancialsManager(root, event_bus)
    
    root.mainloop()