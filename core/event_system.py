# core/event_system.py - Updated for new cache system

from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
import threading
import time


class EventType(Enum):
    """All event types in the application - Updated for cache system"""
    
    # Core data events
    DATA_RECEIVED = "data_received"
    DATA_FETCH_STARTED = "data_fetch_started"
    DATA_FETCH_COMPLETED = "data_fetch_completed"
    STOCK_SELECTED = "stock_selected"
    
    # Cache system events (NEW)
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    CACHE_UPDATED = "cache_updated"
    CACHE_LOADING_STARTED = "cache_loading_started"
    CACHE_LOADING_COMPLETED = "cache_loading_completed"
    BACKGROUND_CACHE_STARTED = "background_cache_started"
    BACKGROUND_CACHE_COMPLETED = "background_cache_completed"
    BACKGROUND_CACHE_PROGRESS = "background_cache_progress"
    TICKER_ADDED_TO_CACHE = "ticker_added_to_cache"
    NEW_FILING_DETECTED = "new_filing_detected"
    CACHE_CLEANUP_STARTED = "cache_cleanup_started"
    CACHE_CLEANUP_COMPLETED = "cache_cleanup_completed"
    
    # UI and navigation events
    TAB_CHANGED = "tab_changed"
    LOADING_STARTED = "loading_started"
    LOADING_COMPLETED = "loading_completed"
    ERROR_OCCURRED = "error_occurred"
    
    # Analysis events
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_PROGRESS = "analysis_progress"
    CALCULATION_STARTED = "calculation_started"
    CALCULATION_COMPLETED = "calculation_completed"
    
    # Chart events
    CHART_READY = "chart_ready"
    CHART_UPDATED = "chart_updated"
    CHART_CREATED = "chart_created"
    TIMEFRAME_CHANGED = "timeframe_changed"
    CHART_MODE_CHANGED = "chart_mode_changed"
    
    # User interaction events
    USER_INPUT_RECEIVED = "user_input_received"
    TICKER_VALIDATED = "ticker_validated"
    TICKER_INVALID = "ticker_invalid"
    
    # System events
    APP_INITIALIZED = "app_initialized"
    COMPONENT_READY = "component_ready"
    CLEANUP_REQUESTED = "cleanup_requested"
    
    # Status and progress events
    STATUS_UPDATED = "status_updated"
    PROGRESS_UPDATED = "progress_updated"
    MESSAGE_DISPLAYED = "message_displayed"
    
    # Network and API events (simplified for EdgarTools)
    API_REQUEST_STARTED = "api_request_started"
    API_REQUEST_COMPLETED = "api_request_completed"
    API_REQUEST_FAILED = "api_request_failed"
    NETWORK_ERROR = "network_error"
    
    # File and data events
    FILE_LOADED = "file_loaded"
    FILE_SAVED = "file_saved"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    
    # EdgarTools-specific events
    EDGARTOOLS_REQUEST_STARTED = "edgartools_request_started"
    EDGARTOOLS_REQUEST_COMPLETED = "edgartools_request_completed"
    EDGARTOOLS_REQUEST_FAILED = "edgartools_request_failed"
    EDGAR_FILING_FOUND = "edgar_filing_found"
    EDGAR_FILING_NOT_FOUND = "edgar_filing_not_found"
    FINANCIAL_DATA_EXTRACTED = "financial_data_extracted"
    FINANCIAL_DATA_EXTRACTION_FAILED = "financial_data_extraction_failed"
    TICKER_RESOLVED = "ticker_resolved"
    TICKER_RESOLUTION_FAILED = "ticker_resolution_failed"
    SEC_IDENTITY_SET = "sec_identity_set"
    XBRL_DATA_PARSED = "xbrl_data_parsed"
    FINANCIAL_STATEMENTS_LOADED = "financial_statements_loaded"


