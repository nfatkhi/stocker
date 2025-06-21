# core/app.py - Clean and simple with SEC EDGAR integration
import tkinter as tk
from core.event_system import EventBus
from ui.main_window import MainWindow
from components.data_fetcher import DataFetcher  # Now SEC EDGAR enhanced!
from components.analyzer import Analyzer
from components.news_manager import NewsManager
from components.metrics_display import MetricsDisplay
from config import API_KEYS, APP_CONFIG, SEC_EDGAR_CONFIG

# Try to import the enhanced chart manager, fall back to regular one
try:
    from components.chart_manager import EnhancedChartManager
    CHART_MANAGER_CLASS = EnhancedChartManager
    ENHANCED_CHARTS = True
    print("✓ Using EnhancedChartManager with API key support")
except (ImportError, AttributeError):
    from components.chart_manager import ChartManager
    CHART_MANAGER_CLASS = ChartManager
    ENHANCED_CHARTS = False
    print("⚠️  Using basic ChartManager (no API key support)")


class StockerApp:
    """Main application class that coordinates all components"""
    
    def __init__(self, root: tk.Tk):
        """Initialize the application with tkinter root window"""
        self.root = root
        self.event_bus = EventBus()
        
        # Print SEC EDGAR status
        print(f"🏛️  SEC EDGAR integration active")
        print(f"📧 Contact email: {SEC_EDGAR_CONFIG['contact_email']}")
        
        # Initialize UI first
        self.main_window = MainWindow(self.root, self.event_bus)
        
        # Initialize components - DataFetcher is now SEC EDGAR enhanced!
        self.data_fetcher = DataFetcher(self.event_bus, API_KEYS)
        self.analyzer = Analyzer(self.event_bus)
        self.news_manager = NewsManager(self.event_bus)
        self.metrics_display = MetricsDisplay(self.event_bus)
        
        # Initialize chart manager with or without API keys based on what's available
        if ENHANCED_CHARTS:
            try:
                # Try to create enhanced chart manager with API keys
                self.chart_manager = CHART_MANAGER_CLASS(self.event_bus, API_KEYS)
                print("✓ Enhanced chart manager initialized with API keys")
            except TypeError:
                # Fall back to basic initialization if API keys not supported
                self.chart_manager = CHART_MANAGER_CLASS(self.event_bus)
                print("⚠️  Enhanced chart manager created without API keys")
        else:
            # Use basic chart manager
            self.chart_manager = CHART_MANAGER_CLASS(self.event_bus)
            print("✓ Basic chart manager initialized")
        
        # Connect components to UI containers
        self._connect_components_to_ui()
        
        # Print initialization summary
        print(f"StockerApp initialized successfully!")
        print(f"📊 Data sources: SEC EDGAR (primary) + FMP (backup)")
        print(f"🔑 API Keys available: {list(API_KEYS.keys())}")
        
    def _connect_components_to_ui(self):
        """Connect components to their UI containers"""
        # Get tab frames from the main window's tab manager
        overview_frame = self.main_window.tab_manager.get_tab_frame('Overview')
        charts_frame = self.main_window.tab_manager.get_tab_frame('Charts')
        analysis_frame = self.main_window.tab_manager.get_tab_frame('Analysis')
        
        # Connect components to their containers
        if overview_frame:
            self.metrics_display.set_container(overview_frame)
            print("✓ Metrics display connected to Overview tab")
            
        if charts_frame:
            self.chart_manager.set_container('Charts', charts_frame)
            print("✓ Chart manager connected to Charts tab")
            
        if analysis_frame:
            self.analyzer.set_container(analysis_frame)
            print("✓ Analyzer connected to Analysis tab")
        
        # Verify all connections
        if not all([overview_frame, charts_frame, analysis_frame]):
            print("⚠️  Warning: Some tab frames not found during component connection")
        else:
            print("✓ All components successfully connected to UI")
        
    def run(self):
        """Start the application"""
        print("🚀 Starting Stocker application with SEC EDGAR integration...")
        self.root.mainloop()