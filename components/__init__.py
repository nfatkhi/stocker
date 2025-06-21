# components/__init__.py
"""
Components package for the Stocker application.
Contains all reusable UI components and data fetchers.
"""

# Import all components for easy access
from .chart_manager import EnhancedChartManager, ChartManager
from .data_fetcher import DataFetcher
from .financials_manager import FinancialsManager  # NEW

try:
    from .live_price_widget import LivePriceWidget
except ImportError:
    # LivePriceWidget is optional if not implemented yet
    LivePriceWidget = None

# Define what gets imported when using "from components import *"
__all__ = [
    'EnhancedChartManager',
    'ChartManager', 
    'DataFetcher',
    'FinancialsManager',  # NEW
    'LivePriceWidget'
]

# Version info
__version__ = '1.0.0'

# Component registry for dynamic loading (optional)
COMPONENT_REGISTRY = {
    'chart_manager': EnhancedChartManager,
    'data_fetcher': DataFetcher,
    'financials_manager': FinancialsManager,  # NEW
}

def get_component(name):
    """Get a component class by name"""
    return COMPONENT_REGISTRY.get(name)

def list_components():
    """List all available components"""
    return list(COMPONENT_REGISTRY.keys())