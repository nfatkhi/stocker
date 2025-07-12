# ui/widgets/metric_card.py - Compatible fix for existing MetricCard interface

import tkinter as tk
from tkinter import ttk

class MetricCard:
    """Metric card with enhanced widget safety checks - compatible with existing interface"""
    
    def __init__(self, parent, title, initial_value="--", width=200, height=80, **kwargs):
        """Initialize metric card - compatible with existing calls"""
        self.parent = parent
        self.title = title
        self.width = width
        self.height = height
        self._destroyed = False
        
        # Handle legacy 'value' parameter
        if 'value' in kwargs:
            initial_value = kwargs['value']
        
        # Create the card UI
        self._create_ui(initial_value)
        
    def _create_ui(self, initial_value):
        """Create the metric card UI"""
        try:
            # Main frame
            self.frame = tk.Frame(
                self.parent,
                bg='#3c3c3c',
                relief='raised',
                bd=1,
                width=self.width,
                height=self.height
            )
            self.frame.pack_propagate(False)
            
            # Title label
            self.title_label = tk.Label(
                self.frame,
                text=self.title,
                font=('Arial', 9, 'bold'),
                bg='#3c3c3c',
                fg='#ffffff',
                anchor='w'
            )
            self.title_label.pack(fill='x', padx=5, pady=(5, 0))
            
            # Value label
            self.value_label = tk.Label(
                self.frame,
                text=str(initial_value),
                font=('Arial', 12, 'bold'),
                bg='#3c3c3c',
                fg='#4CAF50',
                anchor='w'
            )
            self.value_label.pack(fill='x', padx=5, pady=(0, 5))
            
        except Exception as e:
            print(f"❌ Error creating metric card '{self.title}': {e}")
            self._destroyed = True
    
    def _is_widget_valid(self) -> bool:
        """Check if widget is still valid and not destroyed"""
        if self._destroyed:
            return False
            
        try:
            # Test if the value label still exists and is valid
            if hasattr(self, 'value_label') and self.value_label:
                # Try to access a property - this will raise TclError if destroyed
                _ = self.value_label.winfo_exists()
                return True
            return False
        except tk.TclError:
            # Widget has been destroyed
            self._destroyed = True
            return False
        except Exception:
            return False
    
    def update_value(self, value, trend='neutral', color=None):
        """Safely update the metric card value with widget validation"""
        try:
            # Check widget validity first
            if not self._is_widget_valid():
                print(f"⚠️ Metric card '{self.title}' is invalid, skipping update to '{value}'")
                return False
            
            # Update the value safely
            self.value_label.config(text=str(value))
            
            # Update color based on trend if no specific color provided
            if not color:
                color = self._get_trend_color(trend)
            
            if color:
                self.value_label.config(fg=color)
                
            return True
            
        except tk.TclError as e:
            print(f"⚠️ Widget destroyed during update for '{self.title}': {e}")
            self._destroyed = True
            return False
        except Exception as e:
            print(f"❌ Error updating metric card '{self.title}': {e}")
            return False
    
    def _get_trend_color(self, trend):
        """Get color based on trend"""
        trend_colors = {
            'up': '#4CAF50',      # Green
            'down': '#F44336',    # Red
            'neutral': '#2196F3', # Blue
            'warning': '#FF9800'  # Orange
        }
        return trend_colors.get(trend, '#ffffff')
    
    def update_title(self, new_title):
        """Safely update the title"""
        try:
            if not self._is_widget_valid():
                return False
                
            if hasattr(self, 'title_label') and self.title_label:
                self.title_label.config(text=new_title)
                self.title = new_title
                return True
            return False
        except tk.TclError:
            self._destroyed = True
            return False
        except Exception as e:
            print(f"❌ Error updating title for '{self.title}': {e}")
            return False
    
    def pack(self, **kwargs):
        """Safely pack the widget"""
        try:
            if self._is_widget_valid() and hasattr(self, 'frame'):
                self.frame.pack(**kwargs)
                return True
            return False
        except Exception as e:
            print(f"❌ Error packing metric card '{self.title}': {e}")
            return False
    
    def grid(self, **kwargs):
        """Safely grid the widget"""
        try:
            if self._is_widget_valid() and hasattr(self, 'frame'):
                self.frame.grid(**kwargs)
                return True
            return False
        except Exception as e:
            print(f"❌ Error gridding metric card '{self.title}': {e}")
            return False
    
    def destroy(self):
        """Safely destroy the widget"""
        try:
            self._destroyed = True
            
            if hasattr(self, 'frame') and self.frame:
                self.frame.destroy()
                
        except Exception as e:
            print(f"⚠️ Error destroying metric card '{self.title}': {e}")
    
    def is_valid(self):
        """Public method to check if widget is valid"""
        return self._is_widget_valid()


