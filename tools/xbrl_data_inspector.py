# tools/xbrl_data_inspector.py - Inspect raw XBRL cache files

import json
import os
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime


class XBRLDataInspector:
    """Inspect and analyze raw XBRL cache files"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
    
    def inspect_ticker_cache(self, ticker: str):
        """Inspect all cached files for a ticker"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            print(f"❌ No cache directory found for {ticker}")
            return
        
        print(f"🔍 Inspecting cache for {ticker}")
        print("=" * 50)
        
        # Check metadata first
        metadata_path = os.path.join(ticker_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            print(f"📋 Metadata Summary:")
            print(f"   Company: {metadata.get('company_name', 'Unknown')}")
            print(f"   Total Quarters: {metadata.get('total_quarters_cached', 0)}")
            print(f"   Last Updated: {metadata.get('last_updated', 'Unknown')}")
            print()
        
        # List all quarter files
        quarter_files = [f for f in os.listdir(ticker_dir) if f.endswith('.json') and f != 'metadata.json']
        quarter_files.sort()
        
        print(f"📄 Found {len(quarter_files)} quarter files:")
        for file in quarter_files:
            file_path = os.path.join(ticker_dir, file)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"   📄 {file} ({file_size:.2f}MB)")
        
        return quarter_files
    
    def examine_quarter_file(self, ticker: str, quarter_file: str):
        """Examine a specific quarter file in detail"""
        ticker = ticker.upper()
        file_path = os.path.join(self.cache_dir, ticker, quarter_file)
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        print(f"\n🔬 Examining: {quarter_file}")
        print("=" * 60)
        
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
        
        # Basic structure analysis
        print(f"📊 File Structure:")
        for key, value in raw_data.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"   {key}: <large string> ({len(value)} chars)")
            elif isinstance(value, list):
                print(f"   {key}: <list> ({len(value)} items)")
            elif isinstance(value, dict):
                print(f"   {key}: <dict> ({len(value)} keys)")
            else:
                print(f"   {key}: {value}")
        
        # Examine facts_json if present
        if raw_data.get('facts_json'):
            print(f"\n📈 Facts Data Analysis:")
            try:
                facts_df = pd.read_json(raw_data['facts_json'])
                print(f"   Total Facts: {len(facts_df)}")
                print(f"   Columns: {list(facts_df.columns)}")
                
                # Show concept distribution
                if 'concept' in facts_df.columns:
                    concept_counts = facts_df['concept'].value_counts().head(10)
                    print(f"\n   Top 10 Concepts:")
                    for concept, count in concept_counts.items():
                        print(f"      {concept}: {count}")
                
                # Show sample facts
                print(f"\n   Sample Facts (first 5):")
                sample_facts = facts_df.head(5)
                for idx, row in sample_facts.iterrows():
                    concept = row.get('concept', 'Unknown')
                    value = row.get('value', row.get('numeric_value', 'N/A'))
                    period = row.get('period', 'Unknown')
                    print(f"      {concept}: {value} ({period})")
                
            except Exception as e:
                print(f"   ❌ Error analyzing facts: {e}")
        
        # Examine dimensions if present
        if raw_data.get('dimensions_json'):
            print(f"\n🔍 Dimensions Analysis:")
            try:
                dimensions = json.loads(raw_data['dimensions_json'])
                print(f"   Total Dimensions: {len(dimensions)}")
                for dim_name, dim_data in dimensions.items():
                    values_count = dim_data.get('count', 0)
                    print(f"      {dim_name}: {values_count} values")
                    if values_count <= 5:  # Show values if few
                        values = dim_data.get('values', [])
                        print(f"         Values: {values}")
            except Exception as e:
                print(f"   ❌ Error analyzing dimensions: {e}")
        
        # Examine statements info if present
        if raw_data.get('statements_info'):
            print(f"\n📈 Statements Analysis:")
            statements = raw_data['statements_info']
            available = statements.get('available_statements', [])
            print(f"   Available Statements: {len(available)}")
            for stmt in available:
                print(f"      📋 {stmt}")
        
        return raw_data
    
    def find_financial_concepts(self, ticker: str, quarter_file: str):
        """Find and extract key financial concepts from a quarter file"""
        raw_data = self.examine_quarter_file(ticker, quarter_file)
        
        if not raw_data or not raw_data.get('facts_json'):
            print(f"❌ No facts data available")
            return {}
        
        try:
            facts_df = pd.read_json(raw_data['facts_json'])
            
            # Key financial concepts to look for
            financial_concepts = {
                'revenue': ['Revenues', 'Revenue', 'SalesRevenueNet', 'PropertyIncome', 'RentalIncome'],
                'operating_cash_flow': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByOperatingActivities'],
                'net_income': ['NetIncomeLoss', 'NetIncome', 'ProfitLoss'],
                'total_assets': ['Assets', 'TotalAssets'],
                'total_liabilities': ['Liabilities', 'TotalLiabilities']
            }
            
            found_concepts = {}
            
            print(f"\n💰 Financial Concepts Found:")
            
            for category, concepts in financial_concepts.items():
                found_values = []
                for concept in concepts:
                    concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
                    if len(concept_rows) > 0:
                        for _, row in concept_rows.iterrows():
                            value = row.get('value', row.get('numeric_value', None))
                            period = row.get('period', 'Unknown')
                            if value is not None:
                                try:
                                    numeric_value = float(value)
                                    found_values.append({
                                        'concept': row['concept'],
                                        'value': numeric_value,
                                        'period': period,
                                        'formatted_value': f"${numeric_value:,.0f}" if numeric_value > 1000 else str(numeric_value)
                                    })
                                except:
                                    pass
                
                if found_values:
                    found_concepts[category] = found_values
                    print(f"   {category.upper()}:")
                    for item in found_values[:3]:  # Show first 3
                        print(f"      {item['concept']}: {item['formatted_value']} ({item['period']})")
                    if len(found_values) > 3:
                        print(f"      ... and {len(found_values) - 3} more")
            
            return found_concepts
            
        except Exception as e:
            print(f"❌ Error finding financial concepts: {e}")
            return {}
    
    def compare_quarters(self, ticker: str):
        """Compare financial data across all quarters for a ticker"""
        quarter_files = self.inspect_ticker_cache(ticker)
        
        if not quarter_files:
            return
        
        print(f"\n📊 Comparing Financial Data Across Quarters:")
        print("=" * 60)
        
        all_quarters_data = {}
        
        for quarter_file in quarter_files:
            print(f"\n🔍 Processing {quarter_file}...")
            concepts = self.find_financial_concepts(ticker, quarter_file)
            
            quarter_name = quarter_file.replace('.json', '')
            all_quarters_data[quarter_name] = concepts
        
        # Create comparison table
        print(f"\n📈 Revenue Comparison:")
        print(f"{'Quarter':<15} {'Revenue Concept':<30} {'Value':<15}")
        print("-" * 60)
        
        for quarter, data in all_quarters_data.items():
            revenue_data = data.get('revenue', [])
            if revenue_data:
                best_revenue = max(revenue_data, key=lambda x: abs(x['value']) if x['value'] else 0)
                print(f"{quarter:<15} {best_revenue['concept'][:30]:<30} {best_revenue['formatted_value']:<15}")
            else:
                print(f"{quarter:<15} {'No revenue data':<30} {'N/A':<15}")


