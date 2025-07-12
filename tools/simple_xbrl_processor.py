# tools/simple_xbrl_processor.py - Lightweight XBRL data processor

import json
import os
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import io


class SimpleXBRLProcessor:
    """Lightweight processor to convert raw XBRL cache to clean datasets"""
    
    def __init__(self, cache_dir: str = "data/cache", output_dir: str = "data/unified"):
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Simple concept mapping - covers 90% of companies
        self.key_concepts = {
            'revenue': ['Revenue', 'Revenues', 'SalesRevenueNet', 'PropertyIncome', 'RentalIncome'],
            'net_income': ['NetIncomeLoss', 'NetIncome', 'ProfitLoss'],
            'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByOperatingActivities'],
            'total_assets': ['Assets', 'TotalAssets'],
            'total_liabilities': ['Liabilities', 'TotalLiabilities']
        }
    
    def process_ticker(self, ticker: str) -> pd.DataFrame:
        """Process one ticker and return clean DataFrame"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            print(f"❌ No cache for {ticker}")
            return pd.DataFrame()
        
        print(f"🔄 Processing {ticker}...")
        
        # Get all quarter files
        quarter_files = [f for f in os.listdir(ticker_dir) 
                        if f.endswith('.json') and f != 'metadata.json']
        
        all_quarters = []
        
        for quarter_file in quarter_files:
            quarter_data = self._process_quarter(ticker_dir, quarter_file, ticker)
            if quarter_data:
                all_quarters.append(quarter_data)
        
        if not all_quarters:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_quarters)
        df = df.sort_values('filing_date', ascending=False)  # Most recent first
        
        print(f"   ✅ {len(df)} quarters processed")
        return df
    
    def _process_quarter(self, ticker_dir: str, quarter_file: str, ticker: str) -> Optional[Dict]:
        """Process single quarter file"""
        file_path = os.path.join(ticker_dir, quarter_file)
        
        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
            
            # Basic quarter info
            quarter_data = {
                'ticker': ticker,
                'filing_date': raw_data.get('filing_date', ''),
                'quarter': self._get_quarter(raw_data.get('filing_date', '')),
                'year': self._get_year(raw_data.get('filing_date', '')),
                'form_type': raw_data.get('form_type', '10-Q')
            }
            
            # Extract financial metrics
            if raw_data.get('facts_json'):
                facts_df = pd.read_json(io.StringIO(raw_data['facts_json']))
                financials = self._extract_simple_financials(facts_df)
                quarter_data.update(financials)
            
            return quarter_data
            
        except Exception as e:
            print(f"   ⚠️ Error processing {quarter_file}: {e}")
            return None
    
    def _extract_simple_financials(self, facts_df: pd.DataFrame) -> Dict:
        """Extract key financial metrics - simple approach"""
        financials = {}
        
        for metric, concepts in self.key_concepts.items():
            value = self._find_concept_value(facts_df, concepts)
            financials[metric] = value
        
        # Calculate simple derived metrics
        ocf = financials.get('operating_cash_flow')
        financials['free_cash_flow'] = ocf  # Simplified (OCF ≈ FCF)
        
        # Add quarterly growth if we have revenue
        revenue = financials.get('revenue')
        if revenue and revenue > 0:
            financials['revenue_millions'] = round(revenue / 1000000, 1)
        
        return financials
    
    def _find_concept_value(self, facts_df: pd.DataFrame, concepts: List[str]) -> Optional[float]:
        """Find value for financial concept - simple search"""
        for concept in concepts:
            # Case-insensitive search
            matches = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            
            if len(matches) > 0:
                # Get the most recent/best value
                for _, row in matches.iterrows():
                    value = row.get('value', row.get('numeric_value'))
                    if value is not None:
                        try:
                            return float(value)
                        except (ValueError, TypeError):
                            continue
        
        return None
    
    def _get_quarter(self, filing_date: str) -> str:
        """Extract quarter from filing date"""
        try:
            date_obj = datetime.strptime(filing_date, '%Y-%m-%d')
            month = date_obj.month
            return f"Q{(month - 1) // 3 + 1}"
        except:
            return "Unknown"
    
    def _get_year(self, filing_date: str) -> int:
        """Extract year from filing date"""
        try:
            return int(filing_date.split('-')[0])
        except:
            return 0
    
    def save_dataset(self, ticker: str, df: pd.DataFrame):
        """Save clean dataset"""
        if df.empty:
            return
        
        # Save as CSV (easy to analyze)
        csv_file = os.path.join(self.output_dir, f"{ticker}_simple.csv")
        df.to_csv(csv_file, index=False)
        
        # Save as JSON (complete data)
        json_file = os.path.join(self.output_dir, f"{ticker}_simple.json")
        df.to_json(json_file, orient='records', indent=2)
        
        print(f"   💾 Saved: {csv_file}")
        print(f"   💾 Saved: {json_file}")
    
    def process_all_tickers(self):
        """Process all cached tickers"""
        tickers = [d for d in os.listdir(self.cache_dir) 
                  if os.path.isdir(os.path.join(self.cache_dir, d)) and d != '__pycache__']
        
        print(f"🚀 Processing {len(tickers)} tickers: {', '.join(tickers)}")
        
        all_data = []
        
        for ticker in tickers:
            df = self.process_ticker(ticker)
            if not df.empty:
                self.save_dataset(ticker, df)
                all_data.append(df)
        
        # Create combined dataset
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            combined_file = os.path.join(self.output_dir, "all_tickers_combined.csv")
            combined_df.to_csv(combined_file, index=False)
            print(f"\n💾 Combined dataset: {combined_file}")
        
        print(f"\n✅ Processing completed!")
    
    def analyze_ticker(self, ticker: str):
        """Quick analysis of a ticker's data"""
        df = self.process_ticker(ticker)
        
        if df.empty:
            print(f"❌ No data for {ticker}")
            return
        
        print(f"\n📊 Analysis for {ticker}:")
        print(f"   Quarters: {len(df)}")
        print(f"   Date range: {df['filing_date'].min()} to {df['filing_date'].max()}")
        
        # Show revenue trend
        revenue_data = df.dropna(subset=['revenue'])
        if len(revenue_data) > 0:
            print(f"\n💰 Revenue Trend:")
            for _, row in revenue_data.head(4).iterrows():
                revenue_m = row['revenue'] / 1000000 if row['revenue'] else 0
                print(f"   {row['quarter']} {row['year']}: ${revenue_m:.1f}M")
        
        # Show cash flow
        cf_data = df.dropna(subset=['operating_cash_flow'])
        if len(cf_data) > 0:
            print(f"\n💸 Operating Cash Flow:")
            for _, row in cf_data.head(4).iterrows():
                cf_m = row['operating_cash_flow'] / 1000000 if row['operating_cash_flow'] else 0
                print(f"   {row['quarter']} {row['year']}: ${cf_m:.1f}M")
        
        return df


def main():
    """Simple main function"""
    processor = SimpleXBRLProcessor()
    
    # Quick demo with one ticker
    print("🔍 Testing with Realty Income (O)...")
    df = processor.analyze_ticker("O")
    
    if not df.empty:
        processor.save_dataset("O", df)
        
        print(f"\n📋 Sample data:")
        print(df[['quarter', 'year', 'revenue', 'operating_cash_flow']].head())
    
    # Uncomment to process all tickers
    # print(f"\n🌍 Processing all tickers...")
    # processor.process_all_tickers()


if __name__ == "__main__":
    main()