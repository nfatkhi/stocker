# ui/widgets/working_stock_chart.py
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime
import pandas as pd

class WorkingStockChart(ttk.Frame):
    """Working stock chart widget based on your successful example"""
    
    def __init__(self, parent, title="Stock Chart", **kwargs):
        super().__init__(parent, **kwargs)
        self.title = title
        self.canvas = None
        self.figure = None
        self.ax = None
        
        # Create the chart immediately
        self._create_chart()
        
    def _create_chart(self):
        """Create matplotlib chart using the working pattern"""
        print(f"DEBUG: Creating working chart for {self.title}")
        
        # Clear any existing widgets
        for widget in self.winfo_children():
            widget.destroy()
            
        # Create figure with explicit size (matching your working example)
        self.figure = Figure(figsize=(10, 6), dpi=100, facecolor='#444444')
        self.ax = self.figure.add_subplot(111)
        
        # Style the plot (dark theme like your working example)
        self.ax.set_facecolor('#444444')
        self.ax.tick_params(colors='#e0e0e0')
        self.ax.set_title(self.title, color='#6ea3d8', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('Date', color='#e0e0e0')
        self.ax.set_ylabel('Price ($)', color='#e0e0e0')
        self.ax.grid(True, alpha=0.3, color='#555555')
        
        # Set spine colors
        for spine in self.ax.spines.values():
            spine.set_color('#e0e0e0')
            
        # Create canvas (exactly like your working example)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        
        # Pack the canvas widget
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Adjust layout
        self.figure.subplots_adjust(left=0.08, right=0.95, top=0.92, bottom=0.15)
        
        print(f"DEBUG: Working chart created successfully")
        
    def update_data(self, dates, prices, label='Price'):
        """Update chart with new data"""
        print(f"DEBUG: WorkingStockChart.update_data called with {len(dates)} dates, {len(prices)} prices")
        
        if not self.ax or not self.canvas:
            print(f"DEBUG: Chart not ready, recreating...")
            self._create_chart()
            
        # Clear previous plot
        self.ax.clear()
        
        # Re-apply styling after clear
        self.ax.set_facecolor('#444444')
        self.ax.tick_params(colors='#e0e0e0')
        self.ax.set_title(self.title, color='#6ea3d8', fontsize=14, fontweight='bold')
        self.ax.set_xlabel('Date', color='#e0e0e0')
        self.ax.set_ylabel('Price ($)', color='#e0e0e0')
        self.ax.grid(True, alpha=0.3, color='#555555')
        
        for spine in self.ax.spines.values():
            spine.set_color('#e0e0e0')
        
        # Convert dates to proper format if needed
        plot_dates = []
        for date in dates:
            if isinstance(date, str):
                plot_dates.append(datetime.strptime(date, '%Y-%m-%d'))
            elif isinstance(date, datetime):
                plot_dates.append(date)
            else:
                plot_dates.append(date)
                
        # Plot the data
        self.ax.plot(plot_dates, prices, label=label, linewidth=2, color='#6ea3d8', marker='o', markersize=3)
        self.ax.legend()
        
        # Format x-axis dates
        self.figure.autofmt_xdate()
        
        # Draw the canvas
        self.canvas.draw()
        
        print(f"DEBUG: Working chart updated successfully")
        
    def clear(self):
        """Clear the chart"""
        if self.ax:
            self.ax.clear()
            if self.canvas:
                self.canvas.draw()