@dataclass
class Event:
    """Event data structure"""
    type: EventType
    data: Dict[str, Any]
    timestamp: float = None
    source: Optional[str] = None  # Component that generated the event
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class EventBus:
    """Central event bus for application-wide communication"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = threading.Lock()
        self._event_history: List[Event] = []  # For debugging
        self._max_history = 100  # Keep last 100 events
        
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to events of a specific type"""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(callback)
            
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe from events"""
        with self._lock:
            if event_type in self._subscribers:
                try:
                    self._subscribers[event_type].remove(callback)
                except ValueError:
                    pass  # Callback not found
                    
    def publish(self, event: Event):
        """Publish an event to all subscribers"""
        # Add to history for debugging
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            subscribers = self._subscribers.get(event.type, []).copy()
            
        # Call subscribers outside of lock to prevent deadlock
        for callback in subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event callback for {event.type}: {e}")
                import traceback
                traceback.print_exc()
                
    def publish_async(self, event: Event):
        """Publish an event asynchronously"""
        threading.Thread(target=self.publish, args=(event,), daemon=True).start()
        
    def has_subscribers(self, event_type: EventType) -> bool:
        """Check if there are subscribers for an event type"""
        with self._lock:
            return event_type in self._subscribers and len(self._subscribers[event_type]) > 0
            
    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get number of subscribers for an event type"""
        with self._lock:
            return len(self._subscribers.get(event_type, []))
            
    def clear_subscribers(self, event_type: EventType = None):
        """Clear subscribers for a specific event type or all"""
        with self._lock:
            if event_type:
                self._subscribers.pop(event_type, None)
            else:
                self._subscribers.clear()
                
    def get_recent_events(self, event_type: EventType = None, limit: int = 10) -> List[Event]:
        """Get recent events for debugging"""
        with self._lock:
            if event_type:
                filtered = [e for e in self._event_history if e.type == event_type]
                return filtered[-limit:]
            return self._event_history[-limit:]
            
    def debug_info(self) -> Dict[str, Any]:
        """Get debug information about the event bus"""
        with self._lock:
            return {
                'total_event_types': len(self._subscribers),
                'total_subscribers': sum(len(subs) for subs in self._subscribers.values()),
                'recent_event_count': len(self._event_history),
                'subscriber_breakdown': {
                    event_type.value: len(subs) 
                    for event_type, subs in self._subscribers.items()
                }
            }


# Utility functions for common event patterns
def create_data_event(event_type: EventType, data: Dict[str, Any], source: str = None) -> Event:
    """Helper to create data-related events"""
    return Event(type=event_type, data=data, source=source)


def create_error_event(error_message: str, source: str = None, **extra_data) -> Event:
    """Helper to create error events"""
    data = {'error': error_message, **extra_data}
    return Event(type=EventType.ERROR_OCCURRED, data=data, source=source)


def create_loading_event(is_loading: bool, message: str = "", source: str = None) -> Event:
    """Helper to create loading events"""
    event_type = EventType.LOADING_STARTED if is_loading else EventType.LOADING_COMPLETED
    data = {'message': message, 'loading': is_loading}
    return Event(type=event_type, data=data, source=source)


def create_chart_event(event_type: EventType, ticker: str = None, **extra_data) -> Event:
    """Helper to create chart-related events"""
    data = {'ticker': ticker, **extra_data}
    return Event(type=event_type, data=data, source='chart_manager')


# Cache system event helpers (NEW)
def create_cache_event(event_type: EventType, ticker: str = None, **extra_data) -> Event:
    """Helper to create cache-related events"""
    data = {'ticker': ticker, **extra_data}
    return Event(type=event_type, data=data, source='cache_manager')


def create_cache_hit_event(ticker: str, quarters_loaded: int, source: str = 'cache_manager') -> Event:
    """Helper to create cache hit events"""
    data = {
        'ticker': ticker,
        'quarters_loaded': quarters_loaded,
        'cache_hit': True
    }
    return Event(type=EventType.CACHE_HIT, data=data, source=source)


