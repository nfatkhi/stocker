# Stocker App

A modular stock market analysis application built with Python and tkinter, featuring real-time charts, technical indicators, live price monitoring, and comprehensive financial analysis. 
!very Important: code should be aplicable to all companies irrelevant of their type of business.
!very important: if you want to make changes in additional files, in accordance with their functions, bring it up and ask me to upload them to you.
Claude Integration Note: Always include current config.py content in requests and ask Claude to use defensive imports (try/except) for any new config sections to prevent ImportError crashes.
## Project Structure

```
stocker_app/
├── components/                    # 🎯 Reusable UI components
│   ├── __init__.py
│   ├── analyzer.py               # Legacy analysis component
│   ├── chart_manager.py          # Interactive charts (candlestick, volume, RSI)
│   ├── data_fetcher.py           # Multi-source financial data fetching
│   ├── financials_manager.py     # 🆕 Financial analysis with interactive charts
│   ├── live_price_indicator.py   # Real-time price display & market status
│   ├── metrics_display.py        # Stock metrics display
│   ├── news_manager.py           # News component (legacy)
│   └── revenue_analyzer.py       # Revenue analysis (legacy)
├── core/                         # 🏗️ Foundation systems  
│   ├── __init__.py
│   ├── app.py                    # Core application logic
│   └── event_system.py           # Event-driven communication
├── data/                         # 📊 Data models & structures
│   ├── __init__.py
│   └── models.py                 # Data models and structures
├── ui/                          # 🖼️ Main application interface
│   ├── __init__.py
│   └── main_window.py           # Primary application window with financial tabs
├── widgets/                     # 🔧 UI widget library
│   ├── __init__.py
│   └── [widget components]      # Reusable UI widgets
├── utils/                       # 🛠️ Shared utilities
│   └── __init__.py
├── tests/                       # 🧪 Test suite
├── main.py                      # 🚀 Application entry point
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── Core dependencies.txt        # Core dependency list
└── # Stocker Project Snapshot.md # Project documentation
```

## Architecture Principles

This application follows **Event-Driven Architecture (EDA)** with strict modular design:

### Core Patterns
- **Single Responsibility**: Each component has one clear purpose
- **Event Communication**: Components interact via `EventBus`, not direct calls
- **Separation of Concerns**: UI, business logic, and data access are isolated
- **Reusable Widgets**: All UI components designed for modularity

### Component Design Rules
```python
# ✅ GOOD - Event-driven communication
self.event_bus.publish(Event(EventType.DATA_RECEIVED, {'stock_data': data}))

# ❌ BAD - Direct coupling
self.chart_manager.update_with_data(data)
```

### Integration Pattern
Every widget follows this integration standard:
```python
# Widget creation with event bus integration
self.financials_manager = FinancialsManager(
    parent=financials_frame,
    theme_colors=theme_colors,
    event_bus=self.event_bus
)

# Theme consistency across all components
theme_colors = {
    'bg': '#333333',
    'frame': '#444444', 
    'text': '#e0e0e0',
    'header': '#6ea3d8',
    'success': '#5a9c5a',
    'error': '#d16a6a',
    'warning': '#d8a062'
}
```

## Current Implementation

### Event System (`core/event_system.py`)
- **EventBus**: Central communication hub
- **Event Types**: DATA_RECEIVED, DATA_FETCH_STARTED, DATA_FETCH_COMPLETED, STOCK_SELECTED
- **Pub/Sub Pattern**: Loose coupling between components

### Financial Analysis (`components/financials_manager.py`) 🆕
**Features:**
- **Three analysis tabs**: Revenue & Growth, Profitability, Balance Sheet
- **Interactive matplotlib charts** with mouse hover annotations
- **20 quarters of financial data** from Finnhub/Yahoo Finance
- **Real-time metrics cards** with color-coded health indicators
- **Vertical bar charts** with exact value tooltips
- **Professional dark theme** integration

**Chart Types:**
- **Revenue Analysis**: Quarterly revenue trends with growth calculations
- **Profitability**: Net income with profit/loss color coding and zero line
- **Balance Sheet**: Cash vs Debt comparison with grouped bars

