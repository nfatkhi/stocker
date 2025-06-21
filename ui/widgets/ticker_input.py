# ui/widgets/ticker_input.py
import tkinter as tk
from tkinter import ttk
from core.event_system import Event, EventType

class TickerInput(ttk.Frame):
    """Widget for entering and submitting stock tickers"""
    
    def __init__(self, parent, event_bus, **kwargs):
        super().__init__(parent, **kwargs)
        self.event_bus = event_bus
        
        # Create widgets
        self._create_widgets()
        
    def _create_widgets(self):
        # Label
        self.label = ttk.Label(self, text="Stock Symbol:")
        self.label.pack(side='left', padx=(0, 5))
        
        # Entry field
        self.ticker_var = tk.StringVar()
        self.entry = ttk.Entry(
            self, 
            textvariable=self.ticker_var,
            width=10,
            font=('Arial', 12)
        )
        self.entry.pack(side='left', padx=5)
        
        # Make entry uppercase automatically
        self.ticker_var.trace('w', self._uppercase_ticker)
        
        # Analyze button
        self.analyze_btn = ttk.Button(
            self,
            text="Analyze",
            command=self._on_analyze
        )
        self.analyze_btn.pack(side='left', padx=5)
        
        # Bind Enter key
        self.entry.bind('<Return>', lambda e: self._on_analyze())
        
    def _uppercase_ticker(self, *args):
        """Convert ticker to uppercase as user types"""
        current = self.ticker_var.get()
        self.ticker_var.set(current.upper())
        
    def _on_analyze(self):
        """Handle analyze button click"""
        ticker = self.ticker_var.get().strip()
        
        if ticker:
            # Publish event
            self.event_bus.publish(Event(
                type=EventType.STOCK_SELECTED,
                data={'ticker': ticker},
                source='TickerInput'
            ))
            
            # Disable button temporarily (FIXED: use state() method for ttk widgets)
            self.analyze_btn.state(['disabled'])
            self.after(1000, lambda: self.analyze_btn.state(['!disabled']))