# revenue_inspector.py - Uses your existing config setup

import requests
from datetime import datetime
from typing import Dict, List, Optional
from config import API_KEYS  # Import your existing config

class RawRevenueInspector:
    """Inspect raw us-gaap_Revenues data from Finnhub using existing config"""
    
    def __init__(self):
        self.api_key = API_KEYS['finnhub']
        self.base_url = "https://finnhub.io/api/v1"
        print(f"🔑 Using Finnhub API key: {self.api_key[:8]}...{self.api_key[-4:]}")
    
    def inspect_raw_revenues(self, ticker: str, num_quarters: int = 12) -> None:
        """Inspect last N quarters of us-gaap_Revenues data"""
        print(f"\n🔍 RAW REVENUE INSPECTOR - {ticker.upper()}")
        print(f"📊 Analyzing last {num_quarters} quarters of us-gaap_Revenues data")
        print("=" * 80)
        
        try:
            # Get raw reported financials from Finnhub
            url = f"{self.base_url}/stock/financials-reported"
            params = {
                'symbol': ticker,
                'token': self.api_key
            }
            
            print(f"🌐 Fetching: {url}")
            response = requests.get(url, params=params, timeout=30)
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 401:
                print("❌ Authentication failed!")
                print("💡 Check your FINNHUB_API_KEY in .env file")
                return
            elif response.status_code != 200:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return
            
            data = response.json()
            reports = data.get('data', [])
            
            if not reports:
                print(f"❌ No financial reports found for {ticker}")
                return
            
            print(f"📋 Found {len(reports)} total financial reports")
            
            # Process and display revenue data
            self._analyze_revenue_data(reports, num_quarters)
            
        except Exception as e:
            print(f"❌ Error inspecting raw revenue data: {e}")
            import traceback
            traceback.print_exc()
    
    def _analyze_revenue_data(self, reports: List[Dict], num_quarters: int) -> None:
        """Analyze and display revenue data from reports"""
        
        revenue_data = []
        
        # Extract us-gaap_Revenues from each report
        for report in reports:
            try:
                period = report.get('period', 'Unknown')
                year = report.get('year', 0)
                quarter = report.get('quarter', 0)
                
                # Skip annual reports, focus on quarterly
                if quarter == 0:
                    continue
                
                # Look for us-gaap_Revenues in the report
                ic_statements = report.get('report', {}).get('ic', [])
                
                us_gaap_revenues = None
                all_revenue_fields = []
                
                for item in ic_statements:
                    concept = item.get('concept', '')
                    value = item.get('value', 0)
                    
                    # Collect all revenue-related fields for comparison
                    if 'revenue' in concept.lower():
                        all_revenue_fields.append({
                            'concept': concept,
                            'value': value,
                            'value_billions': value / 1e9 if value and value > 0 else 0
                        })
                    
                    # Find us-gaap_Revenues specifically
                    if concept == 'us-gaap_Revenues':
                        us_gaap_revenues = value
                
                revenue_data.append({
                    'period': period,
                    'year': year,
                    'quarter': quarter,
                    'quarter_label': f"{year}Q{quarter}",
                    'us_gaap_revenues': us_gaap_revenues,
                    'us_gaap_revenues_billions': us_gaap_revenues / 1e9 if us_gaap_revenues else None,
                    'all_revenue_fields': all_revenue_fields
                })
                
            except Exception as e:
                print(f"⚠️ Error processing report for {period}: {e}")
                continue
        
        # Sort by year and quarter (most recent first)
        revenue_data.sort(key=lambda x: (x['year'], x['quarter']), reverse=True)
        
        # Display results for last N quarters
        print(f"\n📊 US-GAAP REVENUES ANALYSIS (Last {num_quarters} Quarters)")
        print("-" * 80)
        
        displayed = 0
        for i, data in enumerate(revenue_data):
            if displayed >= num_quarters:
                break
            
            quarter_label = data['quarter_label']
            us_gaap_rev = data['us_gaap_revenues']
            us_gaap_rev_billions = data['us_gaap_revenues_billions']
            
            if us_gaap_rev is not None:
                print(f"✅ {quarter_label}: us-gaap_Revenues = ${us_gaap_rev:,} (${us_gaap_rev_billions:.2f}B)")
                displayed += 1
                
                # Show other revenue fields for comparison
                other_fields = data['all_revenue_fields']
                if len(other_fields) > 1:  # More than just us-gaap_Revenues
                    print(f"   📋 Other revenue fields in same quarter:")
                    for field in other_fields:
                        if field['concept'] != 'us-gaap_Revenues':
                            print(f"      • {field['concept']}: ${field['value']:,} (${field['value_billions']:.2f}B)")
                    print()
            else:
                print(f"❌ {quarter_label}: us-gaap_Revenues = NOT FOUND")
                # Show what revenue fields ARE available
                other_fields = data['all_revenue_fields']
                if other_fields:
                    print(f"   📋 Available revenue fields:")
                    for field in other_fields:
                        print(f"      • {field['concept']}: ${field['value']:,} (${field['value_billions']:.2f}B)")
                print()
        
        # Summary analysis
        print("=" * 80)
        print("📈 REVENUE PATTERN ANALYSIS")
        print("-" * 40)
        
        valid_revenues = [d for d in revenue_data[:num_quarters] if d['us_gaap_revenues'] is not None]
        
        if valid_revenues:
            revenues_billions = [d['us_gaap_revenues_billions'] for d in valid_revenues]
            avg_revenue = sum(revenues_billions) / len(revenues_billions)
            min_revenue = min(revenues_billions)
            max_revenue = max(revenues_billions)
            
            print(f"Valid quarters with us-gaap_Revenues: {len(valid_revenues)}/{num_quarters}")
            print(f"Average revenue: ${avg_revenue:.2f}B")
            print(f"Range: ${min_revenue:.2f}B to ${max_revenue:.2f}B")
            print(f"Variation: {((max_revenue - min_revenue) / avg_revenue * 100):.1f}%")
            
            # Flag potential outliers
            outliers = []
            normal_quarters = []
            for d in valid_revenues:
                rev = d['us_gaap_revenues_billions']
                if rev > avg_revenue * 1.5:  # More than 1.5x average
                    outliers.append(d)
                else:
                    normal_quarters.append(d)
            
            if outliers:
                print(f"\n🚨 POTENTIAL OUTLIERS (>1.5x average):")
                for outlier in outliers:
                    ratio = outlier['us_gaap_revenues_billions'] / avg_revenue
                    print(f"   • {outlier['quarter_label']}: ${outlier['us_gaap_revenues_billions']:.2f}B ({ratio:.1f}x average)")
                    
                    # Show what other revenue fields exist in outlier quarters
                    other_fields = outlier['all_revenue_fields']
                    reit_specific = [f for f in other_fields if 'realestate' in f['concept'].lower()]
                    if reit_specific:
                        print(f"     💡 REIT-specific fields available:")
                        for field in reit_specific:
                            print(f"        • {field['concept']}: ${field['value_billions']:.2f}B")
            
            if normal_quarters:
                normal_avg = sum(d['us_gaap_revenues_billions'] for d in normal_quarters) / len(normal_quarters)
                print(f"\n✅ NORMAL QUARTERS AVERAGE: ${normal_avg:.2f}B ({len(normal_quarters)} quarters)")
                
                # Show typical REIT revenue fields in normal quarters
                print(f"\n🏢 TYPICAL REIT REVENUE FIELDS IN NORMAL QUARTERS:")
                for d in normal_quarters[:3]:  # Show first 3 normal quarters
                    reit_fields = [f for f in d['all_revenue_fields'] if 'realestate' in f['concept'].lower()]
                    if reit_fields:
                        print(f"   {d['quarter_label']}:")
                        for field in reit_fields:
                            print(f"      • {field['concept']}: ${field['value_billions']:.2f}B")
                        
        else:
            print("❌ No valid us-gaap_Revenues data found!")

# Simple script to run the inspector
if __name__ == "__main__":
    inspector = RawRevenueInspector()
    
    # Test with Realty Income
    inspector.inspect_raw_revenues("O", 12)
    
    print("\n" + "="*80)
    print("🎯 CONCLUSION: This will show you if the $3.9B values are")
    print("   actual data quality issues in Finnhub's raw data, or if")
    print("   there are better REIT-specific revenue fields to use.")
    print("="*80)