**Data Display:**
- Latest quarter highlights with key financial metrics
- 12-quarter rolling averages and growth rates
- Financial health indicators (margins, debt ratios)
- Mouse hover shows exact dollar amounts

### Data Fetching Architecture (Dual System) 🔄

**The application uses TWO separate data fetching systems for different purposes:**

#### **Financial Data Fetching (`components/data_fetcher.py`)**
- **Purpose**: Quarterly financial statements for FinancialsManager
- **Sources**: Finnhub API → Yahoo Finance → Mock data fallback
- **Data Types**: 20 quarters of revenue, net income, balance sheet data
- **Integration**: Event-driven via EventBus (DATA_RECEIVED events)
- **Update Frequency**: On-demand when stock selected

#### **Chart Data Fetching (`components/chart_manager.py`)**
- **Purpose**: OHLCV price data + live price updates for charts
- **Sources**: Polygon.io → Yahoo Finance (+ Alpha Vantage legacy)
- **Data Types**: Hourly/daily OHLCV, live price feeds, market status
- **Integration**: Self-contained within ChartManager class
- **Update Frequency**: Real-time (15s market hours, 30s extended, 60s closed)

#### **Why Two Systems Exist:**
- **Different data needs**: Financial statements vs price charts vs live feeds
- **Different update patterns**: Quarterly vs real-time vs on-demand
- **Specialized APIs**: Polygon for quality hourly data, Finnhub for financials
- **Independent development**: Charts and financials evolved separately

#### **API Key Distribution:**
```python
# config.py provides keys to both systems
API_KEYS = {
    "finnhub": "...",    # Used by data_fetcher.py
    "polygon": "...",    # Used by chart_manager.py  
    "alpha_vantage": "..." # Legacy in chart_manager.py
}

# chart_manager.py receives keys during initialization
chart_manager = EnhancedChartManager(event_bus, api_keys=API_KEYS)

# data_fetcher.py receives keys during initialization  
data_fetcher = DataFetcher(event_bus, API_KEYS)
```

#### **Data Flow Pattern:**
```
User Selects Stock
├── data_fetcher.py → Quarterly financials → FinancialsManager
└── chart_manager.py → OHLCV + live prices → Interactive charts
```

**Data Structure (from `data/models.py`):**
```python
@dataclass
class QuarterlyFinancials:
    date: str
    revenue: float
    net_income: float
    gross_profit: float
    operating_income: float
    assets: float
    cash: float
    debt: float
    eps: float
```

### Live Price Display (`components/live_price_indicator.py`)
**Features:**
- Real-time price updates (15s market hours, 30s extended, 60s closed)
- Market status detection (Open/Closed/Pre-market/After-hours)
- Price change with color coding (+green, -red)
- Eastern timezone market hours
- Integration callback for chart live price line

### Application Core (`core/app.py` & `core/event_system.py`)
**Features:**
- Centralized application lifecycle management
- Event-driven communication between all components
- Configuration management via `config.py`
- Modular component initialization

## Main Window Structure (`ui/main_window.py`)

**Tab Organization:**
1. **Overview** - Key metrics cards (Price, Market Cap, P/E, Volume)
2. **Charts** - Interactive price charts with technical indicators
3. **Financials** - Financial analysis with three sub-tabs 🆕
4. **News** - Stock news and updates
5. **Analysis** - Advanced analysis tools

**Financial Tab Integration:**
```python
def _setup_financials_tab(self):
    financials_frame = self.tab_manager.get_tab_frame('Financials')
    
    # Clear any placeholder content
    for widget in financials_frame.winfo_children():
        widget.destroy()
    
    # Create FinancialsManager directly in tab frame
    self.financials_manager = FinancialsManager(
        parent=financials_frame,
        theme_colors=theme_colors,
        event_bus=self.event_bus
    )
```

## Event Flow Architecture

