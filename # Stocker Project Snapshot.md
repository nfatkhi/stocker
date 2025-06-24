# Stocker App

A modular stock market analysis application built with Python and tkinter, featuring real-time charts, technical indicators, live price monitoring, and comprehensive financial analysis with **automatic ticker discovery** and **Year-over-Year (YoY) analysis**.

**Important**: Keep code concise and responses focused. Ask for clarification regarding app architecture before making changes. Code should be applicable to all companies regardless of business type.

**Claude Integration**: Always include current config.py content and use defensive imports (try/except) for new config sections to prevent ImportError crashes.

**File naming**: Keep file names with a 1-sentence description as the 1st line of each file.
- **Interactive Charts**: All financial charts must include mouseover tooltips showing exact values and quarter/year information

## Latest Updates 🆕

**Simplified Data Architecture & YoY Analysis** - Replaced complex data merging with direct routing (Polygon.io FCF → FCF tab, SEC EDGAR Revenue → Revenue tab) and upgraded both tabs to use Year-over-Year analysis for better seasonal insights. Enhanced scrolling system centralized in BaseChart for universal trackpad/mouse wheel support across all charts.

**Streamlined FCF Tab with QoQ Analysis** - Rebuilt Free Cash Flow tab with clean, efficient architecture:
- **3-section scrollable layout**: Summary cards + Main FCF chart + QoQ analysis chart
- **Quarter-over-Quarter analysis**: Interactive chart showing percentage change between consecutive quarters with color-coded bars
- **Streamlined codebase**: Reduced from 1300+ lines to ~300 lines while preserving all functionality
- **Mouse wheel scrolling**: Full scroll functionality with visual scrollbar for easy navigation
- **Interactive charts**: Hover tooltips with exact values and quarter information

**Auto CIK Discovery System** - Intelligent ticker lookup via SEC's official database:
- **Real-time discovery**: Unknown tickers searched in SEC's `company_tickers.json` (10,000+ companies)
- **Exact match only**: No fuzzy matching to prevent false positives
- **User-only mode**: No background processing - only looks up tickers when requested
- **Smart caching**: Auto-discovered companies cached locally for instant future access
- **SEC compliance**: Proper rate limiting and headers for SEC API usage

## Project Structure

```
stocker_app/
├── components/                    # 🎯 Reusable UI components
│   ├── __init__.py
│   ├── analyzer.py               # Stock analysis component with financial metrics
│   ├── auto_cik_updater.py       # Automatic CIK discovery using SEC company_tickers.json
│   ├── chart_manager.py          # Interactive charts coordinator (candlestick, volume, RSI)
│   ├── charts/                   # 📊 Chart components folder
│   │   ├── __init__.py
│   │   ├── base_chart.py         # Base chart class with enhanced scrolling functionality
│   │   ├── cashflow_chart.py     # 🆕 STREAMLINED FCF + YoY analysis (17 KB)
│   │   ├── revenue_chart.py      # Revenue analysis chart with YoY analysis (17 KB)
│   │   └── universal_chart_manager.py # Layout manager for complex charts
│   ├── cik_library.py            # Dynamic CIK library with persistent caching
│   ├── data_fetcher.py           # Enhanced data fetcher with separated routing (37 KB)
│   ├── financials_manager.py     # Financial analysis with separated data routing (26 KB)
│   ├── live_price_indicator.py   # Real-time price display & market status
│   ├── metrics_display.py        # Stock metrics display
│   ├── news_manager.py           # News component
│   └── revenue_analyzer.py       # Revenue analysis
├── core/                         # 🏗️ Foundation systems  
│   ├── __init__.py
│   ├── app.py                    # Core application logic
│   └── event_system.py           # Event-driven communication
├── data/                         # 📊 Data models & structures
│   ├── __init__.py
│   ├── cik_cache.json            # Persistent CIK ticker->company mappings (9 KB)
│   ├── last_cik_update.txt       # Timestamp tracking for CIK updates
│   └── models.py                 # Data models and structures
├── ui/                          # 🖼️ Main application interface
│   ├── __init__.py
│   └── main_window.py           # Primary application window with financial tabs (10 KB)
├── widgets/                     # 🧩 Custom UI widgets and components
│   ├── __init__.py
│   ├── loading_spinner.py       # Loading animation component
│   ├── metric_card.py           # Reusable metric display cards
│   ├── status_bar.py            # Application status bar
│   ├── stock_chart.py           # Stock price chart widget
│   ├── tab_manager.py           # Tab management utilities
│   ├── ticker_input.py          # Ticker input widget with validation
│   └── working_stock_chart.py   # Enhanced stock chart implementation
├── tests/                       # 🧪 Test suite
├── main.py                      # 🚀 Application entry point
├── config.py                    # Configuration with SEC EDGAR and auto-update settings (8 KB)
├── requirements.txt             # Python dependencies
├── Core dependencies.txt        # Core dependency list
└── # Stocker Project Snapshot.md # This documentation file (14 KB)
```

## Architecture Principles

Event-Driven Architecture (EDA) with intelligent data discovery and streamlined chart components:

### Core Patterns
- **Single Responsibility**: Each component has one clear purpose
- **Event Communication**: Components interact via `EventBus`, not direct calls
- **Streamlined Charts**: Clean, focused chart implementations without unnecessary complexity
- **Auto-Discovery**: Unknown tickers automatically resolved via SEC APIs
- **Smart Caching**: Discovered data persisted for performance

### FCF Tab Architecture Flow
```python
# Streamlined 3-section layout with enhanced scrolling
CashFlowChart.create_chart(financial_data)
    ↓
_process_data() → Extract FCF + Calculate YoY metrics
    ↓
_create_scrollable_layout() → Enhanced base chart scrolling
    ↓
3 Sections:
  1. _create_summary_section() → Summary cards (100px height)
  2. _create_fcf_section() → Main FCF chart (400px height)  
  3. _create_yoy_section() → YoY analysis chart (350px height)
```

### Data Architecture Flow
```python
# Simplified separated data routing (no merging)
DataFetcher:
├── Polygon.io → fcf_data (direct to FCF tab)
├── SEC EDGAR → revenue_data (direct to Revenue tab)
└── No merging or date matching required

FinancialsManager:
├── FCF Tab ← Uses fcf_data independently
└── Revenue Tab ← Uses revenue_data independently
```

### YoY Analysis Implementation
Year-over-Year (YoY) measures growth from current quarter vs same quarter previous year:

```python
# YoY calculation for seasonal comparison
yoy_index = i - 4  # 4 quarters back (same quarter previous year)
if yoy_index >= 0:
    yoy_pct = ((curr_val - prev_year_val) / abs(prev_year_val)) * 100

# Visual representation
- Green bars: >5% growth year-over-year
- Red bars: <-5% decline year-over-year
- Blue bars: -5% to +5% neutral change
```

## Current Implementation

### Streamlined FCF Tab 📊
**Enhanced CashFlow Chart** (`components/charts/cashflow_chart.py`):
- **300 lines total** (reduced from 1300+) while preserving all functionality
- **3-section scrollable layout**: Summary + FCF chart + YoY analysis
- **Interactive YoY chart**: Colored bars showing percentage changes vs same quarter previous year
- **Enhanced scrolling**: Universal trackpad/mouse wheel support from BaseChart
- **Responsive design**: Adapts to window size with proper scaling

**Key Features**:
- **Summary cards**: Data source, latest FCF, average FCF, YoY growth
- **Main FCF chart**: Interactive bar chart with quarterly FCF values  
- **YoY analysis**: Dedicated section with year-over-year percentage change visualization
- **Error handling**: Graceful fallbacks for missing data or chart failures

### SEC EDGAR Integration 🏛️
**Enhanced Data Fetcher** (`components/data_fetcher.py`):
- **Primary Source**: SEC EDGAR official APIs with proper compliance
- **Auto CIK Discovery**: Real-time lookup of unknown tickers
- **Separated Data Routing**: No complex merging, direct data paths

**Auto CIK System** (`components/auto_cik_updater.py` + `components/cik_library.py`):
- **SEC Database Access**: Searches 10,000+ companies in `company_tickers.json`
- **Exact Match Only**: No fuzzy matching prevents false positives
- **User-Only Mode**: No background processing, only on-demand lookups
- **Persistent Caching**: JSON-based local storage for discovered mappings

### Financial Analysis (`components/financials_manager.py`)
- **Separated Data Routing**: FCF data (Polygon.io) → cashflow_chart, Revenue data (SEC EDGAR) → revenue_chart
- **Lazy Loading**: Data fetched when tabs are activated
- **Event-Driven Updates**: Uses EventBus for communication

### Event System (`core/event_system.py`)
- **EventBus**: Central communication hub
- **Event Types**: DATA_RECEIVED, STOCK_SELECTED, STATUS_UPDATED
- **Auto-Discovery Events**: CIK lookup notifications

### Custom Widgets (`widgets/`)
- **Reusable Components**: Custom UI elements for consistent user experience
- **Theme Integration**: Widgets that respect application-wide dark theme

## Configuration

### SEC EDGAR Configuration
```python
SEC_EDGAR_CONFIG = {
    'contact_email': 'nfatpro@gmail.com',
    'company_name': 'Stocker App',
    'company_tickers_url': 'https://www.sec.gov/files/company_tickers.json',
    'rate_limit_delay': 0.1,
    'request_timeout': 15
}
```

### FCF Chart Configuration
```python
# In CashFlowChart class
MAX_QUARTERS = 12      # Maximum quarters to display
YOY_CAP = 500         # Cap YoY changes at ±500% for visualization
COLORS = {
    'yoy_growth': '#00C851',    # Green for >5% growth
    'yoy_decline': '#FF4444',   # Red for <-5% decline  
    'yoy_neutral': '#33B5E5'    # Blue for neutral changes
}
```

## Current Features

