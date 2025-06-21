# sec_10q_finder.py
# Find recent 10-Q filings and extract data from them directly

import requests
import json
from datetime import datetime
import time

class SEC10QExplorer:
    """Find and explore recent 10-Q quarterly filings"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Stocker App nfatpro@gmail.com',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'data.sec.gov',
            'Accept': 'application/json'
        }
        
        self.last_request_time = 0
        self.rate_limit_delay = 0.1
        
        self.known_ciks = {
            'AAPL': '0000320193',
            'MSFT': '0000789019',
            'GOOGL': '0001652044',
            'O': '0000726728',
            'TSLA': '0001318605',
        }
    
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def find_recent_10q_filings(self, ticker):
        """Find recent 10-Q filings for a company"""
        cik = self.known_ciks.get(ticker.upper())
        if not cik:
            print(f"❌ Unknown ticker {ticker}")
            return []
        
        self._rate_limit()
        
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        
        print(f"\n🔍 Finding recent 10-Q filings for {ticker}")
        print(f"📡 URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                company_name = data.get('name', 'Unknown')
                print(f"✅ Success! Company: {company_name}")
                
                # Get recent filings
                filings = data.get('filings', {}).get('recent', {})
                
                if not filings:
                    print("❌ No recent filings found")
                    return []
                
                # Extract 10-Q filings
                forms = filings.get('form', [])
                filing_dates = filings.get('filingDate', [])
                accession_numbers = filings.get('accessionNumber', [])
                report_dates = filings.get('reportDate', [])
                
                print(f"📊 Total recent filings: {len(forms)}")
                
                # Find 10-Q filings
                quarterly_filings = []
                for i, form in enumerate(forms):
                    if form == '10-Q':
                        filing_info = {
                            'form': form,
                            'filing_date': filing_dates[i] if i < len(filing_dates) else 'N/A',
                            'accession_number': accession_numbers[i] if i < len(accession_numbers) else 'N/A',
                            'report_date': report_dates[i] if i < len(report_dates) else 'N/A',
                            'cik': cik
                        }
                        quarterly_filings.append(filing_info)
                
                print(f"📋 Found {len(quarterly_filings)} recent 10-Q filings")
                
                # Show recent 10-Q filings
                if quarterly_filings:
                    print(f"\n📊 RECENT 10-Q FILINGS:")
                    print(f"{'#':<3} {'Report Date':<12} {'Filed':<12} {'Accession Number':<25}")
                    print("-" * 55)
                    
                    for i, filing in enumerate(quarterly_filings[:10], 1):
                        print(f"{i:<3} {filing['report_date']:<12} {filing['filing_date']:<12} {filing['accession_number']:<25}")
                
                return quarterly_filings[:5]  # Return top 5 recent filings
                
            else:
                print(f"❌ Error: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return []
    
    def get_10q_filing_data(self, filing_info, ticker):
        """Get the actual XBRL data from a specific 10-Q filing"""
        self._rate_limit()
        
        cik = filing_info['cik']
        accession = filing_info['accession_number'].replace('-', '')
        
        # SEC XBRL data URL for specific filing
        url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
        
        print(f"\n🔍 Getting XBRL data for {ticker} filing {filing_info['accession_number']}")
        print(f"📅 Report Date: {filing_info['report_date']}")
        print(f"📡 URL: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Look for revenue data in this specific filing
                facts = data.get('facts', {})
                us_gaap = facts.get('us-gaap', {})
                
                # Try different revenue concepts
                revenue_concepts = [
                    'Revenues',
                    'SalesRevenueNet',
                    'RevenueFromContractWithCustomerExcludingAssessedTax',
                    'RevenueFromContractWithCustomerIncludingAssessedTax',
                    'TotalRevenues'
                ]
                
                filing_revenue_data = None
                concept_used = None
                
                for concept in revenue_concepts:
                    if concept in us_gaap:
                        concept_data = us_gaap[concept]
                        usd_data = concept_data.get('units', {}).get('USD', [])
                        
                        # Look for data from this specific filing date
                        for record in usd_data:
                            if (record.get('end') == filing_info['report_date'] and 
                                record.get('form') == '10-Q'):
                                filing_revenue_data = record
                                concept_used = concept
                                break
                        
                        if filing_revenue_data:
                            break
                
                if filing_revenue_data:
                    print(f"✅ Found revenue data using concept: {concept_used}")
                    return filing_revenue_data, concept_used
                else:
                    print(f"❌ No revenue data found for this filing date")
                    
                    # Show what data is available for debugging
                    print(f"\n🔍 Available revenue concepts:")
                    for concept in revenue_concepts:
                        if concept in us_gaap:
                            usd_data = us_gaap[concept].get('units', {}).get('USD', [])
                            recent_dates = [r.get('end') for r in usd_data if r.get('form') == '10-Q']
                            recent_dates = sorted(set(recent_dates), reverse=True)[:5]
                            print(f"   {concept}: {len(usd_data)} records, recent dates: {recent_dates}")
                
                return None, None
                
            else:
                print(f"❌ Error: {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None, None
    
    def explore_ticker_10q_data(self, ticker):
        """Complete exploration of 10-Q data for a ticker"""
        print(f"\n{'='*80}")
        print(f"🏛️ SEC 10-Q EXPLORATION FOR {ticker}")
        print(f"{'='*80}")
        
        # Step 1: Find recent 10-Q filings
        recent_10q = self.find_recent_10q_filings(ticker)
        
        if not recent_10q:
            print(f"❌ No recent 10-Q filings found for {ticker}")
            return
        
        print(f"\n📊 Exploring revenue data in recent 10-Q filings...")
        
        # Step 2: Try to get revenue data from each recent filing
        revenue_data_found = []
        
        for i, filing in enumerate(recent_10q[:3], 1):  # Check top 3 filings
            print(f"\n🔍 Checking filing #{i}:")
            revenue_data, concept = self.get_10q_filing_data(filing, ticker)
            
            if revenue_data:
                revenue_data_found.append({
                    'filing_info': filing,
                    'revenue_data': revenue_data,
                    'concept': concept
                })
                
                # Display the revenue data
                value = revenue_data.get('val', 0)
                start_date = revenue_data.get('start', 'N/A')
                end_date = revenue_data.get('end', 'N/A')
                
                if value > 1e9:
                    value_str = f"${value/1e9:.2f}B"
                elif value > 1e6:
                    value_str = f"${value/1e6:.1f}M"
                else:
                    value_str = f"${value:,.0f}"
                
                print(f"   ✅ Revenue: {value_str}")
                print(f"   📅 Period: {start_date} to {end_date}")
                print(f"   📋 Concept: {concept}")
            else:
                print(f"   ❌ No revenue data found")
        
        # Step 3: Summary
        if revenue_data_found:
            print(f"\n✅ SUMMARY: Found revenue data in {len(revenue_data_found)} filings")
            
            print(f"\n📊 QUARTERLY REVENUE DATA:")
            print(f"{'Quarter End':<12} {'Revenue':<12} {'Period Start':<12} {'Filed':<12}")
            print("-" * 50)
            
            for item in revenue_data_found:
                filing = item['filing_info']
                revenue = item['revenue_data']
                
                value = revenue.get('val', 0)
                value_str = f"${value/1e9:.2f}B" if value > 1e9 else f"${value/1e6:.1f}M"
                
                print(f"{revenue.get('end', 'N/A'):<12} {value_str:<12} {revenue.get('start', 'N/A'):<12} {filing['filing_date']:<12}")
        else:
            print(f"\n❌ No revenue data found in recent 10-Q filings")
            print(f"💡 This might mean:")
            print(f"   • Company uses different revenue concept names")
            print(f"   • Recent filings are not yet in XBRL format")
            print(f"   • Data is in a different SEC endpoint")

def main():
    """Main function"""
    print("🏛️ SEC 10-Q Recent Filings Explorer")
    print("=" * 50)
    
    explorer = SEC10QExplorer()
    
    while True:
        print(f"\n🏛️ Available tickers: {list(explorer.known_ciks.keys())}")
        ticker_input = input("\n📈 Enter ticker symbol (or 'quit' to exit): ").strip().upper()
        
        if ticker_input.lower() == 'quit':
            print("👋 Goodbye!")
            break
        
        if not ticker_input:
            print("❌ Please enter a valid ticker symbol")
            continue
        
        if ticker_input not in explorer.known_ciks:
            print(f"❌ Unknown ticker. Please use one of: {list(explorer.known_ciks.keys())}")
            continue
        
        # Explore 10-Q data for the ticker
        explorer.explore_ticker_10q_data(ticker_input)
        
        print(f"\n" + "="*80)

if __name__ == "__main__":
    main()