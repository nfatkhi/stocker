# ui/widgets/status_bar.py
import tkinter as tk
from tkinter import ttk
from core.event_system import EventType

class StatusBar(ttk.Frame):
    """Status bar showing app state and progress"""
    
    def __init__(self, parent, event_bus, **kwargs):
        super().__init__(parent, **kwargs)
        self.event_bus = event_bus
        
        # Subscribe to events
        self._subscribe_to_events()
        
        # Create widgets
        self._create_widgets()
        
    def _create_widgets(self):
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(
            self, 
            textvariable=self.status_var,
            relief='sunken',
            anchor='w'
        )
        self.status_label.pack(side='left', fill='x', expand=True, padx=2)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self,
            mode='indeterminate',
            length=100
        )
        self.progress.pack(side='right', padx=5)
        self.progress.pack_forget()  # Hide initially
        
    def _subscribe_to_events(self):
        """Subscribe to relevant events"""
        self.event_bus.subscribe(
            EventType.DATA_FETCH_STARTED,
            self._on_fetch_started
        )
        self.event_bus.subscribe(
            EventType.DATA_FETCH_COMPLETED,
            self._on_fetch_completed
        )
        self.event_bus.subscribe(
            EventType.ANALYSIS_COMPLETED,
            self._on_analysis_completed
        )
        
    def _on_fetch_started(self, event):
        """Handle fetch started event"""
        ticker = event.data.get('ticker', '')
        self.update_status(f"Fetching data for {ticker}...")
        self.show_progress()
        
    def _on_fetch_completed(self, event):
        """Handle fetch completed event"""
        self.update_status("Analyzing data...")
        
    def _on_analysis_completed(self, event):
        """Handle analysis completed event"""
        ticker = event.data.get('ticker', '')
        self.update_status(f"Analysis complete for {ticker}")
        self.hide_progress()
        
    def update_status(self, message):
        """Update status message"""
        self.status_var.set(message)
        self.update_idletasks()
        
    def show_progress(self):
        """Show progress bar"""
        self.progress.pack(side='right', padx=5)
        self.progress.start(10)
        
    def hide_progress(self):
        """Hide progress bar"""
        self.progress.stop()
        self.progress.pack_forget()