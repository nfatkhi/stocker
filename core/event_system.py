# core/event_system.py - Updated with Live Price Events and Enhanced Features
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import threading
import time


class EventType(Enum):
    """All event types in the application"""
    
    # Core data events
    DATA_RECEIVED = "data_received"
    DATA_FETCH_STARTED = "data_fetch_started"
    DATA_FETCH_COMPLETED = "data_fetch_completed"
    STOCK_SELECTED = "stock_selected"
    
    # UI and navigation events
    TAB_CHANGED = "tab_changed"
    LOADING_STARTED = "loading_started"
    LOADING_COMPLETED = "loading_completed"
    ERROR_OCCURRED = "error_occurred"
    
    # Analysis events (for status bar compatibility)
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_COMPLETED = "analysis_completed"
    ANALYSIS_PROGRESS = "analysis_progress"
    CALCULATION_STARTED = "calculation_started"
    CALCULATION_COMPLETED = "calculation_completed"
    
    # Live price events (NEW)
    LIVE_PRICE_UPDATED = "live_price_updated"
    PRICE_UPDATED = "price_updated"  # Generic price update (for backward compatibility)
    PRICE_ALERT_TRIGGERED = "price_alert_triggered"
    
    # Chart events (NEW)
    CHART_READY = "chart_ready"
    CHART_UPDATED = "chart_updated"
    CHART_CREATED = "chart_created"
    TIMEFRAME_CHANGED = "timeframe_changed"
    CHART_MODE_CHANGED = "chart_mode_changed"  # For daily/hourly mode switches
    
    # Market events (NEW)
    MARKET_STATUS_CHANGED = "market_status_changed"
    TRADING_SESSION_STARTED = "trading_session_started"
    TRADING_SESSION_ENDED = "trading_session_ended"
    MARKET_HOURS_DETECTED = "market_hours_detected"
    
    # User interaction events (NEW)
    USER_INPUT_RECEIVED = "user_input_received"
    TICKER_VALIDATED = "ticker_validated"
    TICKER_INVALID = "ticker_invalid"
    
    # System events (NEW)
    APP_INITIALIZED = "app_initialized"
    COMPONENT_READY = "component_ready"
    CLEANUP_REQUESTED = "cleanup_requested"
    
    # Status and progress events (for UI components)
    STATUS_UPDATED = "status_updated"
    PROGRESS_UPDATED = "progress_updated"
    MESSAGE_DISPLAYED = "message_displayed"
    
    # Network and API events
    API_REQUEST_STARTED = "api_request_started"
    API_REQUEST_COMPLETED = "api_request_completed"
    API_REQUEST_FAILED = "api_request_failed"
    NETWORK_ERROR = "network_error"
    
    # File and data events
    FILE_LOADED = "file_loaded"
    FILE_SAVED = "file_saved"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"


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


def create_live_price_event(ticker: str, live_data, source: str = 'live_price_indicator') -> Event:
    """Helper to create live price events"""
    data = {'ticker': ticker, 'live_data': live_data}
    return Event(type=EventType.LIVE_PRICE_UPDATED, data=data, source=source)


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