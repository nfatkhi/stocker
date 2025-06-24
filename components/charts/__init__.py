# components/charts/__init__.py - Chart components package initialization

"""
Modular Chart Components for Stocker Financial Analysis

This package provides reusable, responsive chart components for financial data visualization.
Each chart component is self-contained and follows the same base architecture for consistency.

Available Components:
- BaseChart: Base class with common functionality (responsive sizing, styling, etc.)
- FinancialBarChart: Base class for financial bar charts
- UniversalChartManager: Universal layout manager for all financial charts
- RevenueChart: Revenue-specific chart component
- CashFlowChart: Free cash flow chart component
- RevenueTab: Complete revenue tab with summary and chart
- CashFlowTab: Complete cash flow tab with summary and chart

Architecture Features:
- Universal Chart Manager for consistent layouts
- Responsive design that scales with window size
- Consistent styling and color scheme
- Modular and reusable components
- Easy to extend with new chart types
- Built-in error handling and fallbacks

Usage:
    from charts.revenue_chart import RevenueTab
    from charts.cashflow_chart import CashFlowTab
    from charts.universal_chart_manager import UniversalChartManager, LayoutTemplate
    
    revenue_tab = RevenueTab(parent_frame, ticker="AAPL")
    revenue_tab.update_data(financial_data)
"""

# Version information
__version__ = "1.1.0"  # Updated for Universal Chart Manager
__author__ = "Stocker App Development Team"

# Import main components for easy access
try:
    from .base_chart import BaseChart, FinancialBarChart
    from .universal_chart_manager import UniversalChartManager, LayoutTemplate, FinancialChartIntegration
    from .revenue_chart import RevenueChart, RevenueTab
    from .cashflow_chart import CashFlowChart, CashFlowTab
    
    # List of available chart components
    __all__ = [
        'BaseChart',
        'FinancialBarChart',
        'UniversalChartManager',  # NEW
        'LayoutTemplate',         # NEW
        'FinancialChartIntegration',  # NEW
        'RevenueChart',
        'RevenueTab',
        'CashFlowChart', 
        'CashFlowTab'
    ]
    
    print("📊 Chart components package loaded successfully")
    print("✨ Universal Chart Manager available for enhanced layouts")
    
except ImportError as e:
    print(f"⚠️ Warning: Could not import all chart components: {e}")
    print("💡 Make sure all chart component files are present in the charts/ directory")
    
    # Provide minimal fallback
    __all__ = []


def get_available_charts():
    """Get list of available chart components"""
    return __all__


def create_revenue_tab(parent_frame, ticker="", **kwargs):
    """Factory function to create revenue tab with error handling"""
    try:
        return RevenueTab(parent_frame, ticker, **kwargs)
    except Exception as e:
        print(f"❌ Error creating revenue tab: {e}")
        return None


def create_cashflow_tab(parent_frame, ticker="", **kwargs):
    """Factory function to create cash flow tab with error handling"""
    try:
        return CashFlowTab(parent_frame, ticker, **kwargs)
    except Exception as e:
        print(f"❌ Error creating cash flow tab: {e}")
        return None


def create_universal_chart_manager(parent_frame, layout_template=None, title="Financial Analysis"):
    """Factory function to create universal chart manager with error handling"""
    try:
        if layout_template is None:
            layout_template = LayoutTemplate.MAIN_PLUS_ANALYSIS
        return UniversalChartManager(parent_frame, layout_template, title)
    except Exception as e:
        print(f"❌ Error creating universal chart manager: {e}")
        return None


# Chart registry for dynamic chart creation (future feature)
CHART_REGISTRY = {
    'revenue': {
        'name': 'Revenue Chart',
        'description': 'Quarterly revenue analysis with growth metrics',
        'class': 'RevenueChart',
        'tab_class': 'RevenueTab',
        'icon': '📈',
        'layout_template': 'MAIN_PLUS_ANALYSIS'  # NEW
    },
    'cashflow': {
        'name': 'Free Cash Flow Chart', 
        'description': 'Quarterly free cash flow analysis with QoQ changes',
        'class': 'CashFlowChart',
        'tab_class': 'CashFlowTab',
        'icon': '💰',
        'layout_template': 'MAIN_PLUS_ANALYSIS'  # NEW
    }
    # Future charts can be added here:
    # 'income': {...},
    # 'margins': {...},
    # 'ratios': {...},
}


def get_chart_info(chart_type: str):
    """Get information about a specific chart type"""
    return CHART_REGISTRY.get(chart_type, None)


def list_available_chart_types():
    """Get list of available chart types"""
    return list(CHART_REGISTRY.keys())


# Configuration for chart defaults
CHART_DEFAULTS = {
    'responsive_sizing': True,
    'max_quarters': 12,
    'show_value_labels': True,
    'show_growth_metrics': True,
    'dark_theme': True,
    'animation_enabled': False,  # Future feature
    'use_universal_manager': True,  # NEW: Use universal chart manager by default
    'enable_collapsible_sections': True,  # NEW: Enable collapsible chart sections
    'show_qoq_analysis': True,  # NEW: Show QoQ analysis by default
}


def get_chart_defaults():
    """Get default chart configuration"""
    return CHART_DEFAULTS.copy()


# Utility functions
def validate_financial_data(financial_data):
    """Validate financial data structure"""
    if not financial_data:
        return False, "No financial data provided"
    
    if not isinstance(financial_data, list):
        return False, "Financial data must be a list"
    
    if len(financial_data) == 0:
        return False, "Financial data list is empty"
    
    # Check if first item has required attributes
    first_item = financial_data[0]
    required_attrs = ['date', 'revenue']
    
    for attr in required_attrs:
        if not hasattr(first_item, attr):
            return False, f"Financial data missing required attribute: {attr}"
    
    return True, "Valid financial data"


def format_currency(value, currency_symbol="$", scale="B"):
    """Format currency values for display"""
    if value == 0:
        return "No Data"
    
    if scale == "B":  # Billions
        formatted_value = value / 1e9
        return f"{currency_symbol}{formatted_value:.2f}B"
    elif scale == "M":  # Millions
        formatted_value = value / 1e6
        return f"{currency_symbol}{formatted_value:.2f}M"
    else:
        return f"{currency_symbol}{value:,.2f}"


def calculate_growth_rate(current_value, previous_value):
    """Calculate growth rate between two values"""
    if previous_value == 0:
        return None
    
    growth_rate = ((current_value - previous_value) / abs(previous_value)) * 100
    return growth_rate


# Export utility functions
__all__.extend([
    'get_available_charts',
    'create_revenue_tab', 
    'create_cashflow_tab',
    'create_universal_chart_manager',  # NEW
    'get_chart_info',
    'list_available_chart_types',
    'get_chart_defaults',
    'validate_financial_data',
    'format_currency',
    'calculate_growth_rate',
    'CHART_REGISTRY',
    'CHART_DEFAULTS'
])