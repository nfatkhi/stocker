# ui/widgets/metric_card.py
import tkinter as tk
from tkinter import ttk

class MetricCard(ttk.Frame):
    """Card widget for displaying a single metric"""
    
    def __init__(self, parent, title="", value="", suffix="", 
                 trend=None, **kwargs):
        super().__init__(parent, relief='ridge', borderwidth=2, **kwargs)
        
        self.title = title
        self.value = value
        self.suffix = suffix
        self.trend = trend  # 'up', 'down', or None
        
        # Create widgets
        self._create_widgets()
        
    def _create_widgets(self):
        # Title
        self.title_label = ttk.Label(
            self,
            text=self.title,
            font=('Arial', 10, 'bold')
        )
        self.title_label.pack(pady=(10, 5))
        
        # Value frame
        value_frame = ttk.Frame(self)
        value_frame.pack()
        
        # Value
        self.value_label = ttk.Label(
            value_frame,
            text=str(self.value),
            font=('Arial', 16, 'bold')
        )
        self.value_label.pack(side='left')
        
        # Suffix
        if self.suffix:
            self.suffix_label = ttk.Label(
                value_frame,
                text=self.suffix,
                font=('Arial', 12)
            )
            self.suffix_label.pack(side='left', padx=(2, 0))
            
        # Trend indicator
        if self.trend:
            trend_text = "▲" if self.trend == 'up' else "▼"
            trend_color = 'green' if self.trend == 'up' else 'red'
            
            self.trend_label = tk.Label(
                value_frame,
                text=trend_text,
                fg=trend_color,
                font=('Arial', 14)
            )
            self.trend_label.pack(side='left', padx=(5, 0))
            
    def update_value(self, value, trend=None):
        """Update the metric value and trend"""
        self.value = value
        self.value_label.config(text=str(value))
        
        if trend:
            if hasattr(self, 'trend_label'):
                # Update existing trend
                self.trend = trend
                trend_text = "▲" if trend == 'up' else "▼"
                trend_color = 'green' if trend == 'up' else 'red'
                self.trend_label.config(text=trend_text, fg=trend_color)
            else:
                # Create new trend label if it doesn't exist
                self.trend = trend
                trend_text = "▲" if trend == 'up' else "▼"
                trend_color = 'green' if trend == 'up' else 'red'
                
                # Get the value frame
                value_frame = self.value_label.master
                
                self.trend_label = tk.Label(
                    value_frame,
                    text=trend_text,
                    fg=trend_color,
                    font=('Arial', 14)
                )
                self.trend_label.pack(side='left', padx=(5, 0))
        
        # Force update
        self.update_idletasks()