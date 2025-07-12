# concept_analyzer.py - Analyze and compare XBRL concepts between companies

import pandas as pd
import os
from typing import Dict, List, Set, Tuple
from collections import Counter
import re


class XBRLConceptAnalyzer:
    """Analyze XBRL concepts across different companies to find common patterns"""
    
    def __init__(self):
        self.company_concepts = {}
        self.company_data = {}
    
    def load_company_data(self, ticker: str, csv_file_path: str) -> bool:
        """Load CSV data for a company"""
        try:
            df = pd.read_csv(csv_file_path)
            self.company_data[ticker] = df
            
            # Extract unique concepts
            if 'concept' in df.columns:
                concepts = set(df['concept'].dropna().unique())
                self.company_concepts[ticker] = concepts
                print(f"✅ Loaded {ticker}: {len(df)} facts, {len(concepts)} unique concepts")
                return True
            else:
                print(f"❌ No 'concept' column found in {csv_file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error loading {csv_file_path}: {e}")
            return False
    
    def find_common_concepts(self) -> Set[str]:
        """Find concepts that appear in ALL loaded companies"""
        if not self.company_concepts:
            return set()
        
        # Find intersection of all company concepts
        common_concepts = set.intersection(*self.company_concepts.values())
        return common_concepts
    
    def categorize_concepts(self, concepts: Set[str]) -> Dict[str, List[str]]:
        """Categorize concepts by financial statement type"""
        categories = {
            'Revenue & Income': [],
            'Balance Sheet - Assets': [],
            'Balance Sheet - Liabilities': [],
            'Balance Sheet - Equity': [],
            'Cash Flow': [],
            'Share Information': [],
            'Other': []
        }
        
        # Define patterns for each category
        patterns = {
            'Revenue & Income': [
                r'revenue', r'income', r'earning', r'profit', r'loss', r'expense', r'cost'
            ],
            'Balance Sheet - Assets': [
                r'assets?$', r'cash', r'receivable', r'inventory', r'property', r'equipment', r'investment'
            ],
            'Balance Sheet - Liabilities': [
                r'liabilities?$', r'debt', r'payable', r'accrued', r'deferred.*liab'
            ],
            'Balance Sheet - Equity': [
                r'equity', r'stockholder', r'shareholder', r'retained.*earning', r'capital'
            ],
            'Cash Flow': [
                r'cash.*flow', r'cash.*provided', r'cash.*used', r'cash.*operating', r'cash.*investing', r'cash.*financing'
            ],
            'Share Information': [
                r'shares?.*outstanding', r'shares?.*issued', r'weighted.*average.*shares?', r'earnings.*per.*share'
            ]
        }
        
        for concept in concepts:
            concept_lower = concept.lower()
            categorized = False
            
            for category, category_patterns in patterns.items():
                for pattern in category_patterns:
                    if re.search(pattern, concept_lower):
                        categories[category].append(concept)
                        categorized = True
                        break
                if categorized:
                    break
            
            if not categorized:
                categories['Other'].append(concept)
        
        return categories
    
    def analyze_concept_usage(self, concept: str) -> Dict[str, Dict]:
        """Analyze how a specific concept is used across companies"""
        analysis = {}
        
        for ticker, df in self.company_data.items():
            concept_data = df[df['concept'] == concept].copy()
            
            if len(concept_data) > 0:
                analysis[ticker] = {
                    'occurrences': len(concept_data),
                    'unique_values': len(concept_data['numeric_value'].dropna().unique()),
                    'period_types': list(concept_data['period_type'].dropna().unique()) if 'period_type' in concept_data.columns else [],
                    'statement_types': list(concept_data['statement_type'].dropna().unique()) if 'statement_type' in concept_data.columns else [],
                    'sample_value': concept_data['numeric_value'].dropna().iloc[0] if len(concept_data['numeric_value'].dropna()) > 0 else None,
                    'sample_period': concept_data['period_end'].dropna().iloc[0] if 'period_end' in concept_data.columns and len(concept_data['period_end'].dropna()) > 0 else None
                }
        
        return analysis
    
    def get_key_financial_concepts(self, common_concepts: Set[str]) -> Dict[str, str]:
        """Identify the most important financial concepts for extraction"""
        
        # Key financial metrics we want to find
        target_metrics = {
            'revenue': ['revenue', 'sales'],
            'net_income': ['netincomeloss', 'netincome'],
            'total_assets': ['assets$'],
            'total_liabilities': ['liabilities$'],
            'stockholders_equity': ['stockholdersequity', 'shareholdersequity'],
            'cash_and_equivalents': ['cashandcashequivalents'],
            'operating_cash_flow': ['netcashprovidedbyusedinfromoperatingactivities', 'operatingcashflow'],
            'earnings_per_share': ['earningspershare'],
            'shares_outstanding': ['commonstocksharesoutstanding', 'sharesoutstanding']
        }
        
        key_concepts = {}
        
        for metric, search_terms in target_metrics.items():
            best_match = None
            
            for concept in common_concepts:
                concept_clean = re.sub(r'[^a-zA-Z]', '', concept.lower())
                
                for term in search_terms:
                    if re.search(term, concept_clean):
                        # Prefer exact matches or simpler concept names
                        if not best_match or len(concept) < len(best_match):
                            best_match = concept
                        break
            
            if best_match:
                key_concepts[metric] = best_match
        
        return key_concepts
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report"""
        if not self.company_concepts:
            return "No data loaded for analysis."
        
        report = []
        report.append("🔍 XBRL CONCEPT ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Company overview
        report.append(f"\n📊 COMPANIES ANALYZED:")
        for ticker, concepts in self.company_concepts.items():
            total_facts = len(self.company_data[ticker])
            report.append(f"   {ticker}: {len(concepts)} unique concepts, {total_facts} total facts")
        
        # Common concepts
        common_concepts = self.find_common_concepts()
        report.append(f"\n🤝 COMMON CONCEPTS ACROSS ALL COMPANIES: {len(common_concepts)}")
        
        if common_concepts:
            # Categorize common concepts
            categories = self.categorize_concepts(common_concepts)
            
            for category, concepts in categories.items():
                if concepts:
                    report.append(f"\n📋 {category.upper()} ({len(concepts)} concepts):")
                    for concept in sorted(concepts):  # Show ALL concepts, no limit
                        report.append(f"   • {concept}")
            
            # Key financial concepts
            key_concepts = self.get_key_financial_concepts(common_concepts)
            report.append(f"\n🎯 KEY FINANCIAL CONCEPTS FOR EXTRACTION:")
            for metric, concept in key_concepts.items():
                report.append(f"   {metric}: {concept}")
                
                # Show usage analysis for key concepts
                usage = self.analyze_concept_usage(concept)
                for ticker, info in usage.items():
                    sample_val = info['sample_value']
                    if sample_val and abs(sample_val) > 1000:
                        if abs(sample_val) >= 1e9:
                            formatted_val = f"${sample_val/1e9:.1f}B"
                        elif abs(sample_val) >= 1e6:
                            formatted_val = f"${sample_val/1e6:.1f}M"
                        else:
                            formatted_val = f"${sample_val:,.0f}"
                    else:
                        formatted_val = str(sample_val)
                    
                    report.append(f"      {ticker}: {formatted_val} ({info['period_types']})")
        
        else:
            report.append("   ❌ No concepts are common across all companies")
            
            # Show unique concepts per company
            report.append(f"\n📊 UNIQUE CONCEPTS PER COMPANY:")
            for ticker in self.company_concepts.keys():
                unique_to_ticker = self.company_concepts[ticker]
                for other_ticker in self.company_concepts.keys():
                    if other_ticker != ticker:
                        unique_to_ticker = unique_to_ticker - self.company_concepts[other_ticker]
                
                report.append(f"   {ticker} only: {len(unique_to_ticker)} concepts")
        
        return "\n".join(report)


def main():
    """Main function to run the concept analysis"""
    
    analyzer = XBRLConceptAnalyzer()
    
    # Try to load AAPL and MSFT data
    companies_to_analyze = [
        ("AAPL", "exports/AAPL/AAPL_2023_Q1_raw_facts.csv"),
        ("MSFT", "exports/MSFT/MSFT_2023_Q1_raw_facts.csv")
    ]
    
    print("🔍 Loading company data...")
    
    loaded_count = 0
    for ticker, file_path in companies_to_analyze:
        if os.path.exists(file_path):
            if analyzer.load_company_data(ticker, file_path):
                loaded_count += 1
        else:
            print(f"⚠️ File not found: {file_path}")
    
    if loaded_count < 2:
        print("❌ Need at least 2 companies to compare. Please check file paths.")
        print("Expected files:")
        for ticker, file_path in companies_to_analyze:
            print(f"   {file_path}")
        return
    
    # Generate and print report
    report = analyzer.generate_report()
    print(f"\n{report}")
    
    # Save report to file
    with open("xbrl_concept_analysis.txt", "w") as f:
        f.write(report)
    
    print(f"\n💾 Full report saved to: xbrl_concept_analysis.txt")


if __name__ == "__main__":
    main()