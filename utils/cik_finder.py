# utils/cik_finder.py - Utility to find and add CIKs for new tickers

import requests
import json
import re
from typing import List, Dict, Optional, Tuple
import time

class CIKFinder:
    """
    Utility to find CIK numbers for ticker symbols
    
    Uses various methods to locate CIK numbers:
    1. SEC company search
    2. Manual lookup helpers
    3. Bulk import from external sources
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Stocker App nfatpro@gmail.com',
            'Accept': 'application/json',
            'Host': 'data.sec.gov'
        }
        
        self.base_url = 'https://data.sec.gov/api/xbrl'
        self.search_url = 'https://data.sec.gov'
        
    def find_cik_by_company_name(self, company_name: str) -> List[Tuple[str, str, str]]:
        """
        Search for CIK by company name
        Returns list of (cik, company_name, ticker) tuples
        """
        print(f"🔍 Searching for company: {company_name}")
        
        try:
            # Use SEC's company tickers endpoint
            url = f"{self.search_url}/files/company_tickers.json"
            
            time.sleep(0.1)  # Rate limiting
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Search through company data
                for key, company_info in data.items():
                    cik = str(company_info.get('cik_str', '')).zfill(10)
                    ticker = company_info.get('ticker', '')
                    title = company_info.get('title', '')
                    
                    # Check if company name matches (case insensitive, partial match)
                    if company_name.lower() in title.lower():
                        results.append((cik, title, ticker))
                        print(f"   ✅ Found: {ticker} - {title} (CIK: {cik})")
                
                if not results:
                    print(f"   ❌ No matches found for '{company_name}'")
                    
                return results
                
            else:
                print(f"❌ SEC API error: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching for company: {e}")
            return []
    
    def find_cik_by_ticker_fuzzy(self, ticker: str) -> List[Tuple[str, str, str]]:
        """
        Fuzzy search for ticker symbols
        Returns list of (cik, company_name, ticker) tuples
        """
        print(f"🔍 Fuzzy searching for ticker: {ticker}")
        
        try:
            url = f"{self.search_url}/files/company_tickers.json"
            
            time.sleep(0.1)  # Rate limiting
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Search through ticker data
                for key, company_info in data.items():
                    cik = str(company_info.get('cik_str', '')).zfill(10)
                    company_ticker = company_info.get('ticker', '')
                    title = company_info.get('title', '')
                    
                    # Check for exact or partial ticker match
                    if (ticker.upper() == company_ticker.upper() or 
                        ticker.upper() in company_ticker.upper() or
                        company_ticker.upper() in ticker.upper()):
                        results.append((cik, title, company_ticker))
                        print(f"   ✅ Found: {company_ticker} - {title} (CIK: {cik})")
                
                if not results:
                    print(f"   ❌ No matches found for ticker '{ticker}'")
                
                return results
                
            else:
                print(f"❌ SEC API error: HTTP {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching for ticker: {e}")
            return []
    
    def verify_cik_has_financial_data(self, cik: str, ticker: str = None) -> bool:
        """
        Verify that a CIK has financial data available
        Checks for revenue data specifically
        """
        print(f"🔍 Verifying financial data for CIK {cik}")
        
        try:
            # Check if revenue data exists
            url = f"{self.base_url}/companyconcept/CIK{cik}/us-gaap/Revenues.json"
            
            time.sleep(0.1)  # Rate limiting
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                usd_data = data.get('units', {}).get('USD', [])
                quarterly_data = [r for r in usd_data if r.get('form') == '10-Q']
                
                print(f"   ✅ Found {len(quarterly_data)} quarterly revenue records")
                return len(quarterly_data) > 0
                
            elif response.status_code == 404:
                print(f"   ❌ No revenue data found (may use different accounting standards)")
                return False
            else:
                print(f"   ⚠️ HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error verifying data: {e}")
            return False
    
    def search_and_verify_ticker(self, ticker: str) -> Optional[Tuple[str, str]]:
        """
        Complete search and verification for a ticker
        Returns (cik, company_name) if found and verified
        """
        print(f"\n🎯 Complete search for ticker: {ticker}")
        print("=" * 50)
        
        # Try fuzzy ticker search first
        results = self.find_cik_by_ticker_fuzzy(ticker)
        
        if not results:
            print(f"💡 No direct ticker matches. Try searching by company name instead.")
            return None
        
        # Verify each result
        for cik, company_name, found_ticker in results:
            print(f"\n🔍 Verifying {found_ticker} - {company_name}")
            
            if self.verify_cik_has_financial_data(cik, found_ticker):
                print(f"✅ VERIFIED: {found_ticker} (CIK: {cik}) has financial data")
                return (cik, company_name)
            else:
                print(f"❌ No usable financial data found")
        
        print(f"❌ No verified matches found for {ticker}")
        return None
    
    def bulk_search_tickers(self, tickers: List[str]) -> Dict[str, Tuple[str, str]]:
        """
        Search for multiple tickers at once
        Returns dict of {ticker: (cik, company_name)}
        """
        results = {}
        
        print(f"🔍 Bulk searching {len(tickers)} tickers...")
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}")
            
            result = self.search_and_verify_ticker(ticker)
            if result:
                cik, company_name = result
                results[ticker] = (cik, company_name)
                print(f"✅ Added {ticker}")
            else:
                print(f"❌ Failed {ticker}")
            
            # Rate limiting between requests
            if i < len(tickers):
                time.sleep(0.2)
        
        print(f"\n📊 Bulk search complete: {len(results)}/{len(tickers)} successful")
        return results
    
    def get_manual_lookup_instructions(self, ticker: str) -> str:
        """
        Provide instructions for manual CIK lookup
        """
        instructions = f"""
