# ui/widgets/loading_spinner.py
import tkinter as tk
from tkinter import ttk

class LoadingSpinner(ttk.Frame):
    """Animated loading spinner widget"""
    
    def __init__(self, parent, text="Loading...", **kwargs):
        super().__init__(parent, **kwargs)
        self.text = text
        
        # Create widgets
        self._create_widgets()
        
    def _create_widgets(self):
        # Progress bar in indeterminate mode
        self.progress = ttk.Progressbar(
            self,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(pady=10)
        
        # Loading text
        self.label = ttk.Label(self, text=self.text)
        self.label.pack()
        
    def start(self):
        """Start the spinner"""
        self.progress.start(10)
        
    def stop(self):
        """Stop the spinner"""
        self.progress.stop()
        
    def update_text(self, text):
        """Update loading text"""
        self.label.config(text=text)