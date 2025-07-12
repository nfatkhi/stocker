# components/charts/base_chart.py - Fixed duplicate methods and enhanced scrolling

import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {
        'font_family': 'Arial',
        'font_size': 10,
    }


class BaseChart(ABC):
    """Base class for all financial charts"""
    
    def __init__(self, parent_frame: tk.Frame, ticker: str = "", **kwargs):
        self.parent_frame = parent_frame
        self.ticker = ticker
        
        # Color scheme
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
    
    def get_responsive_size(self) -> tuple:
        """Calculate responsive chart size"""
        try:
            self.parent_frame.update_idletasks()
            window_width = max(400, self.parent_frame.winfo_width())
            window_height = max(300, self.parent_frame.winfo_height())
        except:
            window_width = 800
            window_height = 600
        
        chart_width = max(8, min(16, window_width * 0.015))
        chart_height = max(4, min(10, window_height * 0.012))
        
        return chart_width, chart_height, window_width, window_height
    
    def get_dynamic_font_sizes(self, chart_width: float) -> Dict[str, int]:
        """Calculate dynamic font sizes"""
        return {
            'title': max(10, min(16, int(chart_width * 1.2))),
            'label': max(8, min(12, int(chart_width * 0.8))),
            'tick': max(7, min(10, int(chart_width * 0.7))),
            'value': max(6, min(9, int(chart_width * 0.6)))
        }
    
    def parse_quarter_label(self, date_str: str) -> str:
        """Convert date string to quarter label"""
        try:
            date_part = date_str.split(' ')[0] if ' ' in date_str else date_str
            
            if '-' in date_part and len(date_part) >= 7:
                parts = date_part.split('-')
                if len(parts) >= 2:
                    year = int(parts[0])
                    month = int(parts[1])
                    quarter = (month - 1) // 3 + 1
                    return f"{year}Q{quarter}"
            
            # Fallback
            if len(date_part) >= 4:
                return f"{date_part[:4]}Q?"
            return date_str[:10]
            
        except Exception:
            return "Q?"
    
    def create_chart_frame(self) -> tk.Frame:
        """Create chart frame"""
        chart_frame = tk.Frame(self.parent_frame, bg=self.colors['frame'], relief='sunken', bd=2)
        chart_frame.pack(fill='both', expand=True, pady=(10, 0))
        return chart_frame
    
    def create_matplotlib_figure(self, chart_width: float, chart_height: float) -> tuple:
        """Create matplotlib figure and axis"""
        fig = Figure(figsize=(chart_width, chart_height), facecolor=self.colors['frame'])
        fig.subplots_adjust(bottom=0.25, left=0.1, right=0.95, top=0.9)
        ax = fig.add_subplot(111, facecolor=self.colors['frame'])
        return fig, ax
    
    def style_axis(self, ax, font_sizes: Dict[str, int]):
        """Apply styling to axis"""
        ax.spines['bottom'].set_color(self.colors['text'])
        ax.spines['left'].set_color(self.colors['text'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.3, color=self.colors['text'])
        ax.tick_params(colors=self.colors['text'], labelsize=font_sizes['tick'])
    
    def format_currency_value(self, value_in_dollars: float, show_scale: bool = True) -> tuple:
        """Format currency value with appropriate scale"""
        if value_in_dollars == 0:
            return "No Data", ""
        
        abs_value = abs(value_in_dollars)
        
        if abs_value >= 1e9:
            formatted_value = value_in_dollars / 1e9
            scale = "B"
            return f"${formatted_value:.2f}B", scale
        elif abs_value >= 1e6:
            formatted_value = value_in_dollars / 1e6
            scale = "M"
            return f"${formatted_value:.2f}M", scale
        else:
            return f"${value_in_dollars:,.0f}", ""
    
    def format_negative_currency(self, value_in_dollars: float) -> str:
        """Format negative currency values"""
        if value_in_dollars >= 0:
            formatted, _ = self.format_currency_value(value_in_dollars, False)
            return formatted
        else:
            formatted, _ = self.format_currency_value(abs(value_in_dollars), False)
            return f"-{formatted}"
    
    def create_canvas(self, fig: Figure, chart_frame: tk.Frame) -> FigureCanvasTkAgg:
        """Create matplotlib canvas"""
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True, padx=5, pady=5)
        return canvas
    
    def setup_enhanced_scrolling(self, canvas: tk.Canvas):
        """Enhanced scrolling setup for both mouse wheel and trackpad"""
        
        def enhanced_scroll_handler(event):
            """Handle both mouse wheel and trackpad scrolling with adaptive sensitivity"""
            if hasattr(event, 'delta'):
                # Windows/Mac - detect scroll device by delta magnitude
                if abs(event.delta) < 50:
                    # Likely trackpad - higher sensitivity for small deltas
                    delta = -1 * (event.delta / 8)  # More responsive for trackpad
                elif abs(event.delta) < 120:
                    # Medium sensitivity for moderate deltas - INCREASED
                    delta = -1 * (event.delta / 20)  # Was 40, now 20 for better sensitivity
                else:
                    # Traditional mouse wheel - INCREASED sensitivity
                    delta = -1 * (event.delta / 60)  # Was 120, now 60 for faster scrolling
            else:
                # Linux scroll wheel events - MORE RESPONSIVE
                delta = -3 if event.num == 4 else 3  # Was 1, now 3 for faster scrolling
            
            # Apply scrolling with smooth increments
            # Use "units" for fine control, but multiply for faster movement
            scroll_amount = max(1, abs(int(delta)))  # Ensure minimum scroll of 1
            direction = 1 if delta > 0 else -1
            canvas.yview_scroll(direction * scroll_amount, "units")
        
        def bind_scroll_events():
            """Bind all scroll events when mouse enters canvas area"""
            # Primary scroll binding for Windows/Mac
            canvas.bind_all("<MouseWheel>", enhanced_scroll_handler)
            
            # Linux scroll bindings
            canvas.bind_all("<Button-4>", enhanced_scroll_handler)  # Scroll up
            canvas.bind_all("<Button-5>", enhanced_scroll_handler)  # Scroll down
            
            # Additional Mac trackpad support
            try:
                canvas.bind_all("<Shift-MouseWheel>", enhanced_scroll_handler)
            except tk.TclError:
                pass  # Not supported on this platform
        
        def unbind_scroll_events():
            """Unbind scroll events when mouse leaves canvas area"""
            try:
                canvas.unbind_all("<MouseWheel>")
                canvas.unbind_all("<Button-4>")
                canvas.unbind_all("<Button-5>")
                canvas.unbind_all("<Shift-MouseWheel>")
            except tk.TclError:
                pass  # Some events might not be bound
        
        # Bind enter/leave events to manage scroll binding
        canvas.bind('<Enter>', lambda e: bind_scroll_events())
        canvas.bind('<Leave>', lambda e: unbind_scroll_events())
        
        # Also bind to focus events for better behavior
        canvas.bind('<FocusIn>', lambda e: bind_scroll_events())
        canvas.bind('<FocusOut>', lambda e: unbind_scroll_events())
    
    def create_scrollable_container(self, parent_frame: tk.Frame) -> tuple:
        """Create a scrollable container with enhanced scrolling support"""
        # Create container frame
        container_frame = tk.Frame(parent_frame, bg=self.colors['bg'])
        container_frame.pack(fill='both', expand=True)
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(container_frame, bg=self.colors['bg'])
        scrollbar = tk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        
        # Create content frame that will hold the actual content
        content_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        # Configure canvas scrolling
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def update_scroll_region():
            """Update canvas scroll region when content changes"""
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Update content frame width to match canvas width
            if canvas.winfo_width() > 1:
                canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        
        # Bind events to update scroll region
        content_frame.bind("<Configure>", lambda e: canvas.after_idle(update_scroll_region))
        canvas.bind("<Configure>", lambda e: canvas.after_idle(update_scroll_region))
        
        # Setup enhanced scrolling - BIND TO CONTAINER AND CONTENT FRAME TOO
        self.setup_enhanced_scrolling(canvas)
        self._bind_scrolling_to_all_widgets(container_frame, canvas)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return canvas, scrollbar, content_frame
    
    def _bind_scrolling_to_all_widgets(self, container_frame: tk.Frame, canvas: tk.Canvas):
        """Bind scrolling to all widgets in the container so scrolling works everywhere"""
        def scroll_handler(event):
            """Handle scroll events and forward to canvas"""
            if hasattr(event, 'delta'):
                # Windows/Mac
                if abs(event.delta) < 50:
                    delta = -1 * (event.delta / 8)
                elif abs(event.delta) < 120:
                    delta = -1 * (event.delta / 20)
                else:
                    delta = -1 * (event.delta / 60)
            else:
                # Linux
                delta = -3 if event.num == 4 else 3
            
            scroll_amount = max(1, abs(int(delta)))
            direction = 1 if delta > 0 else -1
            canvas.yview_scroll(direction * scroll_amount, "units")
        
        def bind_recursive(widget):
            """Recursively bind scroll events to all widgets"""
            try:
                # Bind scroll events to this widget
                widget.bind("<MouseWheel>", scroll_handler)
                widget.bind("<Button-4>", scroll_handler)
                widget.bind("<Button-5>", scroll_handler)
                
                # Recursively bind to all children
                for child in widget.winfo_children():
                    bind_recursive(child)
            except tk.TclError:
                pass  # Some widgets might not support binding
        
        # Bind to container and all its children
        bind_recursive(container_frame)
        
        # Also bind to the container frame itself
        container_frame.bind("<MouseWheel>", scroll_handler)
        container_frame.bind("<Button-4>", scroll_handler)
        container_frame.bind("<Button-5>", scroll_handler)
    
    def show_error_message(self, chart_frame: tk.Frame, error_message: str):
        """Show error message"""
        tk.Label(
            chart_frame,
            text=f"Error creating chart: {error_message}",
            bg=self.colors['frame'],
            fg=self.colors['error'],
            font=(UI_CONFIG['font_family'], 12)
        ).pack(expand=True)
    
    def create_summary_cards(self, summary_frame: tk.Frame, metrics: List[tuple]):
        """Create summary metric cards"""
        for label, value, color in metrics:
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
    
    @abstractmethod
    def create_chart(self, financial_data: List[Any]) -> bool:
        """Abstract method to create chart"""
        pass
    
    @abstractmethod
    def get_chart_title(self) -> str:
        """Abstract method to get chart title"""
        pass
    
    @abstractmethod
    def get_y_label(self) -> str:
        """Abstract method to get Y-axis label"""
        pass


