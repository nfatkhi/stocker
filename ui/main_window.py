# ui/main_window.py - Updated with Widget Safety

import tkinter as tk
from tkinter import ttk
from core.event_system import EventBus, Event, EventType
from ui.widgets import (
    TickerInput, StatusBar, TabManager, 
    LoadingSpinner, MetricCard, StockChart
)

# REMOVED: financials_manager import - using direct chart system now


class MainWindow:
    """Main application window - simplified without financials_manager + Widget Safety"""
    
    def __init__(self, root, event_bus):
        self.root = root
        self.event_bus = event_bus
        
        self._setup_window()
        self._create_widgets()
        self._setup_layout()
        self._populate_tabs()
        self._subscribe_to_events()
        
        # Force initial update
        self.root.update_idletasks()
        
        print("🖼️ Main Window initialized with Widget Safety")
    
    def _setup_window(self):
        """Configure main window"""
        self.root.title("Stocker - Stock Analysis with Background Cache")
        self.root.configure(bg='#f0f0f0')
        self.root.minsize(1200, 800)  # Larger minimum for financial charts
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Header frame
        self.header_frame = ttk.Frame(self.root)
        
        # Ticker input widget
        self.ticker_input = TickerInput(
            self.header_frame, 
            self.event_bus
        )
        
        # Tab manager with Financials tab
        self.tab_manager = TabManager(self.root, self.event_bus)
        
        # Status bar
        self.status_bar = StatusBar(self.root, self.event_bus)
        
        # Loading spinner (initially hidden)
        self.loading_spinner = LoadingSpinner(
            self.root,
            text="Loading from cache..."
        )
    
    def _setup_layout(self):
        """Arrange widgets in window"""
        # Header
        self.header_frame.pack(fill='x', padx=10, pady=5)
        self.ticker_input.pack(side='left')
        
        # Main content (tabs)
        self.tab_manager.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Status bar at bottom
        self.status_bar.pack(fill='x', side='bottom')
    
    def _populate_tabs(self):
        """Add content to each tab - UPDATED for cache system"""
        # Overview Tab - Add metric cards
        self._setup_overview_tab()
        
        # Charts Tab - Basic charts (placeholder)
        self._setup_charts_tab()
        
        # Financials Tab - This will be handled by chart_manager in app.py
        self._setup_financials_tab()
        
        # Analysis Tab - Add analyzer content
        self._setup_analysis_tab()
        
        # ENSURE ALL TABS ARE ENABLED INITIALLY
        self._enable_all_tabs()
    
    def _setup_overview_tab(self):
        """Setup overview tab with metric cards"""
        overview_frame = self.tab_manager.get_tab_frame('Overview')
        
        # Create a frame for metrics
        metrics_frame = ttk.Frame(overview_frame)
        metrics_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(
            metrics_frame,
            text="Key Metrics Overview",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Cache status indicator
        cache_status_frame = ttk.Frame(metrics_frame)
        cache_status_frame.pack(pady=(0, 10))
        
        self.cache_status_label = ttk.Label(
            cache_status_frame,
            text="📁 Background cache system active",
            font=('Arial', 10),
            foreground='#2196F3'
        )
        self.cache_status_label.pack()
        
        # Metrics container (grid layout)
        self.metrics_container = ttk.Frame(metrics_frame)
        self.metrics_container.pack()
        
        # Create metric cards - FIXED constructor calls
        self.metric_cards = {
            'price': MetricCard(
                self.metrics_container,
                title="Current Price",
                initial_value="--"  # Fixed: changed from value= to initial_value=
            ),
            'market_cap': MetricCard(
                self.metrics_container,
                title="Market Cap",
                initial_value="--"  # Fixed: changed from value= to initial_value=
            ),
            'pe_ratio': MetricCard(
                self.metrics_container,
                title="P/E Ratio",
                initial_value="--"  # Fixed: changed from value= to initial_value=
            ),
            'cache_status': MetricCard(
                self.metrics_container,
                title="Cache Status",
                initial_value="Ready"  # Fixed: changed from value= to initial_value=
            )
        }
        
        # Arrange in grid
        self.metric_cards['price'].grid(row=0, column=0, padx=10, pady=10)
        self.metric_cards['market_cap'].grid(row=0, column=1, padx=10, pady=10)
        self.metric_cards['pe_ratio'].grid(row=1, column=0, padx=10, pady=10)
        self.metric_cards['cache_status'].grid(row=1, column=1, padx=10, pady=10)
    
    def _setup_charts_tab(self):
        """Setup charts tab - placeholder for future chart types"""
        charts_frame = self.tab_manager.get_tab_frame('Charts')
        
        # Clear any existing content
        for widget in charts_frame.winfo_children():
            widget.destroy()
        
        # Add placeholder content explaining the new structure
        info_frame = ttk.Frame(charts_frame)
        info_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        title_label = ttk.Label(
            info_frame,
            text="📈 Charts & Visualizations",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        info_text = ttk.Label(
            info_frame,
            text="This tab is available for additional chart types:\n\n" +
                 "• Stock price charts\n" +
                 "• Technical analysis indicators\n" +
                 "• Market comparison charts\n" +
                 "• Custom visualizations\n\n" +
                 "💡 Financial charts (Revenue & FCF) are located in the 'Financials' tab",
            font=('Arial', 12),
            justify='center'
        )
        info_text.pack(expand=True)
    
    def _setup_financials_tab(self):
        """Setup financials tab - will be populated by chart_manager"""
        financials_frame = self.tab_manager.get_tab_frame('Financials')
        
        # Clear any existing content
        for widget in financials_frame.winfo_children():
            widget.destroy()
        
        # Add placeholder that will be replaced by chart_manager
        placeholder_label = ttk.Label(
            financials_frame,
            text="📊 Financial Analysis\n\n" +
                 "Chart manager will populate this tab with:\n" +
                 "• Revenue analysis with YoY comparison\n" +
                 "• Free Cash Flow analysis with YoY comparison\n" +
                 "• Data loaded instantly from background cache\n\n" +
                 "Select a stock ticker to begin analysis...",
            font=('Arial', 12),
            justify='center'
        )
        placeholder_label.pack(expand=True)
        
        print("📊 Financials tab setup - ready for chart_manager")
    
    def _setup_analysis_tab(self):
        """Setup analysis tab - placeholder for analyzer component"""
        analysis_frame = self.tab_manager.get_tab_frame('Analysis')
        
        # Clear any existing content
        for widget in analysis_frame.winfo_children():
            widget.destroy()
        
        # Add placeholder content
        placeholder_label = ttk.Label(
            analysis_frame,
            text="🔍 Stock Analysis\n\n" +
                 "This tab will contain:\n" +
                 "• Stock analysis tools\n" +
                 "• Financial ratios\n" +
                 "• Comparative analysis\n" +
                 "• Custom metrics\n\n" +
                 "Component will be connected by app.py...",
            font=('Arial', 12),
            justify='center'
        )
        placeholder_label.pack(expand=True)
    
    def _enable_all_tabs(self):
        """Ensure all tabs are enabled and clickable"""
        try:
            num_tabs = self.tab_manager.index("end")
            for i in range(num_tabs):
                self.tab_manager.tab(i, state='normal')
            print(f"✅ All {num_tabs} tabs enabled")
        except Exception as e:
            print(f"⚠️ Error enabling tabs: {e}")
    
    def _subscribe_to_events(self):
        """Subscribe to relevant events - UPDATED for cache system"""
        # Cache-related events
        cache_events = [
            EventType.DATA_RECEIVED,
            EventType.DATA_FETCH_COMPLETED,
            EventType.DATA_FETCH_STARTED
        ]
        
        # Show loading when fetching starts
        self.event_bus.subscribe(
            EventType.DATA_FETCH_STARTED,
            self._show_loading
        )
        
        # Hide loading when data is received
        for event_type in cache_events:
            self.event_bus.subscribe(event_type, self._hide_loading)
        
        # Update UI when data is received
        self.event_bus.subscribe(
            EventType.DATA_RECEIVED,
            self._update_ui
        )
        
        # Listen for cache status updates
        self.event_bus.subscribe(
            EventType.STATUS_UPDATED,
            self._update_cache_status
        )
    
    # ========================================
    # WIDGET SAFETY METHODS - ADDED
    # ========================================
    
    def _is_widget_valid(self, widget):
        """Check if a widget is still valid and not destroyed"""
        if not widget:
            return False
        try:
            # Test if widget still exists
            widget.winfo_exists()
            return True
        except tk.TclError:
            return False
        except Exception:
            return False
    
    def _safe_widget_config(self, widget, **config):
        """Safely configure a widget with validation"""
        try:
            if self._is_widget_valid(widget):
                widget.config(**config)
                return True
            else:
                return False
        except tk.TclError:
            return False
        except Exception as e:
            print(f"⚠️ Error configuring widget: {e}")
            return False
    
    def _safe_update_metric_card(self, card_name, value, trend='neutral'):
        """Safely update a metric card"""
        try:
            if hasattr(self, 'metric_cards') and card_name in self.metric_cards:
                card = self.metric_cards[card_name]
                if hasattr(card, 'is_valid') and card.is_valid():
                    return card.update_value(value, trend)
                elif hasattr(card, 'update_value'):
                    try:
                        card.update_value(value, trend)
                        return True
                    except tk.TclError:
                        print(f"⚠️ Metric card '{card_name}' destroyed, skipping update")
                        return False
            return False
        except Exception as e:
            print(f"❌ Error updating metric card '{card_name}': {e}")
            return False
    
    # ========================================
    # EVENT HANDLERS - UPDATED WITH WIDGET SAFETY
    # ========================================
    
    def _show_loading(self, event):
        """Show loading state - updated for cache system"""
        print("🔄 Loading started")
        
        # Update cache status metric card safely
        self._safe_update_metric_card('cache_status', "Loading...", 'neutral')
    
    def _hide_loading(self, event):
        """Hide loading state - UPDATED WITH WIDGET SAFETY"""
        print("✅ Loading completed")
        
        # Ensure all tabs are enabled
        self._enable_all_tabs()
        
        # Update cache status safely
        cache_hit = event.data.get('metadata', {}).get('cache_hit', False)
        status_text = "Cache Hit" if cache_hit else "Live Data"
        self._safe_update_metric_card('cache_status', status_text, 'up' if cache_hit else 'neutral')
        
        # Update cache status label safely
        if hasattr(self, 'cache_status_label'):
            self._safe_widget_config(self.cache_status_label, text=status_text)
        
        # Force UI update
        self.root.after_idle(self._enable_all_tabs)
    
    def _update_ui(self, event):
        """Update UI with analysis results - UPDATED WITH WIDGET SAFETY"""
        data = event.data
        
        # Ensure tabs are enabled
        self._enable_all_tabs()
        
        # Update metric cards if data contains metrics
        if 'stock_data' in data:
            stock_data = data['stock_data']
            
            # Update basic info safely
            if hasattr(self, 'metric_cards'):
                # Update price if available (EdgarTools doesn't provide real-time prices)
                self._safe_update_metric_card('price', "N/A (Fundamental)", 'neutral')
                
                # Update market cap if available
                if stock_data.market_cap > 0:
                    market_cap_b = stock_data.market_cap / 1e9
                    self._safe_update_metric_card('market_cap', f"{market_cap_b:.2f}")
                
                # Update P/E ratio if available
                if stock_data.pe_ratio:
                    self._safe_update_metric_card('pe_ratio', f"{stock_data.pe_ratio:.2f}")
        
        # Update cache status based on metadata
        metadata = data.get('metadata', {})
        quarters_found = metadata.get('quarters_found', 0)
        cache_hit = metadata.get('cache_hit', False)
        
        # Update cache status label safely - FIXED THE PROBLEMATIC LINE
        if hasattr(self, 'cache_status_label'):
            status_text = f"📁 Cache: {quarters_found} quarters" if cache_hit else f"🌐 Live: {quarters_found} quarters"
            self._safe_widget_config(self.cache_status_label, text=status_text)  # SAFE VERSION
        
        print(f"🖼️ UI updated - Cache hit: {cache_hit}, Quarters: {quarters_found}")
    
    def _update_cache_status(self, event):
        """Update cache status from background refresh - COMPLETELY REWRITTEN FOR SAFETY"""
        try:
            message = event.data.get('message', '')
            level = event.data.get('level', 'info')
            
            if 'cache' in message.lower():
                # Update cache status label safely - FIXED THE CRASH LINE
                if hasattr(self, 'cache_status_label'):
                    cache_message = f"📁 {message}"
                    self._safe_widget_config(self.cache_status_label, text=cache_message)  # SAFE VERSION
                
                # Update cache status metric card safely
                self._safe_update_metric_card('cache_status', "Updated", 'up')
            
            print(f"📊 Cache status update: {message}")
            
        except Exception as e:
            print(f"❌ Error updating cache status: {e}")
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_tab_frame(self, tab_name: str):
        """Get tab frame by name - for component connection"""
        return self.tab_manager.get_tab_frame(tab_name)
    
    def debug_tab_states(self):
        """Debug method to check tab states"""
        try:
            num_tabs = self.tab_manager.index("end")
            states = []
            for i in range(num_tabs):
                state = self.tab_manager.tab(i, "state")
                text = self.tab_manager.tab(i, "text")
                states.append(f"{text}: {state}")
            print(f"🔍 Tab states: {states}")
            return states
        except Exception as e:
            print(f"❌ Error checking tab states: {e}")
            return []
    
    def validate_all_widgets(self):
        """Validate all widgets and report status - NEW DEBUG METHOD"""
        try:
            print("🔍 Validating all widgets...")
            
            # Check metric cards
            if hasattr(self, 'metric_cards'):
                for name, card in self.metric_cards.items():
                    if hasattr(card, 'is_valid'):
                        valid = card.is_valid()
                        print(f"   Metric card '{name}': {'✅' if valid else '❌'}")
                    else:
                        print(f"   Metric card '{name}': ⚠️ No validation method")
            
            # Check other important widgets
            widgets_to_check = ['cache_status_label']
            for widget_name in widgets_to_check:
                if hasattr(self, widget_name):
                    widget = getattr(self, widget_name)
                    valid = self._is_widget_valid(widget)
                    print(f"   Widget '{widget_name}': {'✅' if valid else '❌'}")
            
            print("✅ Widget validation complete")
            
        except Exception as e:
            print(f"❌ Error validating widgets: {e}")


# Test the updated main window
if __name__ == "__main__":
    from core.event_system import EventBus
    
    root = tk.Tk()
    event_bus = EventBus()
    
    try:
        main_window = MainWindow(root, event_bus)
        print("✅ Updated Main Window with Widget Safety created successfully")
        print("📊 Ready for cache-powered chart system")
        
        # Test tab states
        main_window.debug_tab_states()
        
    except Exception as e:
        print(f"❌ Failed to create main window: {e}")
        import traceback
        traceback.print_exc()
    
    # Don't run mainloop in test
    # root.mainloop()