# components/charts/universal_chart_manager.py - FIXED VISIBILITY VERSION

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional, Tuple, Callable, Union
from enum import Enum

try:
    from config import UI_CONFIG
except ImportError:
    UI_CONFIG = {'font_family': 'Arial', 'font_size': 10}


class ChartType(Enum):
    """Types of financial charts"""
    MAIN_CHART = "main_chart"
    COMPARISON_CHART = "comparison_chart"
    SUBSIDIARY_CHART = "subsidiary_chart"
    SUMMARY_CARDS = "summary_cards"
    INFO_PANEL = "info_panel"
    CUSTOM = "custom"


class LayoutTemplate(Enum):
    """Pre-defined layout templates"""
    SINGLE_CHART = "single"
    MAIN_PLUS_ANALYSIS = "main_analysis"
    COMPREHENSIVE = "comprehensive"
    COMPARISON_FOCUSED = "comparison"
    CUSTOM = "custom"


class ChartRegion:
    """Represents a chart region with configurable properties"""
    
    def __init__(self, name: str, chart_type: ChartType, 
                 height_ratio: float = 0.33, min_height: int = 200,
                 is_collapsible: bool = False, default_visible: bool = True):
        self.name = name
        self.chart_type = chart_type
        self.height_ratio = height_ratio
        self.min_height = min_height
        self.is_collapsible = is_collapsible
        self.is_visible = default_visible
        
        # UI elements
        self.frame = None
        self.content_frame = None
        self.header_frame = None
        self.collapse_button = None
        self.title_label = None
        
        # Content management
        self.chart_widget = None
        self.custom_widgets = []


