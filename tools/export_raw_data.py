# export_raw_data.py - Export raw XBRL data to CSV files using data_fetcher

import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import sys

# Import our data fetcher
try:
    from components.data_fetcher import fetch_company_data
except ImportError:
    print("❌ Cannot import data_fetcher. Make sure you're running from the project root.")
    sys.exit(1)


def export_ticker_to_csv(ticker: str, output_dir: str = "exports") -> bool:
    """
    Export ticker data to CSV files - one file per quarter
    
    Args:
        ticker: Stock ticker to export
        output_dir: Directory to save CSV files
        
    Returns:
        True if successful, False otherwise
    """
    
    print(f"🔍 Fetching data for {ticker}...")
    
    # Fetch raw data using our data_fetcher
    raw_filings, metadata = fetch_company_data(ticker, max_filings=8)  # Get last 8 quarters
    
    if not raw_filings:
        print(f"❌ No data found for {ticker}")
        if 'error' in metadata:
            print(f"   Error: {metadata['error']}")
        return False
    
    print(f"✅ Found {len(raw_filings)} quarters of data")
    print(f"   Company: {metadata.get('company_name', 'Unknown')}")
    
    # Create output directory
    ticker_dir = os.path.join(output_dir, ticker.upper())
    os.makedirs(ticker_dir, exist_ok=True)
    
    # Process each quarter
    for i, filing in enumerate(raw_filings):
        quarter = filing._extract_quarter()
        year = filing._extract_year()
        filing_date = filing.filing_date
        
        print(f"\n📊 Processing {quarter} {year} (Filed: {filing_date})")
        
        if not filing.facts_json:
            print(f"   ⚠️ No facts data for {quarter} {year}")
            continue
        
        try:
            # Parse the facts JSON
            facts_data = json.loads(filing.facts_json)
            
            if not facts_data:
                print(f"   ⚠️ Empty facts data for {quarter} {year}")
                continue
            
            # Convert to DataFrame
            facts_df = pd.DataFrame(facts_data)
            
            print(f"   📋 Raw facts: {len(facts_df)} records")
            print(f"   📋 Columns: {list(facts_df.columns)}")
            
            # Add metadata columns
            facts_df['ticker'] = ticker
            facts_df['filing_date'] = filing_date
            facts_df['quarter'] = quarter
            facts_df['year'] = year
            facts_df['company_name'] = filing.company_name
            
            # Clean up the data for CSV export
            # Handle any JSON-like columns
            for col in facts_df.columns:
                if facts_df[col].dtype == 'object':
                    # Convert any remaining JSON objects to strings
                    facts_df[col] = facts_df[col].astype(str)
            
            # Create filename
            csv_filename = f"{ticker}_{year}_{quarter}_raw_facts.csv"
            csv_path = os.path.join(ticker_dir, csv_filename)
            
            # Export to CSV
            facts_df.to_csv(csv_path, index=False)
            
            print(f"   ✅ Exported to: {csv_filename}")
            print(f"   📊 CSV size: {len(facts_df)} rows x {len(facts_df.columns)} columns")
            
            # Show sample of what we exported
            if len(facts_df) > 0:
                print(f"   🔍 Sample concepts found:")
                
                # Look for interesting concepts to highlight
                sample_concepts = []
                if 'concept' in facts_df.columns:
                    unique_concepts = facts_df['concept'].unique()
                    
                    # Look for common financial concepts
                    interesting_concepts = [
                        'Revenue', 'Revenues', 'NetIncomeLoss', 'Assets', 
                        'Liabilities', 'StockholdersEquity', 'CashAndCashEquivalents'
                    ]
                    
                    for concept in interesting_concepts:
                        matches = [c for c in unique_concepts if concept.lower() in c.lower()]
                        if matches:
                            sample_concepts.extend(matches[:2])  # Max 2 matches per concept
                        
                        if len(sample_concepts) >= 6:  # Show max 6 concepts
                            break
                
                if sample_concepts:
                    for concept in sample_concepts[:6]:
                        concept_rows = facts_df[facts_df['concept'] == concept]
                        if len(concept_rows) > 0:
                            sample_value = concept_rows.iloc[0].get('value', 'N/A')
                            print(f"      • {concept}: {sample_value}")
                else:
                    # If no concept column or no matches, show first few rows
                    print(f"      • First few rows:")
                    for idx, row in facts_df.head(3).iterrows():
                        row_sample = {k: v for k, v in row.items() if k in ['concept', 'value', 'period']}
                        print(f"        {dict(row_sample)}")
        
        except Exception as e:
            print(f"   ❌ Error processing {quarter} {year}: {e}")
            continue
    
    # Create summary file
    summary_data = {
        'ticker': ticker,
        'company_name': metadata.get('company_name', 'Unknown'),
        'export_timestamp': datetime.now().isoformat(),
        'quarters_exported': len(raw_filings),
        'data_source': metadata.get('data_source', 'Unknown'),
        'filings_info': []
    }
    
    for filing in raw_filings:
        summary_data['filings_info'].append({
            'quarter': filing._extract_quarter(),
            'year': filing._extract_year(),
            'filing_date': filing.filing_date,
            'facts_count': filing.total_facts_count,
            'extraction_success': filing.extraction_success
        })
    
    summary_path = os.path.join(ticker_dir, f"{ticker}_export_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\n🎉 Export complete for {ticker}!")
    print(f"   📁 Files saved to: {ticker_dir}")
    print(f"   📊 Quarters exported: {len(raw_filings)}")
    print(f"   📋 Summary saved to: {ticker}_export_summary.json")
    
    return True


def main():
    """Main function to run the export"""
    
    # You can change this ticker to any company you want to test
    test_ticker = "MSFT"  # Apple Inc.
    
    if len(sys.argv) > 1:
        test_ticker = sys.argv[1].upper()
    
    print(f"🚀 Raw XBRL Data Export Tool")
    print(f"=" * 50)
    print(f"Ticker: {test_ticker}")
    print(f"Output: exports/{test_ticker}/")
    
    try:
        success = export_ticker_to_csv(test_ticker)
        
        if success:
            print(f"\n✅ Export successful!")
            print(f"\n💡 Files created:")
            
            ticker_dir = os.path.join("exports", test_ticker)
            if os.path.exists(ticker_dir):
                files = [f for f in os.listdir(ticker_dir) if f.endswith('.csv')]
                for file in sorted(files):
                    file_path = os.path.join(ticker_dir, file)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    print(f"   📄 {file} ({file_size:.1f} KB)")
            
            print(f"\n🔍 To examine the data:")
            print(f"   cd exports/{test_ticker}")
            print(f"   ls -la")
            print(f"   head -20 {test_ticker}_*_Q*_raw_facts.csv")
        
        else:
            print(f"\n❌ Export failed!")
    
    except Exception as e:
        print(f"\n❌ Error during export: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()