class FinancialBarChart(BaseChart):
    """Base class for financial bar charts"""
    
    def create_interactive_chart(self, parent_frame, values_in_dollars, quarters, title, ylabel, color, chart_type: str = "Value"):
        """Create interactive chart with hover"""
        try:
            # Determine scale
            max_value = max([abs(v) for v in values_in_dollars if v != 0]) if values_in_dollars else 0
            
            if max_value >= 1e9:
                chart_values = [v / 1e9 for v in values_in_dollars]
                ylabel = ylabel.replace("Millions", "Billions") + " (Billions $)"
                scale_suffix = "B"
            elif max_value >= 1e6:
                chart_values = [v / 1e6 for v in values_in_dollars]
                ylabel = ylabel + " (Millions $)"
                scale_suffix = "M"
            else:
                chart_values = [v / 1e3 for v in values_in_dollars]
                ylabel = ylabel + " (Thousands $)"
                scale_suffix = "K"
            
            # Get sizing
            chart_width, chart_height, _, _ = self.get_responsive_size()
            font_sizes = self.get_dynamic_font_sizes(chart_width)
            
            # Create figure
            fig, ax = self.create_matplotlib_figure(chart_width, chart_height)
            
            # Create bars
            bar_colors = self._get_bar_colors(chart_values, color)
            bars = ax.bar(range(len(quarters)), chart_values, color=bar_colors, alpha=0.8)
            
            # Style chart
            ax.set_xlabel('Quarter', color=self.colors['text'], fontweight='bold', fontsize=font_sizes['label'])
            ax.set_ylabel(ylabel, color=self.colors['text'], fontweight='bold', fontsize=font_sizes['label'])
            ax.set_title(f'{self.ticker} {title} - Last {len(chart_values)} Quarters',
                        color=self.colors['header'], fontweight='bold', fontsize=font_sizes['title'])
            
            # Set labels
            rotation_angle = 45 if len(quarters) > 8 else 30
            ax.set_xticks(range(len(quarters)))
            ax.set_xticklabels(quarters, rotation=rotation_angle, ha='right',
                              color=self.colors['text'], fontsize=font_sizes['tick'])
            
            # Add zero line for cash flow
            if title == "Free Cash Flow":
                ax.axhline(y=0, color=self.colors['text'], linestyle='--', alpha=0.5)
            
            # Add value labels
            self._add_value_labels(ax, bars, values_in_dollars, font_sizes['value'])
            
            # Style axis
            self.style_axis(ax, font_sizes)
            
            # Create canvas
            canvas = self.create_canvas(fig, parent_frame)
            
            # Setup hover
            self._setup_hover(canvas, ax, bars, values_in_dollars, quarters, chart_type)
            
            return True
            
        except Exception as e:
            self.show_error_message(parent_frame, str(e))
            return False
    
    def _get_bar_colors(self, values: List[float], positive_color: str) -> List[str]:
        """Get bar colors based on values"""
        colors = []
        for value in values:
            if value > 0:
                colors.append(positive_color)
            elif value < 0:
                colors.append(self.colors['error'])
            else:
                colors.append(self.colors['warning'])
        return colors
    
    def _add_value_labels(self, ax, bars, values_in_dollars, font_size: int):
        """Add value labels on bars"""
        if not values_in_dollars:
            return
        
        chart_width = self.get_responsive_size()[0]
        show_labels = len(values_in_dollars) <= 10 or chart_width > 12
        
        if show_labels:
            max_value = max([abs(v) for v in values_in_dollars if v != 0]) if values_in_dollars else 1
            
            for bar, value_dollars in zip(bars, values_in_dollars):
                if value_dollars != 0:
                    height = bar.get_height()
                    formatted_value, _ = self.format_currency_value(value_dollars, False)
                    
                    if value_dollars > 0:
                        label_y = height + (max_value / 1e9 * 0.01) if max_value >= 1e9 else height + (max_value / 1e6 * 0.01)
                        va = 'bottom'
                    else:
                        label_y = height - (max_value / 1e9 * 0.01) if max_value >= 1e9 else height - (max_value / 1e6 * 0.01)
                        va = 'top'
                    
                    ax.text(bar.get_x() + bar.get_width()/2., label_y, formatted_value,
                           ha='center', va=va, color=self.colors['text'], fontsize=font_size)
    
    def _setup_hover(self, canvas, ax, bars, values, quarters, chart_type):
        """Setup hover functionality"""
        hover_annotation = ax.annotate(
            '', xy=(0, 0), xytext=(20, 20), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc=self.colors['frame'], ec=self.colors['text'], alpha=0.9),
            fontsize=9, color=self.colors['text'], visible=False
        )
        
        def on_hover(event):
            if event.inaxes != ax:
                hover_annotation.set_visible(False)
                canvas.draw_idle()
                return
            
            for i, bar in enumerate(bars):
                if bar.contains(event)[0]:
                    value = values[i]
                    quarter = quarters[i]
                    
                    if value == 0:
                        value_text = "No Data"
                    else:
                        value_text = self.format_negative_currency(value)
                    
                    hover_text = f"{quarter}\n{chart_type}: {value_text}"
                    hover_annotation.xy = (bar.get_x() + bar.get_width()/2, bar.get_height())
                    hover_annotation.set_text(hover_text)
                    hover_annotation.set_visible(True)
                    canvas.draw_idle()
                    return
            
            hover_annotation.set_visible(False)
            canvas.draw_idle()
        
        def on_leave(event):
            hover_annotation.set_visible(False)
            canvas.draw_idle()
        
        canvas.mpl_connect('motion_notify_event', on_hover)
        canvas.mpl_connect('axes_leave_event', on_leave)