### Stock Selection Flow:
1. **User Input** → `STOCK_SELECTED` event
2. **DataFetcher** → Fetches from Finnhub → Yahoo → Mock data
3. **DataFetcher** → `DATA_RECEIVED` event with StockData object
4. **All Components** → Update displays simultaneously

### Data Structure in Events:
```python
# Event data structure
{
    'stock_data': StockData(
        ticker='AAPL',
        quarterly_financials=[...],  # 20 quarters
        daily_prices={...},          # 90 days
        current_price=150.25,
        market_cap=2500000000000
    )
}
```

## UI Theme System

Consistent dark theme across all components:
```python
THEME_COLORS = {
    'bg': '#333333',
    'frame': '#444444', 
    'text': '#e0e0e0',
    'header': '#6ea3d8',
    'success': '#5a9c5a',    # Green for gains/good metrics
    'error': '#d16a6a',      # Red for losses/poor metrics  
    'warning': '#d8a062',    # Orange for moderate metrics
    'button': '#8a8a8a',
    'button_text': '#2a2a2a',
    'accent': '#8a8a8a'
}
```

## Configuration

### Configuration Management (`config.py`)
```python
# API Keys and settings managed in config.py
API_KEYS = {
    "finnhub": "your_finnhub_api_key",
    "polygon": "your_polygon_api_key"
}

SETTINGS = {
    "default_ticker": "AAPL",
    "update_interval": 15,
    "cache_timeout": 300
}
```

### Dependencies (`requirements.txt`)
```bash
# Core dependencies from requirements.txt
tkinter
matplotlib 
mplfinance 
pandas 
numpy 
yfinance 
requests 
pytz
```

### Core Dependencies (`Core dependencies.txt`)
Essential system dependencies documented separately for deployment.

## Current Features

### Working ✅
- **Real-time price monitoring** with market status
- **Interactive price charts** with full pan/zoom functionality
- **Technical indicators** (RSI, moving averages)
- **Financial analysis dashboard** with 20 quarters of data 🆕
- **Interactive financial charts** with hover tooltips 🆕
- **Multiple timeframes** (hourly with live updates, daily historical)
- **Event-driven architecture** with loose coupling
- **Consistent theming** across all components
- **Robust data fetching** with Finnhub + Yahoo Finance fallbacks

### Financial Analysis Features 🆕
- **Revenue & Growth Analysis**: Quarterly trends, growth rates, 12Q averages
- **Profitability Analysis**: Net income trends, margin analysis, profit/loss indicators
- **Balance Sheet Analysis**: Cash vs debt trends, financial health metrics
- **Interactive Charts**: Mouse hover shows exact values, color-coded health indicators
- **Comprehensive Metrics**: Latest quarter highlights, health scoring, trend analysis

### In Development 🚧
- Portfolio tracking and performance metrics
- Additional technical indicators (MACD, Bollinger Bands)
- Price alerts and notifications
- Stock news integration
- Advanced chart annotations

### Planned 📋
- Financial statement drill-down (10-K, 10-Q integration)
- Peer comparison analysis
- Options chain analysis
- Paper trading simulation
- Export functionality (PDF reports, CSV data)

## Known Issues & Technical Debt

### Current Issues
- **Financial charts** work perfectly but require matplotlib as dependency
- **Data access pattern** in FinancialsManager needs `stock_data.quarterly_financials` structure
- **UI nesting** - removed extra wrapper layers but some tabs may still have redundant containers

### Legacy Components (May Need Cleanup)
- `components/analyzer.py` - Legacy analysis component
- `components/news_manager.py` - News component (158 bytes, likely placeholder)
- `components/revenue_analyzer.py` - Revenue analysis (170 bytes, likely placeholder)
- These components may be superseded by the new FinancialsManager

### Technical Debt
- **Dual data fetching systems** - `data_fetcher.py` and `chart_manager.py` handle different data independently
- **API key management** - Scattered across multiple components instead of centralized
- **Code duplication** - Error handling, API patterns repeated between fetchers
- `chart_manager.py` could benefit from further modularization (1000+ lines)
- Error handling needs standardization across components
- Unit tests needed for financial analysis components (tests/ directory exists but may be empty)
- Date parsing in FinancialsManager handles multiple formats but could be cleaner
- Legacy components should be evaluated for removal or integration