def create_cache_miss_event(ticker: str, reason: str = None, source: str = 'cache_manager') -> Event:
    """Helper to create cache miss events"""
    data = {
        'ticker': ticker,
        'cache_hit': False,
        'reason': reason
    }
    return Event(type=EventType.CACHE_MISS, data=data, source=source)


def create_cache_update_event(ticker: str, new_quarters: int = 0, total_quarters: int = 0, 
                             source: str = 'cache_manager') -> Event:
    """Helper to create cache update events"""
    data = {
        'ticker': ticker,
        'new_quarters': new_quarters,
        'total_quarters': total_quarters,
        'updated': True
    }
    return Event(type=EventType.CACHE_UPDATED, data=data, source=source)


def create_background_cache_event(event_type: EventType, tickers_processed: int = 0, 
                                 total_tickers: int = 0, current_ticker: str = None,
                                 source: str = 'cache_manager') -> Event:
    """Helper to create background cache events"""
    data = {
        'tickers_processed': tickers_processed,
        'total_tickers': total_tickers,
        'current_ticker': current_ticker,
        'progress_percent': (tickers_processed / total_tickers * 100) if total_tickers > 0 else 0
    }
    return Event(type=event_type, data=data, source=source)


def create_new_filing_event(ticker: str, filing_date: str, quarter: str, year: int,
                           source: str = 'cache_manager') -> Event:
    """Helper to create new filing detected events"""
    data = {
        'ticker': ticker,
        'filing_date': filing_date,
        'quarter': quarter,
        'year': year,
        'new_filing': True
    }
    return Event(type=EventType.NEW_FILING_DETECTED, data=data, source=source)


# EdgarTools-specific event helpers
def create_edgartools_event(event_type: EventType, ticker: str = None, **extra_data) -> Event:
    """Helper to create EdgarTools-specific events"""
    data = {'ticker': ticker, **extra_data}
    return Event(type=event_type, data=data, source='edgartools_provider')


def create_edgar_filing_event(ticker: str, filing_type: str = None, filing_data=None, **extra_data) -> Event:
    """Helper to create SEC filing-related events"""
    data = {
        'ticker': ticker,
        'filing_type': filing_type,
        'filing_data': filing_data,
        **extra_data
    }
    return Event(type=EventType.EDGAR_FILING_FOUND, data=data, source='edgartools_provider')


def create_financial_extraction_event(ticker: str, extraction_success: bool, 
                                     revenue_data=None, fcf_data=None, **extra_data) -> Event:
    """Helper to create financial data extraction events"""
    event_type = EventType.FINANCIAL_DATA_EXTRACTED if extraction_success else EventType.FINANCIAL_DATA_EXTRACTION_FAILED
    data = {
        'ticker': ticker,
        'success': extraction_success,
        'revenue_data': revenue_data,
        'fcf_data': fcf_data,
        **extra_data
    }
    return Event(type=event_type, data=data, source='edgartools_provider')


def create_ticker_resolution_event(ticker: str, success: bool, company_name: str = None, **extra_data) -> Event:
    """Helper to create ticker resolution events"""
    event_type = EventType.TICKER_RESOLVED if success else EventType.TICKER_RESOLUTION_FAILED
    data = {
        'ticker': ticker,
        'success': success,
        'company_name': company_name,
        **extra_data
    }
    return Event(type=event_type, data=data, source='edgartools_provider')


def create_sec_identity_event(identity: str, success: bool, **extra_data) -> Event:
    """Helper to create SEC identity setup events"""
    data = {
        'identity': identity,
        'success': success,
        **extra_data
    }
    return Event(type=EventType.SEC_IDENTITY_SET, data=data, source='edgartools_provider')


# Event bus singleton for global access
_global_event_bus = None