# Legacy compatibility functions
def safe_update_metric_card(metric_card, value, trend='neutral'):
    """Safely update a metric card with validation"""
    try:
        if hasattr(metric_card, 'is_valid') and metric_card.is_valid():
            return metric_card.update_value(value, trend)
        elif hasattr(metric_card, 'update_value'):
            # Fallback for existing metric cards without safety checks
            try:
                metric_card.update_value(value, trend)
                return True
            except tk.TclError:
                print(f"⚠️ Metric card widget destroyed, skipping update to '{value}'")
                return False
        else:
            print(f"⚠️ Invalid metric card object, skipping update")
            return False
    except Exception as e:
        print(f"❌ Error in safe metric card update: {e}")
        return False
        
    def _create_ui(self, initial_value):
        """Create the metric card UI"""
        try:
            # Main frame
            self.frame = tk.Frame(
                self.parent,
                bg='#3c3c3c',
                relief='raised',
                bd=1,
                width=self.width,
                height=self.height
            )
            self.frame.pack_propagate(False)
            
            # Title label
            self.title_label = tk.Label(
                self.frame,
                text=self.title,
                font=('Arial', 9, 'bold'),
                bg='#3c3c3c',
                fg='#ffffff',
                anchor='w'
            )
            self.title_label.pack(fill='x', padx=5, pady=(5, 0))
            
            # Value label
            self.value_label = tk.Label(
                self.frame,
                text=str(initial_value),
                font=('Arial', 12, 'bold'),
                bg='#3c3c3c',
                fg='#4CAF50',
                anchor='w'
            )
            self.value_label.pack(fill='x', padx=5, pady=(0, 5))
            
        except Exception as e:
            print(f"❌ Error creating metric card '{self.title}': {e}")
            self._destroyed = True
    
    def _is_widget_valid(self) -> bool:
        """Check if widget is still valid and not destroyed"""
        if self._destroyed:
            return False
            
        try:
            # Test if the value label still exists and is valid
            if hasattr(self, 'value_label') and self.value_label:
                # Try to access a property - this will raise TclError if destroyed
                _ = self.value_label.winfo_exists()
                return True
            return False
        except tk.TclError:
            # Widget has been destroyed
            self._destroyed = True
            return False
        except Exception:
            return False
    
    def update_value(self, value, trend='neutral', color=None):
        """Safely update the metric card value with widget validation"""
        try:
            # Check widget validity first
            if not self._is_widget_valid():
                print(f"⚠️ Metric card '{self.title}' is invalid, skipping update to '{value}'")
                return False
            
            # Update the value safely
            self.value_label.config(text=str(value))
            
            # Update color based on trend if no specific color provided
            if not color:
                color = self._get_trend_color(trend)
            
            if color:
                self.value_label.config(fg=color)
                
            return True
            
        except tk.TclError as e:
            print(f"⚠️ Widget destroyed during update for '{self.title}': {e}")
            self._destroyed = True
            return False
        except Exception as e:
            print(f"❌ Error updating metric card '{self.title}': {e}")
            return False
    
    def _get_trend_color(self, trend):
        """Get color based on trend"""
        trend_colors = {
            'up': '#4CAF50',      # Green
            'down': '#F44336',    # Red
            'neutral': '#2196F3', # Blue
            'warning': '#FF9800'  # Orange
        }
        return trend_colors.get(trend, '#ffffff')
    
    def update_title(self, new_title):
        """Safely update the title"""
        try:
            if not self._is_widget_valid():
                return False
                
            if hasattr(self, 'title_label') and self.title_label:
                self.title_label.config(text=new_title)
                self.title = new_title
                return True
            return False
        except tk.TclError:
            self._destroyed = True
            return False
        except Exception as e:
            print(f"❌ Error updating title for '{self.title}': {e}")
            return False
    
    def pack(self, **kwargs):
        """Safely pack the widget"""
        try:
            if self._is_widget_valid() and hasattr(self, 'frame'):
                self.frame.pack(**kwargs)
                return True
            return False
        except Exception as e:
            print(f"❌ Error packing metric card '{self.title}': {e}")
            return False
    
    def grid(self, **kwargs):
        """Safely grid the widget"""
        try:
            if self._is_widget_valid() and hasattr(self, 'frame'):
                self.frame.grid(**kwargs)
                return True
            return False
        except Exception as e:
            print(f"❌ Error gridding metric card '{self.title}': {e}")
            return False
    
    def destroy(self):
        """Safely destroy the widget"""
        try:
            self._destroyed = True
            
            if hasattr(self, 'frame') and self.frame:
                self.frame.destroy()
                
        except Exception as e:
            print(f"⚠️ Error destroying metric card '{self.title}': {e}")
    
    def is_valid(self):
        """Public method to check if widget is valid"""
        return self._is_widget_valid()


