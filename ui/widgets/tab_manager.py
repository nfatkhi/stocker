# ui/widgets/tab_manager.py
import tkinter as tk
from tkinter import ttk
from core.event_system import Event, EventType

class TabManager(ttk.Notebook):
    """Manages tabbed interface for different views"""
    
    def __init__(self, parent, event_bus, **kwargs):
        super().__init__(parent, **kwargs)
        self.event_bus = event_bus
        self.last_tab = None
        
        # Create tabs
        self._create_tabs()
        
        # Bind tab change event
        self.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
    def _create_tabs(self):
        """Create all tabs"""
        # Overview tab
        self.overview_frame = ttk.Frame(self)
        self.add(self.overview_frame, text='Overview')
        
        # Charts tab
        self.charts_frame = ttk.Frame(self)
        self.add(self.charts_frame, text='Charts')
        
        # Financials tab
        self.financials_frame = ttk.Frame(self)
        self.add(self.financials_frame, text='Financials')
        
        # News tab
        self.news_frame = ttk.Frame(self)
        self.add(self.news_frame, text='News')
        
        # Analysis tab
        self.analysis_frame = ttk.Frame(self)
        self.add(self.analysis_frame, text='Analysis')
        
        # Add placeholder content
        for tab, name in [
            (self.overview_frame, "Overview"),
            (self.charts_frame, "Charts"),
            (self.financials_frame, "Financials"),
            (self.news_frame, "News"),
            (self.analysis_frame, "Analysis")
        ]:
            label = ttk.Label(
                tab, 
                text=f"{name} content will go here",
                font=('Arial', 14)
            )
            label.pack(pady=20)
            
    def _on_tab_changed(self, event):
        """Handle tab change event with error handling"""
        try:
            # Get current tab - this might fail if tabs are disabled
            current_tab = self.tab('current')['text']
        except (tk.TclError, KeyError):
            # If we can't get current tab (e.g., tabs are disabled), just return
            return
        
        # Only process if tab actually changed
        if current_tab != self.last_tab:
            self.last_tab = current_tab
            
            # Publish tab change event
            self.event_bus.publish(Event(
                type=EventType.TAB_CHANGED,
                data={'tab': current_tab},
                source='TabManager'
            ))
            
            # Schedule a refresh after 100ms
            self.after(100, self._refresh_current_tab)
    
    def _refresh_current_tab(self):
        """Force refresh of current tab content with error handling"""
        try:
            # Get current tab frame
            current_widget = self.nametowidget(self.select())
            
            # Force update
            current_widget.update()
            current_widget.update_idletasks()
            
            # Also update parent
            self.update()
            self.update_idletasks()
        except (tk.TclError, AttributeError):
            # If we can't refresh (e.g., no current tab), just skip
            pass
        
    def get_tab_frame(self, tab_name):
        """Get frame for specific tab"""
        tab_map = {
            'Overview': self.overview_frame,
            'Charts': self.charts_frame,
            'Financials': self.financials_frame,
            'News': self.news_frame,
            'Analysis': self.analysis_frame
        }
        return tab_map.get(tab_name)