def get_global_event_bus() -> EventBus:
    """Get the global event bus instance"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


def reset_global_event_bus():
    """Reset the global event bus (useful for testing)"""
    global _global_event_bus
    _global_event_bus = None


# Cache system event monitoring (NEW)
class CacheEventMonitor:
    """Monitor cache-related events for debugging and performance tracking"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.cache_events = []
        self.cache_stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_updates': 0,
            'background_updates': 0,
            'new_filings_detected': 0
        }
        
        # Subscribe to all cache events
        cache_event_types = [
            EventType.CACHE_HIT,
            EventType.CACHE_MISS,
            EventType.CACHE_UPDATED,
            EventType.BACKGROUND_CACHE_STARTED,
            EventType.BACKGROUND_CACHE_COMPLETED,
            EventType.BACKGROUND_CACHE_PROGRESS,
            EventType.TICKER_ADDED_TO_CACHE,
            EventType.NEW_FILING_DETECTED,
            EventType.CACHE_CLEANUP_STARTED,
            EventType.CACHE_CLEANUP_COMPLETED
        ]
        
        for event_type in cache_event_types:
            self.event_bus.subscribe(event_type, self._on_cache_event)
    
    def _on_cache_event(self, event: Event):
        """Handle cache events"""
        self.cache_events.append(event)
        # Keep only last 100 events
        if len(self.cache_events) > 100:
            self.cache_events.pop(0)
        
        # Update stats
        if event.type == EventType.CACHE_HIT:
            self.cache_stats['cache_hits'] += 1
        elif event.type == EventType.CACHE_MISS:
            self.cache_stats['cache_misses'] += 1
        elif event.type == EventType.CACHE_UPDATED:
            self.cache_stats['cache_updates'] += 1
        elif event.type == EventType.BACKGROUND_CACHE_COMPLETED:
            self.cache_stats['background_updates'] += 1
        elif event.type == EventType.NEW_FILING_DETECTED:
            self.cache_stats['new_filings_detected'] += 1
        
        # Debug logging for important events
        if event.type in [EventType.CACHE_HIT, EventType.CACHE_MISS, EventType.NEW_FILING_DETECTED]:
            ticker = event.data.get('ticker', 'N/A')
            print(f"🔍 Cache Event: {event.type.value} - {ticker}")
    
    def get_cache_performance_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['cache_hits'] + self.cache_stats['cache_misses']
        hit_rate = (self.cache_stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            'hit_rate_percent': round(hit_rate, 1),
            'total_requests': total_requests
        }
    
    def get_recent_cache_events(self, limit: int = 10) -> List[Event]:
        """Get recent cache events"""
        return self.cache_events[-limit:]
    
    def get_ticker_cache_history(self, ticker: str) -> List[Event]:
        """Get cache event history for a specific ticker"""
        return [e for e in self.cache_events if e.data.get('ticker') == ticker]


