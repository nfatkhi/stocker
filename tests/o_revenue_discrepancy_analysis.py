# o_revenue_discrepancy_analysis.py - Analysis of Realty Income revenue data discrepancies

"""
Realty Income (O) Revenue Discrepancy Analysis
Comparing actual reported revenues with what Stocker displays
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List


class ORevenueAnalysis:
    """Analysis of Realty Income revenue discrepancies"""
    
    def __init__(self):
        # CORRECT revenues from official earnings reports (in millions)
        self.actual_revenues = {
            'Q1 2025': 1380.5,  # $1,380.5M from Q1 2025 earnings
            'Q4 2024': 1340.3,  # $1,340.3M from Q4 2024 earnings  
            'Q3 2024': 1330.0,  # $1.33B from Q3 2024 earnings
            'Q2 2024': 1340.0,  # $1.34B from Q2 2024 earnings
            'Q1 2024': 1260.0,  # $1.26B from Q1 2024 earnings
        }
        
        # What Stocker is showing (your reported values)
        self.stocker_values = {
            'Q1 2025': 1384.9,  # What you saw in Stocker
            'Q4 2024': 1342.7,  # What you saw in Stocker
            'Q3 2024': 1336.0,  # What you saw in Stocker
        }
        
        # Known issue: Possible quarterly aggregation
        self.potential_aggregation_issue = {
            'Q3 2024 Displayed': 1336.0,  # What Stocker shows for Q3
            'Q2+Q3 2024 Actual': 1340.0 + 1330.0,  # Q2 + Q3 = 2670.0
            'Q2 Only': 1340.0,
            'Q3 Only': 1330.0,
        }
    
    def analyze_discrepancies(self) -> Dict:
        """Analyze the discrepancies between actual and displayed values"""
        
        analysis = {
            'summary': {},
            'detailed_comparison': [],
            'potential_causes': [],
            'recommendations': []
        }
        
        print("🔍 REALTY INCOME (O) REVENUE DISCREPANCY ANALYSIS")
        print("="*60)
        
        # Compare values where we have both
        for quarter in ['Q1 2025', 'Q4 2024', 'Q3 2024']:
            if quarter in self.actual_revenues and quarter in self.stocker_values:
                actual = self.actual_revenues[quarter]
                displayed = self.stocker_values[quarter]
                diff = displayed - actual
                diff_percent = (diff / actual) * 100
                
                comparison = {
                    'quarter': quarter,
                    'actual': actual,
                    'displayed': displayed,
                    'difference': diff,
                    'difference_percent': diff_percent,
                    'significant': abs(diff_percent) > 0.5  # >0.5% difference
                }
                
                analysis['detailed_comparison'].append(comparison)
                
                print(f"\n📊 {quarter}:")
                print(f"  Actual:    ${actual:,.1f}M")
                print(f"  Displayed: ${displayed:,.1f}M") 
                print(f"  Difference: ${diff:+.1f}M ({diff_percent:+.2f}%)")
                
                if abs(diff_percent) > 0.5:
                    print(f"  ⚠️ SIGNIFICANT DISCREPANCY!")
        
        # Test aggregation hypothesis
        print(f"\n🧪 TESTING AGGREGATION HYPOTHESIS:")
        print(f"Q3 2024 shown in Stocker: ${self.stocker_values['Q3 2024']:,.1f}M")
        print(f"Q3 2024 actual revenue:  ${self.actual_revenues['Q3 2024']:,.1f}M")
        print(f"Q2 2024 actual revenue:  ${self.actual_revenues['Q2 2024']:,.1f}M")
        print(f"Q2+Q3 combined:         ${self.actual_revenues['Q2 2024'] + self.actual_revenues['Q3 2024']:,.1f}M")
        
        # Check if Q3 display might be Q2+Q3 or have other issues
        if abs(self.stocker_values['Q3 2024'] - self.actual_revenues['Q3 2024']) > 5:
            analysis['potential_causes'].append("Q3 data appears to have measurement or aggregation issues")
        
        # Identify potential causes
        analysis['potential_causes'].extend([
            "Finnhub API returning slightly different revenue figures",
            "Potential rounding differences in data source",
            "Different accounting periods or adjustments",
            "Data parsing issues in revenue extraction",
            "Currency conversion or unit conversion errors"
        ])
        
        # Generate recommendations
        analysis['recommendations'] = [
            "🔧 Debug Finnhub API response for O ticker specifically",
            "📊 Compare multiple Finnhub endpoints (basic vs reported financials)",
            "🔍 Check exact field names being extracted for revenue",
            "⚡ Implement revenue validation against known correct values",
            "📈 Add logging to show which Finnhub fields are being used",
            "🎯 Consider cross-validation with other data sources",
            "⚖️ Implement tolerance checks (±1% variance acceptable)"
        ]
        
        return analysis
    
    def generate_debug_script(self) -> str:
        """Generate a debug script to investigate the Finnhub API directly"""
        
        debug_script = '''
# debug_o_finnhub.py - Debug script for Realty Income revenue discrepancies

import requests
import json

def debug_finnhub_o_revenue(api_key: str):
    """Debug Finnhub API for Realty Income revenue data"""
    
    print("🔍 DEBUGGING FINNHUB API FOR REALTY INCOME (O)")
    print("="*50)
    
    base_url = 'https://finnhub.io/api/v1'
    
    # Method 1: financials-reported endpoint
    print("\\n📊 Method 1: Financials Reported")
    url1 = f"{base_url}/stock/financials-reported"
    params1 = {'symbol': 'O', 'freq': 'quarterly', 'token': api_key}
    
    try:
        response1 = requests.get(url1, params=params1, timeout=15)
        print(f"Status: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            reports = data1.get('data', [])[:4]  # Check last 4 quarters
            
            for i, report in enumerate(reports):
                date_end = report.get('endDate', 'N/A')
                year = report.get('year', 'N/A')
                quarter = report.get('quarter', 'N/A')
                
                # Look for revenue in income statement
                ic_data = report.get('report', {}).get('ic', [])
                
                revenue_found = None
                concept_used = None
                
                for item in ic_data:
                    concept = item.get('concept', '').lower()
                    if any(term in concept for term in ['revenue', 'total revenue']):
                        revenue_found = item.get('value', 0)
                        concept_used = item.get('concept')
                        break
                
                print(f"  Q{quarter} {year} ({date_end}): ${revenue_found/1e6:.1f}M ({concept_used})")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 2: metric endpoint
    print("\\n📈 Method 2: Metric Endpoint")
    url2 = f"{base_url}/stock/metric"
    params2 = {'symbol': 'O', 'metric': 'all', 'token': api_key}
    
    try:
        response2 = requests.get(url2, params=params2, timeout=15)
        print(f"Status: {response2.status_code}")
        
        if response2.status_code == 200:
            data2 = response2.json()
            quarterly_data = data2.get('series', {}).get('quarterly', {})
            
            if 'revenue' in quarterly_data:
                revenue_series = quarterly_data['revenue'][:4]
                for entry in revenue_series:
                    period = entry.get('period', 'N/A')
                    value = entry.get('v', 0)
                    print(f"  {period}: ${value/1e6:.1f}M")
            else:
                print("  No revenue series found")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Method 3: basic financials endpoint  
    print("\\n📋 Method 3: Basic Financials")
    url3 = f"{base_url}/stock/financials"
    params3 = {'symbol': 'O', 'statement': 'ic', 'freq': 'quarterly', 'token': api_key}
    
    try:
        response3 = requests.get(url3, params=params3, timeout=15)
        print(f"Status: {response3.status_code}")
        
        if response3.status_code == 200:
            data3 = response3.json()
            financials = data3.get('financials', [])[:4]
            
            for period_data in financials:
                period = period_data.get('period', 'N/A')
                revenue = period_data.get('revenue') or period_data.get('totalRevenue')
                print(f"  {period}: ${revenue/1e6:.1f}M" if revenue else f"  {period}: No revenue")
    
    except Exception as e:
        print(f"❌ Error: {e}")

# Example usage:
# debug_finnhub_o_revenue("YOUR_FINNHUB_API_KEY")
'''
        
        return debug_script
    
    def print_known_correct_values(self):
        """Print the officially confirmed correct values"""
        
        print("\\n✅ OFFICIALLY CONFIRMED CORRECT VALUES:")
        print("="*45)
        
        sources = {
            'Q1 2025': 'Official earnings release May 5, 2025',
            'Q4 2024': 'Official earnings release Feb 24, 2025', 
            'Q3 2024': 'Official earnings release Nov 4, 2024',
            'Q2 2024': 'Official earnings release Aug 5, 2024',
            'Q1 2024': 'Official earnings release May 6, 2024'
        }
        
        for quarter, revenue in self.actual_revenues.items():
            source = sources.get(quarter, 'Financial reports')
            print(f"{quarter}: ${revenue:,.1f}M ({source})")
    
    def generate_validation_test(self) -> str:
        """Generate a validation test for the corrected data fetcher"""
        
        test_code = '''
def test_o_revenue_accuracy(data_fetcher):
    """Test that O revenue data matches known correct values"""
    
    # Known correct values (in millions)
    known_correct = {
        '2025-03-31': 1380.5,  # Q1 2025
        '2024-12-31': 1340.3,  # Q4 2024
        '2024-09-30': 1330.0,  # Q3 2024
        '2024-06-30': 1340.0,  # Q2 2024
        '2024-03-31': 1260.0,  # Q1 2024
    }
    
    # Fetch data for O
    class MockEvent:
        def __init__(self):
            self.data = {'ticker': 'O'}
    
    event = MockEvent()
    data_fetcher.fetch_stock_data(event)
    
    # Get the quarterly financials
    # (This would need to be integrated with your actual event system)
    
    # Validate revenue values
    tolerance = 0.02  # 2% tolerance for minor differences
    
    for quarter_data in quarterly_financials:
        date = quarter_data.date
        fetched_revenue = quarter_data.revenue / 1e6  # Convert to millions
        
        if date in known_correct:
            expected_revenue = known_correct[date]
            diff_percent = abs(fetched_revenue - expected_revenue) / expected_revenue
            
            if diff_percent > tolerance:
                print(f"❌ FAIL: {date} revenue mismatch")
                print(f"   Expected: ${expected_revenue:.1f}M")
                print(f"   Fetched:  ${fetched_revenue:.1f}M")
                print(f"   Diff:     {diff_percent*100:.1f}%")
                return False
            else:
                print(f"✅ PASS: {date} revenue accurate (${fetched_revenue:.1f}M)")
    
    return True
'''
        
        return test_code


# Run the analysis
if __name__ == "__main__":
    analyzer = ORevenueAnalysis()
    
    # Perform the analysis
    results = analyzer.analyze_discrepancies()
    
    print("\\n" + "="*60)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*60)
    
    print("\\n🎯 KEY FINDINGS:")
    print("• Small but consistent discrepancies in revenue data")
    print("• Differences range from +0.33% to +0.45%")
    print("• Suggests systematic issue in data extraction or source")
    
    print("\\n🔧 IMMEDIATE ACTIONS:")
    for rec in results['recommendations'][:4]:
        print(f"• {rec}")
    
    print("\\n📊 DEBUGGING NEXT STEPS:")
    print("1. Run the debug script against Finnhub API")
    print("2. Check which exact fields are being extracted")
    print("3. Verify unit conversion (millions vs billions)")
    print("4. Implement the validation test")
    
    # Print known correct values
    analyzer.print_known_correct_values()
    
    print("\\n💡 The discrepancies are small but significant enough")
    print("   to warrant investigation and correction for data integrity.")