class UniversalChartManager:
    """FIXED Universal chart layout manager with guaranteed visibility"""
    
    def __init__(self, parent_container: tk.Widget, 
                 layout_template: LayoutTemplate = LayoutTemplate.MAIN_PLUS_ANALYSIS,
                 tab_title: str = "Financial Analysis"):
        
        self.parent_container = parent_container
        self.layout_template = layout_template
        self.tab_title = tab_title
        
        # Chart regions storage
        self.regions: Dict[str, ChartRegion] = {}
        self.main_container = None
        self.header_frame = None
        
        # Styling
        self.colors = {
            'bg': '#2b2b2b',
            'frame': '#3c3c3c',
            'text': '#ffffff',
            'header': '#4CAF50',
            'accent': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'border': '#555555',
            'collapse_button': '#666666'
        }
        
        # State management
        self.is_initialized = False
        self.current_ticker = ""
        self.data_sources = {}
        
        # Initialize layout
        self._setup_layout()
        print(f"📐 FIXED Universal Chart Manager initialized - Template: {layout_template.value}")
    
    def _setup_layout(self):
        """FIXED Initialize the main layout structure - NO SCROLLING ISSUES"""
        # Clear existing content
        for widget in self.parent_container.winfo_children():
            widget.destroy()
        
        # FIXED: Create simple main container WITHOUT complex scrolling
        self.main_container = tk.Frame(self.parent_container, bg=self.colors['bg'])
        self.main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create header section
        self._create_header_section()
        
        # Setup regions based on template
        self._setup_layout_template()
        
        # FORCE geometry update
        self.main_container.update_idletasks()
        self.parent_container.update_idletasks()
        
        self.is_initialized = True
        print("✅ FIXED: Simple layout created without scrolling complexity")
    
    def _create_header_section(self):
        """Create header with title and controls"""
        self.header_frame = tk.Frame(self.main_container, bg=self.colors['bg'])
        self.header_frame.pack(fill='x', pady=(0, 10))
        
        # Main title
        title_label = tk.Label(
            self.header_frame,
            text=self.tab_title,
            font=(UI_CONFIG['font_family'], 16, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['header']
        )
        title_label.pack(side='left')
        
        # Data source indicators
        self.data_source_frame = tk.Frame(self.header_frame, bg=self.colors['bg'])
        self.data_source_frame.pack(side='right')
    
    def _setup_layout_template(self):
        """Setup regions based on selected template"""
        if self.layout_template == LayoutTemplate.MAIN_PLUS_ANALYSIS:
            self._create_main_plus_analysis_template()
        else:
            # Default to main plus analysis
            self._create_main_plus_analysis_template()
    
    def _create_main_plus_analysis_template(self):
        """FIXED Template: Summary + Main Chart + QoQ Analysis"""
        self.regions = {
            'summary': ChartRegion('summary', ChartType.SUMMARY_CARDS, height_ratio=0.15, min_height=100),
            'main_chart': ChartRegion('main_chart', ChartType.MAIN_CHART, height_ratio=0.5, min_height=300),
            'analysis_chart': ChartRegion('analysis_chart', ChartType.COMPARISON_CHART, height_ratio=0.35, min_height=250, is_collapsible=True)
        }
        self._create_region_frames()
    
    def _create_region_frames(self):
        """FIXED Create UI frames for all defined regions with guaranteed visibility"""
        for region_name, region in self.regions.items():
            if not region.is_visible:
                continue
            
            print(f"🔧 FIXED: Creating region {region_name}")
            
            # FIXED: Create main region frame with explicit height
            region.frame = tk.Frame(
                self.main_container,
                bg=self.colors['frame'],
                relief='solid',
                bd=2,
                height=region.min_height  # EXPLICIT HEIGHT
            )
            
            # Create content frame
            region.content_frame = tk.Frame(region.frame, bg=self.colors['bg'])
            
            # FIXED: Pack region frame with explicit sizing
            if region.chart_type == ChartType.SUMMARY_CARDS:
                # Summary cards - fixed height
                region.frame.pack(fill='x', pady=(0, 10))
                region.frame.pack_propagate(False)  # MAINTAIN EXPLICIT HEIGHT
                region.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
            else:
                # Chart regions - expandable
                region.frame.pack(fill='both', expand=True, pady=(0, 10))
                region.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Add collapse button if needed
            if region.is_collapsible:
                self._add_collapse_button(region)
            
            # FORCE geometry update
            region.frame.update_idletasks()
            region.content_frame.update_idletasks()
            
            print(f"✅ FIXED: Created region: {region_name} (height: {region.min_height}px)")
    
    def _add_collapse_button(self, region: ChartRegion):
        """Add collapse/expand button to a region"""
        if not region.header_frame:
            region.header_frame = tk.Frame(region.frame, bg=self.colors['frame'])
            region.header_frame.pack(fill='x', pady=(2, 0))
        
        def toggle_collapse():
            if region.content_frame.winfo_viewable():
                region.content_frame.pack_forget()
                region.collapse_button.config(text="▶")
                print(f"🔧 Collapsed {region.name}")
            else:
                region.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
                region.collapse_button.config(text="▼")
                print(f"🔧 Expanded {region.name}")
        
        region.collapse_button = tk.Button(
            region.header_frame,
            text="▼",
            command=toggle_collapse,
            font=(UI_CONFIG['font_family'], 8),
            bg=self.colors['collapse_button'],
            fg=self.colors['text'],
            relief='flat',
            width=3
        )
        region.collapse_button.pack(side='right', padx=5, pady=2)
    
    # ===== PUBLIC API METHODS =====
    
    def set_tab_info(self, ticker: str, data_sources: Dict[str, str] = None):
        """Set tab information"""
        self.current_ticker = ticker
        self.data_sources = data_sources or {}
        
        # Update header title
        if hasattr(self, 'header_frame'):
            for widget in self.header_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(text=f"{ticker} - {self.tab_title}")
                    break
        
        # Update data source indicators
        self._update_data_source_indicators()
    
    def _update_data_source_indicators(self):
        """Update data source indicators in header"""
        # Clear existing indicators
        for widget in self.data_source_frame.winfo_children():
            widget.destroy()
        
        # Add new indicators
        for source_type, source_name in self.data_sources.items():
            indicator = tk.Label(
                self.data_source_frame,
                text=f"📊 {source_type}: {source_name}",
                font=(UI_CONFIG['font_family'], 9),
                bg=self.colors['bg'],
                fg=self.colors['accent']
            )
            indicator.pack(side='right', padx=5)
    
    def get_region_frame(self, region_name: str) -> Optional[tk.Frame]:
        """Get content frame for a specific region"""
        region = self.regions.get(region_name)
        return region.content_frame if region else None
    
    def add_chart_to_region(self, region_name: str, chart_creator: Callable[[tk.Frame], Any], 
                           title: str = None, clear_existing: bool = True) -> bool:
        """FIXED Add a chart to a specific region with guaranteed visibility"""
        region = self.regions.get(region_name)
        if not region or not region.content_frame:
            print(f"❌ FIXED: Region {region_name} not found")
            return False
        
        try:
            print(f"🔧 FIXED: Adding chart to {region_name} region")
            
            # Clear existing content if requested
            if clear_existing:
                for widget in region.content_frame.winfo_children():
                    widget.destroy()
            
            # Add title if provided
            if title:
                self._add_region_title(region.content_frame, title)
            
            # Create chart using the provided function
            chart_widget = chart_creator(region.content_frame)
            region.chart_widget = chart_widget
            
            # FORCE immediate geometry updates
            region.content_frame.update_idletasks()
            region.frame.update_idletasks()
            self.main_container.update_idletasks()
            self.parent_container.update_idletasks()
            
            print(f"✅ FIXED: Added chart to {region_name} region with forced updates")
            return True
            
        except Exception as e:
            print(f"❌ FIXED: Error adding chart to {region_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _add_region_title(self, parent_frame: tk.Frame, title: str):
        """Add a title to a region"""
        title_label = tk.Label(
            parent_frame,
            text=title,
            font=(UI_CONFIG['font_family'], 12, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['header']
        )
        title_label.pack(pady=(0, 10))
    
    def add_summary_cards(self, metrics: List[Tuple[str, str, str]]) -> bool:
        """Add summary metric cards"""
        def create_summary_cards(parent_frame):
            print("🔧 FIXED: Creating summary cards...")
            cards_container = tk.Frame(parent_frame, bg=self.colors['bg'])
            cards_container.pack(fill='both', expand=True)
            
            for label, value, color in metrics:
                card_frame = tk.Frame(
                    cards_container,
                    bg=self.colors['frame'],
                    relief='raised',
                    bd=1
                )
                card_frame.pack(side='left', fill='both', expand=True, padx=5)
                
                # Label
                tk.Label(
                    card_frame,
                    text=label,
                    font=(UI_CONFIG['font_family'], 10),
                    bg=self.colors['frame'],
                    fg=self.colors['text']
                ).pack(pady=(10, 5))
                
                # Value
                tk.Label(
                    card_frame,
                    text=value,
                    font=(UI_CONFIG['font_family'], 12, 'bold'),
                    bg=self.colors['frame'],
                    fg=color
                ).pack(pady=(0, 10))
            
            print("✅ FIXED: Summary cards created")
            return cards_container
        
        return self.add_chart_to_region('summary', create_summary_cards)
    
    def show_error_in_region(self, region_name: str, error_message: str):
        """Show an error message in a specific region"""
        def create_error_display(parent_frame):
            error_label = tk.Label(
                parent_frame,
                text=f"❌ Error: {error_message}",
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['error'],
                justify='center',
                wraplength=400
            )
            error_label.pack(expand=True)
            return error_label
        
        self.add_chart_to_region(region_name, create_error_display)
    
    def show_no_data_message(self, region_name: str, message: str = None):
        """Show a no data message in a specific region"""
        default_message = f"No data available for {self.current_ticker}"
        display_message = message or default_message
        
        def create_no_data_display(parent_frame):
            no_data_label = tk.Label(
                parent_frame,
                text=f"📊 {display_message}",
                font=(UI_CONFIG['font_family'], 12),
                bg=self.colors['bg'],
                fg=self.colors['warning'],
                justify='center',
                wraplength=400
            )
            no_data_label.pack(expand=True)
            return no_data_label
        
        self.add_chart_to_region(region_name, create_no_data_display)
    
    def get_available_regions(self) -> List[str]:
        """Get list of available region names"""
        return list(self.regions.keys())


# ===== FIXED INTEGRATION HELPER =====

class FinancialChartIntegration:
    """FIXED Helper class with guaranteed visibility"""
    
    @staticmethod
    def integrate_fcf_chart(chart_manager: UniversalChartManager, fcf_chart_instance, financial_data: List[Any]) -> bool:
        """FIXED FCF chart integration with guaranteed visibility"""
        try:
            print("🔧 FIXED: Starting FCF integration with visibility fixes...")
            
            # Set tab info
            chart_manager.set_tab_info(
                fcf_chart_instance.ticker,
                {'FCF': 'Polygon.io', 'QoQ Analysis': 'Calculated'}
            )
            
            # Add summary cards (simplified)
            try:
                summary_metrics = [
                    ("Data Source", "Polygon.io", '#1976D2'),
                    ("Data Points", f"{len(financial_data)}", '#2196F3'),
                    ("Status", "DEBUG Active", '#4CAF50')
                ]
                chart_manager.add_summary_cards(summary_metrics)
                print("✅ FIXED: Summary cards added")
            except Exception as e:
                print(f"⚠️ FIXED: Summary cards failed: {e}")
            
            # Add main FCF chart (simplified test)
            def create_main_fcf_chart(parent_frame):
                print("🔧 FIXED: Creating main FCF chart content...")
                
                # Create a large, visible test chart
                chart_content = tk.Frame(parent_frame, bg='#1976D2', relief='raised', bd=3)
                chart_content.pack(fill='both', expand=True, padx=20, pady=20)
                
                main_label = tk.Label(
                    chart_content,
                    text=f"🎯 MAIN FCF CHART\n\nTicker: {fcf_chart_instance.ticker}\nData Points: {len(financial_data)}\n\nThis should be HIGHLY VISIBLE!",
                    font=(UI_CONFIG['font_family'], 14, 'bold'),
                    bg='#1976D2',
                    fg='white',
                    justify='center'
                )
                main_label.pack(expand=True, pady=50)
                
                print("✅ FIXED: Main chart content created")
                return chart_content
            
            main_success = chart_manager.add_chart_to_region(
                'main_chart', 
                create_main_fcf_chart, 
                'MAIN: Free Cash Flow (Polygon.io)'
            )
            
            # Add QoQ analysis chart (simplified test)
            def create_qoq_chart(parent_frame):
                print("🔧 FIXED: Creating QoQ chart content...")
                
                # Create a large, visible test chart
                qoq_content = tk.Frame(parent_frame, bg='#FF9800', relief='raised', bd=3)
                qoq_content.pack(fill='both', expand=True, padx=20, pady=20)
                
                qoq_label = tk.Label(
                    qoq_content,
                    text=f"📊 QoQ ANALYSIS CHART\n\nThis is the Quarter-over-Quarter analysis!\n\nShould be HIGHLY VISIBLE below main chart!",
                    font=(UI_CONFIG['font_family'], 14, 'bold'),
                    bg='#FF9800',
                    fg='white',
                    justify='center'
                )
                qoq_label.pack(expand=True, pady=50)
                
                print("✅ FIXED: QoQ chart content created")
                return qoq_content
            
            qoq_success = chart_manager.add_chart_to_region(
                'analysis_chart', 
                create_qoq_chart, 
                'QoQ: Quarter-over-Quarter Analysis'
            )
            
            if main_success and qoq_success:
                print("🎉 FIXED: Both charts added - should be HIGHLY VISIBLE!")
                return True
            else:
                print(f"⚠️ FIXED: Partial success - Main: {main_success}, QoQ: {qoq_success}")
                return main_success  # At least main chart should work
            
        except Exception as e:
            print(f"❌ FIXED: Integration error: {e}")
            import traceback
            traceback.print_exc()
            chart_manager.show_error_in_region('main_chart', str(e))
            return False


print("✅ FIXED Universal Chart Manager loaded - Guaranteed visibility!")