# Enhanced EdgarTools event monitoring
class EdgarToolsEventMonitor:
    """Monitor EdgarTools-specific events for debugging"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.edgar_events = []
        
        # Subscribe to all EdgarTools events
        edgar_event_types = [
            EventType.EDGARTOOLS_REQUEST_STARTED,
            EventType.EDGARTOOLS_REQUEST_COMPLETED,
            EventType.EDGARTOOLS_REQUEST_FAILED,
            EventType.EDGAR_FILING_FOUND,
            EventType.EDGAR_FILING_NOT_FOUND,
            EventType.FINANCIAL_DATA_EXTRACTED,
            EventType.FINANCIAL_DATA_EXTRACTION_FAILED,
            EventType.TICKER_RESOLVED,
            EventType.TICKER_RESOLUTION_FAILED,
            EventType.SEC_IDENTITY_SET,
            EventType.XBRL_DATA_PARSED,
            EventType.FINANCIAL_STATEMENTS_LOADED
        ]
        
        for event_type in edgar_event_types:
            self.event_bus.subscribe(event_type, self._on_edgar_event)
    
    def _on_edgar_event(self, event: Event):
        """Handle EdgarTools events"""
        self.edgar_events.append(event)
        # Keep only last 50 events
        if len(self.edgar_events) > 50:
            self.edgar_events.pop(0)
        
        # Debug logging
        print(f"🔍 EdgarTools Event: {event.type.value} - {event.data.get('ticker', 'N/A')}")
    
    def get_recent_edgar_events(self, limit: int = 10) -> List[Event]:
        """Get recent EdgarTools events"""
        return self.edgar_events[-limit:]
    
    def get_ticker_event_history(self, ticker: str) -> List[Event]:
        """Get event history for a specific ticker"""
        return [e for e in self.edgar_events if e.data.get('ticker') == ticker]


# Helper to set up monitoring
def setup_cache_event_monitoring(event_bus: EventBus = None) -> CacheEventMonitor:
    """Set up cache event monitoring"""
    if event_bus is None:
        event_bus = get_global_event_bus()
    return CacheEventMonitor(event_bus)


def setup_edgar_event_monitoring(event_bus: EventBus = None) -> EdgarToolsEventMonitor:
    """Set up EdgarTools event monitoring"""
    if event_bus is None:
        event_bus = get_global_event_bus()
    return EdgarToolsEventMonitor(event_bus)


def setup_comprehensive_monitoring(event_bus: EventBus = None) -> Tuple[CacheEventMonitor, EdgarToolsEventMonitor]:
    """Set up both cache and EdgarTools event monitoring"""
    if event_bus is None:
        event_bus = get_global_event_bus()
    
    cache_monitor = CacheEventMonitor(event_bus)
    edgar_monitor = EdgarToolsEventMonitor(event_bus)
    
    return cache_monitor, edgar_monitor


if __name__ == "__main__":
    # Test the enhanced event system
    print("🧪 Testing Enhanced Event System with Cache Support")
    print("=" * 50)
    
    # Create event bus
    event_bus = EventBus()
    
    # Set up comprehensive monitoring
    cache_monitor, edgar_monitor = setup_comprehensive_monitoring(event_bus)
    
    # Test basic events
    def test_subscriber(event):
        print(f"📧 Received: {event.type.value}")
    
    # Subscribe to data and cache events
    event_bus.subscribe(EventType.DATA_RECEIVED, test_subscriber)
    event_bus.subscribe(EventType.CACHE_HIT, test_subscriber)
    event_bus.subscribe(EventType.CACHE_MISS, test_subscriber)
    
    # Test cache events
    cache_hit_event = create_cache_hit_event('AAPL', 12)
    event_bus.publish(cache_hit_event)
    
    cache_miss_event = create_cache_miss_event('MSFT', 'No cached data found')
    event_bus.publish(cache_miss_event)
    
    cache_update_event = create_cache_update_event('AAPL', new_quarters=2, total_quarters=12)
    event_bus.publish(cache_update_event)
    
    new_filing_event = create_new_filing_event('AAPL', '2024-01-15', 'Q4', 2023)
    event_bus.publish(new_filing_event)
    
    # Test background cache events
    bg_start_event = create_background_cache_event(EventType.BACKGROUND_CACHE_STARTED, 0, 10)
    event_bus.publish(bg_start_event)
    
    bg_progress_event = create_background_cache_event(EventType.BACKGROUND_CACHE_PROGRESS, 5, 10, 'MSFT')
    event_bus.publish(bg_progress_event)
    
    bg_complete_event = create_background_cache_event(EventType.BACKGROUND_CACHE_COMPLETED, 10, 10)
    event_bus.publish(bg_complete_event)
    
    # Show cache performance stats
    cache_stats = cache_monitor.get_cache_performance_stats()
    print(f"\n📊 Cache Performance Stats:")
    for key, value in cache_stats.items():
        print(f"   {key}: {value}")
    
    # Show debug info
    debug_info = event_bus.debug_info()
    print(f"\n📊 Event Bus Status:")
    print(f"   Event Types: {debug_info['total_event_types']}")
    print(f"   Subscribers: {debug_info['total_subscribers']}")
    print(f"   Recent Events: {debug_info['recent_event_count']}")
    
    print("\n✅ Enhanced event system test completed")