def inspect_realty_income_example():
    """Inspect Realty Income (O) as an example"""
    inspector = XBRLDataInspector()
    
    print("🏢 Inspecting Realty Income (O) XBRL Data")
    print("=" * 50)
    
    # Check if O cache exists
    ticker = "O"
    quarter_files = inspector.inspect_ticker_cache(ticker)
    
    if not quarter_files:
        print(f"❌ No cache data found for {ticker}")
        print("💡 Run the app and search for 'O' to cache the data first")
        return
    
    # Find the 2025_Q2 file if it exists
    q2_2025_file = None
    for file in quarter_files:
        if "2025_Q2" in file:
            q2_2025_file = file
            break
    
    if q2_2025_file:
        print(f"\n🎯 Found 2025 Q2 file: {q2_2025_file}")
        raw_data = inspector.examine_quarter_file(ticker, q2_2025_file)
        concepts = inspector.find_financial_concepts(ticker, q2_2025_file)
    else:
        print(f"\n⚠️ 2025_Q2_10Q.json not found, examining most recent file...")
        if quarter_files:
            latest_file = quarter_files[-1]  # Assuming sorted
            raw_data = inspector.examine_quarter_file(ticker, latest_file)
            concepts = inspector.find_financial_concepts(ticker, latest_file)
    
    # Compare all quarters
    inspector.compare_quarters(ticker)
    
    return raw_data


if __name__ == "__main__":
    # Run the inspection
    inspect_realty_income_example()