# Quick fix for main_window.py event callbacks
def safe_update_metric_card(metric_card, value, trend='neutral'):
    """Safely update a metric card with validation"""
    try:
        if hasattr(metric_card, 'is_valid') and metric_card.is_valid():
            return metric_card.update_value(value, trend)
        elif hasattr(metric_card, 'update_value'):
            # Fallback for existing metric cards without safety checks
            try:
                metric_card.update_value(value, trend)
                return True
            except tk.TclError:
                print(f"⚠️ Metric card widget destroyed, skipping update to '{value}'")
                return False
        else:
            print(f"⚠️ Invalid metric card object, skipping update")
            return False
    except Exception as e:
        print(f"❌ Error in safe metric card update: {e}")
        return False


# Integration function for main_window.py
def patch_main_window_callbacks(main_window):
    """Patch main window callbacks to be widget-safe"""
    
    original_hide_loading = getattr(main_window, '_hide_loading', None)
    original_update_ui = getattr(main_window, '_update_ui', None)
    
    def safe_hide_loading(event):
        """Safe hide loading with widget validation"""
        try:
            # Extract data with safe defaults
            data = event.data
            metadata = data.get('metadata', {})
            cache_hit = metadata.get('cache_hit', False)
            
            # Create status text
            status_text = "📁 Cached" if cache_hit else "🌐 Live"
            
            # Safely update cache status if it exists
            if (hasattr(main_window, 'metric_cards') and 
                'cache_status' in main_window.metric_cards):
                cache_card = main_window.metric_cards['cache_status']
                safe_update_metric_card(cache_card, status_text, 'up' if cache_hit else 'neutral')
            
            # Call original hide loading if it exists
            if original_hide_loading:
                try:
                    original_hide_loading(event)
                except tk.TclError:
                    print("⚠️ Original hide_loading failed due to widget destruction")
            
        except Exception as e:
            print(f"❌ Error in safe_hide_loading: {e}")
    
    def safe_update_ui(event):
        """Safe update UI with widget validation"""
        try:
            # Extract data with safe defaults
            data = event.data
            stock_data = data.get('stock_data')
            
            if not stock_data:
                print("⚠️ No stock data in event, skipping UI update")
                return
            
            # Safely update metric cards
            if hasattr(main_window, 'metric_cards'):
                # Update price card
                if 'price' in main_window.metric_cards:
                    price_card = main_window.metric_cards['price']
                    safe_update_metric_card(price_card, "N/A (Fundamental)", 'neutral')
                
                # Update company name
                if 'company' in main_window.metric_cards:
                    company_card = main_window.metric_cards['company']
                    safe_update_metric_card(company_card, stock_data.company_name, 'neutral')
                
                # Update ticker
                if 'ticker' in main_window.metric_cards:
                    ticker_card = main_window.metric_cards['ticker']
                    safe_update_metric_card(ticker_card, stock_data.ticker, 'neutral')
                
                # Update quarters count
                quarters_count = len(stock_data.quarterly_financials)
                if 'quarters' in main_window.metric_cards:
                    quarters_card = main_window.metric_cards['quarters']
                    trend = 'up' if quarters_count > 8 else 'neutral'
                    safe_update_metric_card(quarters_card, f"{quarters_count} qtrs", trend)
            
            # Call original update UI if it exists
            if original_update_ui:
                try:
                    original_update_ui(event)
                except tk.TclError:
                    print("⚠️ Original update_ui failed due to widget destruction")
            
        except Exception as e:
            print(f"❌ Error in safe_update_ui: {e}")
    
    # Replace the callbacks with safe versions
    main_window._hide_loading = safe_hide_loading
    main_window._update_ui = safe_update_ui
    
    print("🛡️ Main window callbacks patched for widget safety")


if __name__ == "__main__":
    # Test the safe metric card
    print("🧪 Testing Safe Metric Card...")
    
    import tkinter as tk
    root = tk.Tk()
    root.title("Safe Metric Card Test")
    
    # Create test metric card
    card = MetricCard(root, "Test Card", "Initial Value")
    card.pack(padx=10, pady=10)
    
    # Test updates
    def test_updates():
        print("Testing safe updates...")
        card.update_value("Test 1", 'up')
        card.update_value("Test 2", 'down')
        card.update_value("Test 3", 'neutral')
        
        # Test after destruction
        card.destroy()
        card.update_value("Should be safe", 'up')  # Should not crash
    
    root.after(1000, test_updates)
    root.after(3000, root.quit)
    
    root.mainloop()
    print("✅ Safe Metric Card test completed")