### Performance
- Large financial datasets (20+ quarters) render quickly with matplotlib
- Memory usage optimized with 12-quarter display window
- Hover interactions are responsive with proper event handling

### API Limitations
- **Finnhub**: 60 calls/minute (excellent rate limit)
- **Yahoo Finance**: Rate limiting for excessive requests
- **Financial data**: Some companies may have incomplete quarterly reports

## Integration Patterns Used

### Financial Component Integration (`components/financials_manager.py`)
```python
# 1. Event subscription in __init__
self.event_bus.subscribe(EventType.DATA_RECEIVED, self._on_data_received)

# 2. Data extraction from event
def _on_data_received(self, event):
    stock_data_obj = event.data.get('stock_data')
    financials = getattr(stock_data_obj, 'quarterly_financials', [])
    
# 3. Chart update with hover functionality
def _add_hover_functionality(self, canvas, ax, bars, values, quarters, metric_name):
    # Mouse hover shows exact financial values
```

### Data Fetching Integration (`components/data_fetcher.py`)
```python
# Multi-source fallback strategy
quarterly_data = self._fetch_quarterly_financials_finnhub(ticker)
if not quarterly_data:
    quarterly_data = self._fetch_quarterly_financials_yahoo(ticker)
if not quarterly_data:
    quarterly_data = self._generate_mock_quarterly_data(ticker)
```

### Clean UI Integration (`ui/main_window.py`)
```python
# Remove placeholder content before adding real components
for widget in parent_frame.winfo_children():
    widget.destroy()

# Create component directly in parent frame (no extra wrappers)
component = FinancialsManager(parent=parent_frame, ...)
```

### Configuration Integration (`config.py`)
```python
# Centralized configuration management
from config import API_KEYS, SETTINGS

# Component initialization with config
data_fetcher = DataFetcher(event_bus, API_KEYS)
```

## Architecture Mantras

1. **"If it's a different concern, it's a different component"**
2. **"Communicate through events, not direct calls"**  
3. **"Make it reusable from day one"**
4. **"Theme everything, hardcode nothing"**
5. **"Clean up after yourself (lifecycle management)"**
6. **"Interactive charts need hover tooltips"** 🆕
7. **"Financial data requires robust fallback strategies"** 🆕
8. **"All data fetching MUST go through data_fetcher.py"** ⚠️

## ⚠️ **Critical Architectural Exception**

**The `chart_manager.py` contains its own data fetching logic - THIS IS AN EXCEPTION and should NEVER happen again.**

### **Why This Exception Exists:**
- ChartManager was developed before the centralized data fetching architecture
- Real-time price feeds required specialized handling not available in data_fetcher.py
- Different data requirements (OHLCV vs quarterly financials) justified separate systems

### **Future Development Rule:**
🚫 **NO new components should contain data fetching logic**  
✅ **ALL data fetching must be handled by `data_fetcher.py` or dedicated data service**  
✅ **Components should ONLY receive data via EventBus events**  
✅ **API calls should be centralized for consistency, error handling, and maintainability**

### **Exception Justification:**
This architectural inconsistency is acknowledged technical debt that should be refactored in a future version to centralize all data operations. The dual system exists due to historical development but violates the principle of single responsibility for data access.

## Next Development Priorities

1. **Data Architecture Unification** 🔄: Consider consolidating data fetching systems
   - Centralize API management and error handling
   - Unified data source configuration
   - Consistent fallback patterns across components
2. **Peer Comparison**: Add industry/sector comparison charts
3. **Financial Health Scoring**: Expand the scoring algorithm
4. **Export Features**: PDF reports, CSV downloads
5. **Alert System**: Financial threshold notifications
6. **Historical Analysis**: 5+ year trend analysis

This modular approach ensures clean, scalable code that can accommodate new trading and financial analysis features without disrupting existing functionality.