### Working ✅
- **Enhanced Scrolling**: Universal trackpad/mouse wheel support across all charts
- **YoY FCF Analysis**: Year-over-year FCF comparison with seasonal awareness
- **YoY Revenue Analysis**: Year-over-year revenue growth tracking
- **Separated Data Architecture**: Independent data routing without merging complexity
- **Interactive Charts**: Hover tooltips with exact dollar amounts and quarter details
- **Event-Driven Architecture**: Loose coupling between components
- **Smart Caching**: Discovered companies cached for instant future access

### FCF Tab Sections 📊
1. **Summary Cards** (100px): Data source, latest FCF, average FCF, YoY growth
2. **Main FCF Chart** (400px): Interactive bar chart with quarterly values
3. **YoY Analysis** (350px): Year-over-year percentage change visualization

### Revenue Tab Sections 📈
1. **Summary Cards** (100px): Data source, latest revenue, average revenue, YoY growth  
2. **Main Revenue Chart** (400px): Interactive bar chart with quarterly values
3. **YoY Analysis** (350px): Year-over-year percentage change visualization

### Auto-Discovery Stats 📊
- **Database Size**: 49 pre-loaded companies + auto-discovered
- **SEC Coverage**: 10,000+ companies searchable
- **Discovery Success**: ~85% of public US companies discoverable
- **Cache Performance**: Instant retrieval after first lookup

## Technical Implementation

### Streamlined Chart Creation
```python
# Single chart creation method
def create_chart(self, financial_data: List[Any]) -> bool:
    processed_data = self._process_data(financial_data)  # Extract + calculate YoY
    return self._create_scrollable_layout(processed_data)  # 3-section layout
```

### YoY Calculation Logic
```python
# For each quarter, compare with same quarter previous year
yoy_index = i - 4  # 4 quarters back
if yoy_index >= 0:
    yoy_pct = ((current_fcf - prev_year_fcf) / abs(prev_year_fcf)) * 100
    yoy_label = f"{yoy_pct:+.1f}%" if abs(yoy_pct) <= 999 else f"{yoy_pct/100:+.0f}x"
```

### Enhanced Scrollable Layout Pattern
```python
# BaseChart provides universal scrolling
class BaseChart:
    def setup_scrolling(self, canvas):
        # Trackpad-optimized scrolling with adaptive sensitivity
        canvas.bind('<Enter>', lambda e: self._setup_scroll_bindings(canvas))
        canvas.bind('<Leave>', lambda e: self._cleanup_scroll_bindings())
```

### Separated Data Routing Pattern
```python
# No merging - direct routing
DataFetcher:
    fcf_data = polygon.get_quarterly_cash_flow(ticker)
    revenue_data = sec_edgar.get_comprehensive_financials(ticker)
    
    # Send separately
    event_bus.publish({
        'fcf_data': fcf_data,        # → FCF Tab
        'revenue_data': revenue_data # → Revenue Tab
    })
```

### Auto-Discovery Pattern
```python
# Real-time ticker lookup with caching - EXACT MATCHES ONLY
def lookup_ticker_realtime(self, ticker: str):
    # 1. Check cache first
    if self.cik_library.is_ticker_supported(ticker):
        return cached_result
    
    # 2. Search SEC company_tickers.json (exact match only)
    for company_info in sec_data:
        if company_info.get('ticker', '').upper() == ticker.upper():
            # 3. Verify financial data exists
            if self._verify_has_financial_data(cik):
                # 4. Cache and return
                self.cik_library.add_manual_entry(ticker, cik, company_name)
                return result
    
    # 5. No exact match found - return None (no fuzzy matching)
    return None
```

## Architecture Mantras

1. **"If it's a different concern, it's a different component"**
2. **"Communicate through events, not direct calls"**  
3. **"Keep it simple - remove complexity, preserve functionality"**
4. **"YoY analysis reveals seasonal trends and sustainable growth patterns"** 🆕
5. **"Keep data sources separate - no unnecessary merging"** 🆕
6. **"Centralize common behavior in base classes"** 🆕
7. **"Exact match only - no dangerous fuzzy logic"**
8. **"User-triggered only - no background noise"**
9. **"SEC compliance first, performance second"**

## Recent Development Focus

### Key Architectural Improvements ✅
- **Simplified data architecture**: Eliminated complex merging, direct routing from sources
- **YoY analysis upgrade**: More meaningful seasonal comparisons than QoQ
- **Enhanced scrolling system**: Centralized in BaseChart for universal support
- **Streamlined codebase**: 75% reduction in lines while preserving functionality

### Next Development Priorities
1. **Enhanced Financial Metrics**: Add more SEC concepts (NetIncome, Assets, Debt)
2. **Performance Optimization**: Further streamline remaining chart components
3. **Advanced YoY Features**: Multi-year comparisons, seasonal adjustment capabilities
4. **Export Features**: PDF reports with YoY analysis data
5. **Alert System**: Financial threshold notifications
6. **Advanced Chart Interactions**: Zooming, panning, multi-timeframe analysis

This streamlined approach ensures clean, maintainable code with powerful financial analysis capabilities, specifically focusing on Year-over-Year analysis as a crucial tool for understanding seasonal patterns and sustainable business growth.