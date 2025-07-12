# export_raw_data.py - FIXED: Export raw XBRL data to CSV files using data_fetcher

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


def extract_quarter_from_filing_date(filing_date: str) -> tuple:
    """
    Extract quarter and year from filing date
    
    Args:
        filing_date: Filing date string (YYYY-MM-DD)
        
    Returns:
        Tuple of (quarter, year)
    """
    try:
        # Parse the filing date
        date_parts = filing_date.split('-')
        year = int(date_parts[0])
        month = int(date_parts[1])
        
        # Estimate quarter from filing month
        # Q1 (Jan-Mar) typically filed in Apr-May
        # Q2 (Apr-Jun) typically filed in Jul-Aug  
        # Q3 (Jul-Sep) typically filed in Oct-Nov
        # Q4 (Oct-Dec) typically filed in Feb-Mar (next year)
        
        if month in [1, 2, 3, 4]:
            quarter = "Q4"
            quarter_year = year - 1  # Q4 of previous year
        elif month in [5, 6]:
            quarter = "Q1"
            quarter_year = year
        elif month in [7, 8, 9]:
            quarter = "Q2"
            quarter_year = year
        else:  # month in [10, 11, 12]
            quarter = "Q3"
            quarter_year = year
        
        return quarter, quarter_year
        
    except Exception as e:
        print(f"   ⚠️ Error parsing filing date '{filing_date}': {e}")
        return "QX", 2024


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
        # FIXED: Extract quarter/year from filing date
        quarter, year = extract_quarter_from_filing_date(filing.filing_date)
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
            
            # Show sample of what we exported - FOCUS ON REVENUE CONCEPTS
            if len(facts_df) > 0:
                print(f"   🔍 Revenue concepts found:")
                
                # Look specifically for revenue-related concepts
                if 'concept' in facts_df.columns:
                    unique_concepts = facts_df['concept'].unique()
                    
                    # Look for revenue concepts specifically
                    revenue_keywords = [
                        'Revenue', 'Revenues', 'Sales', 'Income', 'Contract'
                    ]
                    
                    revenue_concepts = []
                    for concept in unique_concepts:
                        concept_lower = concept.lower()
                        if any(keyword.lower() in concept_lower for keyword in revenue_keywords):
                            revenue_concepts.append(concept)
                    
                    if revenue_concepts:
                        print(f"      📊 Found {len(revenue_concepts)} revenue-related concepts:")
                        for concept in revenue_concepts[:10]:  # Show first 10
                            concept_rows = facts_df[facts_df['concept'] == concept]
                            if len(concept_rows) > 0:
                                # Try to get the value
                                for val_col in ['value', 'numeric_value', 'amount']:
                                    if val_col in concept_rows.columns:
                                        sample_value = concept_rows.iloc[0][val_col]
                                        if pd.notna(sample_value) and sample_value != '':
                                            try:
                                                # Try to format as number if possible
                                                num_val = float(sample_value)
                                                if abs(num_val) >= 1000000:
                                                    formatted = f"${num_val/1e6:.1f}M"
                                                else:
                                                    formatted = f"${num_val:,.0f}"
                                                print(f"      • {concept}: {formatted}")
                                            except:
                                                print(f"      • {concept}: {sample_value}")
                                            break
                                else:
                                    print(f"      • {concept}: (no value)")
                    else:
                        print(f"      ⚠️ No revenue concepts found")
                        
                        # Show some sample concepts instead
                        print(f"      📋 Sample concepts available:")
                        for concept in list(unique_concepts)[:5]:
                            print(f"        • {concept}")
                else:
                    print(f"      ⚠️ No 'concept' column found")
                    print(f"      📋 Available columns: {list(facts_df.columns)}")
        
        except Exception as e:
            print(f"   ❌ Error processing {quarter} {year}: {e}")
            import traceback
            traceback.print_exc()
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
        quarter, year = extract_quarter_from_filing_date(filing.filing_date)
        summary_data['filings_info'].append({
            'quarter': quarter,
            'year': year,
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
    
    # Default to COMM to help debug the revenue issue
    test_ticker = "COMM"  # CommScope - the one with revenue issues
    
    if len(sys.argv) > 1:
        test_ticker = sys.argv[1].upper()
    
    print(f"🚀 Raw XBRL Data Export Tool - Revenue Debugging Edition")
    print(f"=" * 60)
    print(f"Ticker: {test_ticker}")
    print(f"Output: exports/{test_ticker}/")
    print(f"Focus: Finding correct revenue concepts")
    
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
            
            print(f"\n🔍 To examine the revenue data:")
            print(f"   cd exports/{test_ticker}")
            print(f"   # Look for revenue concepts in the CSV files")
            print(f"   grep -i revenue {test_ticker}_*_raw_facts.csv | head -20")
            print(f"   # Or open in Excel/Numbers to search for revenue concepts")
            
            if test_ticker == "COMM":
                print(f"\n🎯 COMM Revenue Debugging:")
                print(f"   Look for concepts containing values around $1.12B")
                print(f"   Current extraction shows $1.6M - clearly wrong")
                print(f"   Find which concept has the correct revenue amount")
        
        else:
            print(f"\n❌ Export failed!")
    
    except Exception as e:
        print(f"\n❌ Error during export: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()