#!/usr/bin/env python3
# connectivity_test.py - Test component connectivity after fixes

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all component imports"""
    print("🧪 TESTING COMPONENT IMPORTS")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Core components
    try:
        from core.event_system import EventBus, Event, EventType
        print("✅ Core event system imports")
        results['event_system'] = True
    except Exception as e:
        print(f"❌ Event system import failed: {e}")
        results['event_system'] = False
    
    # Test 2: Cache system
    try:
        from components.cache_manager import CacheManager, MultiRowCacheManager
        from components.data_fetcher import XBRLDataFetcher, fetch_company_data
        from components.xbrl_extractor import extract_multi_row_financials
        print("✅ Cache system components imports")
        results['cache_system'] = True
    except Exception as e:
        print(f"❌ Cache system import failed: {e}")
        results['cache_system'] = False
    
    # Test 3: Chart components (FIXED)
    try:
        from components.charts.base_chart import FinancialBarChart
        print("✅ Base chart import")
        results['base_chart'] = True
    except Exception as e:
        print(f"❌ Base chart import failed: {e}")
        results['base_chart'] = False
    
    try:
        from components.charts.revenue.revenue_chart import RevenueTab, RevenueChart
        print("✅ Revenue chart import")
        results['revenue_chart'] = True
    except Exception as e:
        print(f"❌ Revenue chart import failed: {e}")
        results['revenue_chart'] = False
    
    try:
        from components.charts.revenue.revenue_data_processor import get_processed_revenue_data
        print("✅ Revenue data processor import")
        results['revenue_processor'] = True
    except Exception as e:
        print(f"❌ Revenue data processor import failed: {e}")
        results['revenue_processor'] = False
    
    # Test 4: Chart manager (FIXED)
    try:
        from components.chart_manager import EnhancedChartManager
        print("✅ Enhanced Chart Manager import")
        results['chart_manager'] = True
    except Exception as e:
        print(f"❌ Chart manager import failed: {e}")
        print(f"   Error details: {traceback.format_exc()}")
        results['chart_manager'] = False
    
    # Test 5: Main app components
    try:
        from core.app import StockerApp, CacheDataOrchestrator
        print("✅ Main app components import")
        results['main_app'] = True
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        results['main_app'] = False
    
    # Test 6: Config
    try:
        from config import APP_CONFIG, EDGARTOOLS_CONFIG, validate_config
        print("✅ Config imports")
        results['config'] = True
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        results['config'] = False
    
    return results

def test_component_initialization():
    """Test component initialization"""
    print("\n🧪 TESTING COMPONENT INITIALIZATION")
    print("=" * 50)
    
    results = {}
    
    # Test EventBus
    try:
        from core.event_system import EventBus
        event_bus = EventBus()
        print("✅ EventBus created")
        results['event_bus'] = True
    except Exception as e:
        print(f"❌ EventBus creation failed: {e}")
        results['event_bus'] = False
        return results
    
    # Test CacheManager
    try:
        from components.cache_manager import CacheManager
        cache_manager = CacheManager()
        print("✅ CacheManager created")
        results['cache_manager'] = True
    except Exception as e:
        print(f"❌ CacheManager creation failed: {e}")
        results['cache_manager'] = False
    
    # Test Chart Manager (FIXED)
    try:
        from components.chart_manager import EnhancedChartManager
        chart_manager = EnhancedChartManager(event_bus)
        print("✅ EnhancedChartManager created")
        results['enhanced_chart_manager'] = True
    except Exception as e:
        print(f"❌ EnhancedChartManager creation failed: {e}")
        print(f"   Error details: {traceback.format_exc()}")
        results['enhanced_chart_manager'] = False
    
    # Test Revenue components (FIXED)
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        
        from components.charts.revenue.revenue_chart import RevenueTab
        test_frame = tk.Frame(root)
        revenue_tab = RevenueTab(test_frame, "TEST")
        print("✅ RevenueTab created")
        results['revenue_tab'] = True
        
        root.destroy()
    except Exception as e:
        print(f"❌ RevenueTab creation failed: {e}")
        results['revenue_tab'] = False
    
    return results

def test_data_flow():
    """Test basic data flow"""
    print("\n🧪 TESTING DATA FLOW")
    print("=" * 50)
    
    results = {}
    
    # Test event publishing/subscribing
    try:
        from core.event_system import EventBus, Event, EventType
        
        event_bus = EventBus()
        received_events = []
        
        def test_handler(event):
            received_events.append(event)
        
        event_bus.subscribe(EventType.STOCK_SELECTED, test_handler)
        
        test_event = Event(
            type=EventType.STOCK_SELECTED,
            data={'ticker': 'TEST'},
            source='connectivity_test'
        )
        
        event_bus.publish(test_event)
        
        if len(received_events) == 1 and received_events[0].data['ticker'] == 'TEST':
            print("✅ Event system communication working")
            results['event_communication'] = True
        else:
            print("❌ Event system communication failed")
            results['event_communication'] = False
            
    except Exception as e:
        print(f"❌ Event system test failed: {e}")
        results['event_communication'] = False
    
    # Test data processor
    try:
        from components.charts.revenue.revenue_data_processor import get_processed_revenue_data
        
        # Mock cache data
        mock_cache_data = [{
            'ticker': 'TEST',
            'filing_date': '2025-04-27',
            'quarter': 'Q1',
            'year': 2025,
            'revenues': [
                {
                    'concept': 'us-gaap:Revenues',
                    'numeric_value': 1000000000.0,
                    'period_start': '2025-01-01',
                    'period_end': '2025-03-31',
                    'dimensions': None
                }
            ]
        }]
        
        processed = get_processed_revenue_data(mock_cache_data)
        
        if processed and len(processed) == 1 and processed[0].revenue > 0:
            print("✅ Revenue data processor working")
            results['data_processor'] = True
        else:
            print("❌ Revenue data processor failed")
            results['data_processor'] = False
            
    except Exception as e:
        print(f"❌ Data processor test failed: {e}")
        results['data_processor'] = False
    
    return results

def test_full_integration():
    """Test full integration"""
    print("\n🧪 TESTING FULL INTEGRATION")
    print("=" * 50)
    
    try:
        import tkinter as tk
        from core.event_system import EventBus, Event, EventType
        from components.chart_manager import EnhancedChartManager
        
        # Create test environment
        root = tk.Tk()
        root.withdraw()
        
        event_bus = EventBus()
        chart_manager = EnhancedChartManager(event_bus)
        
        test_frame = tk.Frame(root)
        chart_manager.set_container('Financials', test_frame)
        
        # Test stock selection event
        stock_event = Event(
            type=EventType.STOCK_SELECTED,
            data={'ticker': 'NVDA'},
            source='connectivity_test'
        )
        
        # This should trigger the full chain:
        # Event → Chart Manager → Cache Manager → Data Processor → Charts
        chart_manager.on_stock_selected(stock_event)
        
        print("✅ Full integration test completed without errors")
        
        # Get status
        status = chart_manager.get_data_status()
        print(f"✅ Chart manager status: {status['import_status']}")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Full integration test failed: {e}")
        print(f"   Error details: {traceback.format_exc()}")
        return False

def main():
    """Run all connectivity tests"""
    print("🚀 STOCKER APP CONNECTIVITY TEST")
    print("Testing component integration after FIXES")
    print("=" * 60)
    
    # Run tests
    import_results = test_imports()
    init_results = test_component_initialization()
    flow_results = test_data_flow()
    integration_result = test_full_integration()
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 40)
    
    all_results = {**import_results, **init_results, **flow_results}
    
    passed = sum(1 for result in all_results.values() if result)
    total = len(all_results)
    
    print(f"Import Tests: {sum(import_results.values())}/{len(import_results)} passed")
    print(f"Init Tests: {sum(init_results.values())}/{len(init_results)} passed")
    print(f"Flow Tests: {sum(flow_results.values())}/{len(flow_results)} passed")
    print(f"Integration Test: {'✅' if integration_result else '❌'}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total and integration_result:
        print("🎉 ALL CONNECTIVITY TESTS PASSED!")
        print("✅ Components are properly linked and communicating")
        print("🚀 App should be ready to run")
    else:
        print("⚠️ Some tests failed - check error messages above")
        
        failed_tests = [name for name, result in all_results.items() if not result]
        if failed_tests:
            print(f"Failed tests: {', '.join(failed_tests)}")
    
    return passed == total and integration_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)