🔍 Manual CIK Lookup Instructions for {ticker}:

1. Go to https://www.sec.gov/edgar/searchedgar/companysearch.html
2. Search for '{ticker}' or the full company name
3. Look for the company in search results
4. Click on the company name
5. The CIK number will be shown in the URL or company details
6. CIK format: 10 digits with leading zeros (e.g., 0001234567)

Alternative method:
1. Go to https://data.sec.gov/files/company_tickers.json
2. Search (Ctrl+F) for '{ticker}' 
3. Find the 'cik_str' value for your company

Once you have the CIK, add it using:
```python
from components.cik_library import get_cik_library
cik_lib = get_cik_library()
cik_lib.add_manual_entry('{ticker}', 'CIK_NUMBER', 'Company Name')
```
        """
        return instructions


def find_adap_cik():
    """Specific function to find ADAP's CIK"""
    finder = CIKFinder()
    
    print("🎯 Searching for ADAP (Adaptimmune Therapeutics)")
    
    # Try ticker search
    result = finder.search_and_verify_ticker('ADAP')
    if result:
        cik, company_name = result
        print(f"\n✅ ADAP FOUND!")
        print(f"   CIK: {cik}")
        print(f"   Company: {company_name}")
        print(f"\nTo add to your database:")
        print(f"from components.cik_library import get_cik_library")
        print(f"cik_lib = get_cik_library()")
        print(f"cik_lib.add_manual_entry('ADAP', '{cik}', '{company_name}')")
        return cik, company_name
    
    # Try company name search
    print("\n🔍 Trying company name search...")
    results = finder.find_cik_by_company_name('Adaptimmune')
    
    if results:
        for cik, company_name, ticker in results:
            print(f"   Found: {ticker} - {company_name} (CIK: {cik})")
            if finder.verify_cik_has_financial_data(cik):
                print(f"✅ This CIK has financial data!")
                return cik, company_name
    
    # If not found, provide manual instructions
    print("\n❌ ADAP not found automatically")
    print(finder.get_manual_lookup_instructions('ADAP'))
    return None, None


if __name__ == "__main__":
    # Find ADAP specifically
    find_adap_cik()
    
    # Example of finding other tickers
    finder = CIKFinder()
    
    # Test with some example tickers
    test_tickers = ['PLTR', 'SNOW', 'ABNB']  # Some newer companies
    results = finder.bulk_search_tickers(test_tickers)