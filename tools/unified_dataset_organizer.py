# tools/unified_dataset_organizer.py - Convert raw XBRL cache to unified datasets (EdgarTools best practices)

import json
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import io
import numpy as np


class EdgarToolsUniversalOrganizer:
    """Universal dataset organizer following EdgarTools best practices"""
    
    def __init__(self, cache_dir: str = "data/cache", output_dir: str = "data/unified"):
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Standard financial concepts following EdgarTools patterns
        self.financial_concepts = {
            'revenue': {
                'us_gaap_concepts': [
                    'us-gaap:Revenues',
                    'us-gaap:Revenue', 
                    'us-gaap:SalesRevenueNet',
                    'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax'
                ],
                'common_variations': [
                    'Revenues', 'Revenue', 'SalesRevenueNet', 'TotalRevenues',
                    'PropertyIncome', 'RentalIncome', 'RentalRevenue'  # REIT-specific
                ]
            },
            'operating_cash_flow': {
                'us_gaap_concepts': [
                    'us-gaap:NetCashProvidedByUsedInOperatingActivities',
                    'us-gaap:NetCashProvidedByOperatingActivities'
                ],
                'common_variations': [
                    'NetCashProvidedByUsedInOperatingActivities',
                    'NetCashProvidedByOperatingActivities',
                    'CashFlowFromOperatingActivities'
                ]
            },
            'net_income': {
                'us_gaap_concepts': [
                    'us-gaap:NetIncomeLoss',
                    'us-gaap:ProfitLoss'
                ],
                'common_variations': [
                    'NetIncomeLoss', 'NetIncome', 'ProfitLoss',
                    'IncomeLossFromContinuingOperations'
                ]
            },
            'total_assets': {
                'us_gaap_concepts': [
                    'us-gaap:Assets'
                ],
                'common_variations': [
                    'Assets', 'TotalAssets'
                ]
            },
            'total_liabilities': {
                'us_gaap_concepts': [
                    'us-gaap:Liabilities'
                ],
                'common_variations': [
                    'Liabilities', 'TotalLiabilities'
                ]
            },
            'stockholders_equity': {
                'us_gaap_concepts': [
                    'us-gaap:StockholdersEquity'
                ],
                'common_variations': [
                    'StockholdersEquity', 'ShareholdersEquity', 'TotalEquity'
                ]
            },
            'shares_outstanding': {
                'us_gaap_concepts': [
                    'us-gaap:CommonStockSharesOutstanding',
                    'us-gaap:WeightedAverageNumberOfSharesOutstandingBasic'
                ],
                'common_variations': [
                    'CommonStockSharesOutstanding',
                    'WeightedAverageNumberOfSharesOutstandingBasic',
                    'SharesOutstanding'
                ]
            }
        }
    
    def process_ticker_edgartools_style(self, ticker: str) -> Dict[str, Any]:
        """Process ticker using EdgarTools-style XBRL data extraction"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            print(f"❌ No cache found for {ticker}")
            return {}
        
        print(f"🔄 Processing {ticker} using EdgarTools patterns...")
        
        # Load metadata
        metadata = self._load_metadata(ticker_dir)
        
        # Get all quarter files
        quarter_files = [f for f in os.listdir(ticker_dir) 
                        if f.endswith('.json') and f != 'metadata.json']
        quarter_files.sort()
        
        unified_data = {
            'ticker': ticker,
            'company_name': metadata.get('company_name', f"{ticker} Corporation"),
            'processing_method': 'EdgarTools-style XBRL extraction',
            'last_updated': metadata.get('last_updated', datetime.now().isoformat()),
            'quarters': [],
            'facts_analysis': {},
            'dimensions_analysis': {},
            'data_quality': {}
        }
        
        all_quarters = []
        all_facts = []  # Collect all facts for analysis
        all_dimensions = []
        
        # Process each quarter
        for quarter_file in quarter_files:
            quarter_data = self._process_quarter_edgartools_style(ticker_dir, quarter_file)
            if quarter_data:
                all_quarters.append(quarter_data)
                
                # Collect facts for universal analysis
                if quarter_data.get('raw_facts'):
                    all_facts.extend(quarter_data['raw_facts'])
                
                if quarter_data.get('dimensions_data'):
                    all_dimensions.append(quarter_data['dimensions_data'])
        
        # Sort quarters by date (most recent first)
        all_quarters.sort(key=lambda x: x['filing_date'], reverse=True)
        unified_data['quarters'] = all_quarters
        
        # Analyze all facts across quarters (EdgarTools style)
        if all_facts:
            unified_data['facts_analysis'] = self._analyze_facts_edgartools_style(all_facts)
            unified_data['concept_discovery'] = self._discover_unique_concepts(all_facts, ticker)
        
        # Analyze dimensions
        if all_dimensions:
            unified_data['dimensions_analysis'] = self._analyze_dimensions_universal(all_dimensions)
        
        # Calculate data quality
        unified_data['data_quality'] = self._calculate_edgartools_quality(all_quarters, all_facts)
        
        return unified_data
    
    def _process_quarter_edgartools_style(self, ticker_dir: str, quarter_file: str) -> Optional[Dict[str, Any]]:
        """Process single quarter following EdgarTools patterns"""
        file_path = os.path.join(ticker_dir, quarter_file)
        
        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
            
            quarter_data = {
                'filing_date': raw_data.get('filing_date', ''),
                'quarter': self._extract_quarter(raw_data.get('filing_date', '')),
                'year': self._extract_year(raw_data.get('filing_date', '')),
                'form_type': raw_data.get('form_type', '10-Q'),
                'xbrl_object_type': raw_data.get('xbrl_object_type', 'unknown'),
                'extraction_timestamp': raw_data.get('extraction_timestamp', ''),
                'financials': {},
                'raw_facts': [],
                'dimensions_data': {},
                'statements_summary': {},
                'extraction_metadata': {
                    'total_facts_count': raw_data.get('total_facts_count', 0),
                    'dimensions_count': raw_data.get('dimensions_count', 0),
                    'file_size_mb': raw_data.get('original_xbrl_size_estimate', 0)
                }
            }
            
            # Process facts using EdgarTools approach
            if raw_data.get('facts_json'):
                facts_df = pd.read_json(raw_data['facts_json'])
                
                # Store raw facts for analysis
                quarter_data['raw_facts'] = facts_df.to_dict('records')
                
                # Extract financial metrics using EdgarTools patterns
                quarter_data['financials'] = self._extract_financials_edgartools_style(facts_df)
                
                # Analyze facts structure
                quarter_data['facts_structure'] = self._analyze_facts_structure(facts_df)
            
            # Process dimensions
            if raw_data.get('dimensions_json'):
                dimensions = json.loads(raw_data['dimensions_json'])
                quarter_data['dimensions_data'] = dimensions
                quarter_data['dimensions_summary'] = self._summarize_dimensions(dimensions)
            
            # Process statements info
            if raw_data.get('statements_info'):
                quarter_data['statements_summary'] = raw_data['statements_info']
            
            return quarter_data
            
        except Exception as e:
            print(f"   ❌ Error processing {quarter_file}: {e}")
            return None
    
    def _extract_financials_edgartools_style(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract financials following EdgarTools best practices"""
        financials = {}
        
        # Group facts by concept for easier analysis
        concept_groups = facts_df.groupby('concept')
        
        # Extract each financial metric
        for metric, config in self.financial_concepts.items():
            result = self._find_best_financial_value_edgartools(
                concept_groups, 
                config['us_gaap_concepts'], 
                config['common_variations'],
                metric
            )
            financials[metric] = result
        
        # Calculate derived metrics
        financials.update(self._calculate_derived_metrics_edgartools(financials))
        
        # Add industry-specific metrics based on discovered concepts
        financials.update(self._extract_industry_metrics_edgartools(facts_df))
        
        return financials
    
    def _find_best_financial_value_edgartools(self, concept_groups, us_gaap_concepts: List[str], 
                                            variations: List[str], metric_name: str) -> Dict[str, Any]:
        """Find best financial value using EdgarTools prioritization"""
        result = {
            'value': None,
            'concept_used': None,
            'period': None,
            'unit': None,
            'context': None,
            'confidence_score': 0,
            'extraction_method': 'edgartools_style',
            'alternatives': []
        }
        
        # Priority 1: US-GAAP standardized concepts
        for concept in us_gaap_concepts:
            if concept in concept_groups.groups:
                group_df = concept_groups.get_group(concept)
                best_fact = self._select_best_fact_edgartools(group_df, metric_name)
                
                if best_fact is not None:
                    value = self._extract_numeric_value_safe(best_fact)
                    if value is not None:
                        result.update({
                            'value': value,
                            'concept_used': concept,
                            'period': best_fact.get('period', 'Unknown'),
                            'unit': best_fact.get('unit', 'Unknown'),
                            'context': best_fact.get('context', 'Unknown'),
                            'confidence_score': 10,  # Highest for US-GAAP
                        })
                        return result
        
        # Priority 2: Common variations (without us-gaap prefix)
        for variation in variations:
            matching_concepts = [name for name in concept_groups.groups.keys() 
                               if variation.lower() in name.lower()]
            
            for concept in matching_concepts:
                group_df = concept_groups.get_group(concept)
                best_fact = self._select_best_fact_edgartools(group_df, metric_name)
                
                if best_fact is not None:
                    value = self._extract_numeric_value_safe(best_fact)
                    if value is not None:
                        # Store as alternative if we already have a result
                        fact_info = {
                            'value': value,
                            'concept_used': concept,
                            'period': best_fact.get('period', 'Unknown'),
                            'confidence_score': 8  # High for common variations
                        }
                        
                        if result['value'] is None:
                            result.update(fact_info)
                        else:
                            result['alternatives'].append(fact_info)
        
        # Priority 3: Fuzzy matching for similar concepts
        if result['value'] is None:
            fuzzy_result = self._fuzzy_match_concept_edgartools(concept_groups, metric_name)
            if fuzzy_result:
                result.update(fuzzy_result)
                result['confidence_score'] = 6  # Lower confidence for fuzzy matching
        
        return result
    
    def _select_best_fact_edgartools(self, facts_df: pd.DataFrame, metric_name: str) -> Optional[Dict[str, Any]]:
        """Select best fact from multiple options using EdgarTools logic"""
        if len(facts_df) == 0:
            return None
        
        # Prefer facts with period information
        facts_with_period = facts_df.dropna(subset=['period'])
        if len(facts_with_period) > 0:
            facts_df = facts_with_period
        
        # For cash flow metrics, prefer quarterly periods
        if 'cash' in metric_name.lower() or 'flow' in metric_name.lower():
            quarterly_facts = facts_df[facts_df['period'].str.contains('3M|Q[1-4]', case=False, na=False)]
            if len(quarterly_facts) > 0:
                facts_df = quarterly_facts
        
        # For balance sheet metrics, prefer point-in-time (end of period)
        if metric_name in ['total_assets', 'total_liabilities', 'stockholders_equity']:
            instant_facts = facts_df[facts_df['period'].str.contains('instant|as of', case=False, na=False)]
            if len(instant_facts) > 0:
                facts_df = instant_facts
        
        # Select most recent fact
        return facts_df.iloc[-1].to_dict()
    
    def _fuzzy_match_concept_edgartools(self, concept_groups, metric_name: str) -> Optional[Dict[str, Any]]:
        """Fuzzy match concepts using EdgarTools-style pattern matching"""
        fuzzy_patterns = {
            'revenue': ['income', 'sales', 'rental', 'property', 'service'],
            'operating_cash_flow': ['cash', 'operating', 'activities'],
            'net_income': ['income', 'profit', 'earnings', 'loss'],
            'total_assets': ['assets', 'total'],
            'total_liabilities': ['liabilities', 'total'],
            'stockholders_equity': ['equity', 'stockholder', 'shareholder']
        }
        
        patterns = fuzzy_patterns.get(metric_name, [])
        if not patterns:
            return None
        
        # Find concepts that match multiple patterns
        for concept_name in concept_groups.groups.keys():
            concept_lower = concept_name.lower()
            matches = sum(1 for pattern in patterns if pattern in concept_lower)
            
            if matches >= 2:  # Require at least 2 pattern matches
                group_df = concept_groups.get_group(concept_name)
                best_fact = self._select_best_fact_edgartools(group_df, metric_name)
                
                if best_fact is not None:
                    value = self._extract_numeric_value_safe(best_fact)
                    if value is not None:
                        return {
                            'value': value,
                            'concept_used': concept_name,
                            'period': best_fact.get('period', 'Unknown'),
                            'extraction_method': 'fuzzy_match'
                        }
        
        return None
    
    def _calculate_derived_metrics_edgartools(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate derived metrics using EdgarTools approach"""
        derived = {}
        
        # Free Cash Flow (OCF - CapEx, simplified as OCF for now)
        ocf = financials.get('operating_cash_flow', {}).get('value')
        if ocf is not None:
            derived['free_cash_flow'] = {
                'value': ocf,  # Simplified - would need CapEx for true FCF
                'concept_used': 'Calculated from Operating Cash Flow',
                'calculation': 'Operating Cash Flow (CapEx not available)',
                'confidence_score': 7
            }
        
        # Return on Assets
        net_income = financials.get('net_income', {}).get('value')
        total_assets = financials.get('total_assets', {}).get('value')
        
        if net_income is not None and total_assets is not None and total_assets != 0:
            roa = net_income / total_assets
            derived['return_on_assets'] = {
                'value': roa,
                'concept_used': 'Calculated (Net Income / Total Assets)',
                'calculation': f'{net_income} / {total_assets}',
                'confidence_score': 9
            }
        
        # Debt to Assets Ratio
        liabilities = financials.get('total_liabilities', {}).get('value')
        if liabilities is not None and total_assets is not None and total_assets != 0:
            debt_ratio = liabilities / total_assets
            derived['debt_to_assets_ratio'] = {
                'value': debt_ratio,
                'concept_used': 'Calculated (Total Liabilities / Total Assets)',
                'calculation': f'{liabilities} / {total_assets}',
                'confidence_score': 9
            }
        
        # Equity Ratio
        equity = financials.get('stockholders_equity', {}).get('value')
        if equity is not None and total_assets is not None and total_assets != 0:
            equity_ratio = equity / total_assets
            derived['equity_ratio'] = {
                'value': equity_ratio,
                'concept_used': 'Calculated (Stockholders Equity / Total Assets)',
                'calculation': f'{equity} / {total_assets}',
                'confidence_score': 9
            }
        
        return derived
    
    def _extract_industry_metrics_edgartools(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract industry-specific metrics using EdgarTools patterns"""
        industry_metrics = {}
        concept_groups = facts_df.groupby('concept')
        
        # REIT-specific metrics
        reit_concepts = {
            'funds_from_operations': ['FundsFromOperations', 'FFO'],
            'adjusted_funds_from_operations': ['AdjustedFundsFromOperations', 'AFFO'],
            'same_store_noi': ['SameStoreNetOperatingIncome', 'SameStoreNOI'],
            'occupancy_rate': ['OccupancyRate', 'Occupancy']
        }
        
        for metric, concepts in reit_concepts.items():
            for concept in concepts:
                matching = [name for name in concept_groups.groups.keys() 
                          if concept.lower() in name.lower()]
                
                if matching:
                    best_concept = matching[0]  # Take first match
                    group_df = concept_groups.get_group(best_concept)
                    best_fact = self._select_best_fact_edgartools(group_df, metric)
                    
                    if best_fact:
                        value = self._extract_numeric_value_safe(best_fact)
                        if value is not None:
                            industry_metrics[f'reit_{metric}'] = {
                                'value': value,
                                'concept_used': best_concept,
                                'period': best_fact.get('period', 'Unknown'),
                                'industry': 'REIT',
                                'confidence_score': 8
                            }
                            break
        
        # Banking metrics
        bank_concepts = {
            'interest_income': ['InterestIncome'],
            'interest_expense': ['InterestExpense'],
            'net_interest_income': ['NetInterestIncome'],
            'provision_for_loan_losses': ['ProvisionForLoanLosses']
        }
        
        for metric, concepts in bank_concepts.items():
            for concept in concepts:
                matching = [name for name in concept_groups.groups.keys() 
                          if concept.lower() in name.lower()]
                
                if matching:
                    best_concept = matching[0]
                    group_df = concept_groups.get_group(best_concept)
                    best_fact = self._select_best_fact_edgartools(group_df, metric)
                    
                    if best_fact:
                        value = self._extract_numeric_value_safe(best_fact)
                        if value is not None:
                            industry_metrics[f'bank_{metric}'] = {
                                'value': value,
                                'concept_used': best_concept,
                                'period': best_fact.get('period', 'Unknown'),
                                'industry': 'Banking',
                                'confidence_score': 8
                            }
                            break
        
        return industry_metrics
    
    def _analyze_facts_edgartools_style(self, all_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze facts across all quarters using EdgarTools approach"""
        if not all_facts:
            return {}
        
        facts_df = pd.DataFrame(all_facts)
        
        # Concept frequency analysis
        concept_counts = facts_df['concept'].value_counts()
        
        # Unit analysis
        unit_analysis = {}
        if 'unit' in facts_df.columns:
            unit_counts = facts_df['unit'].value_counts()
            unit_analysis = {
                'total_units': len(unit_counts),
                'common_units': unit_counts.head(10).to_dict(),
                'currencies_detected': [unit for unit in unit_counts.index if 'USD' in str(unit)]
            }
        
        # Period analysis
        period_analysis = {}
        if 'period' in facts_df.columns:
            period_counts = facts_df['period'].value_counts()
            period_analysis = {
                'total_periods': len(period_counts),
                'period_types': period_counts.head(10).to_dict()
            }
        
        return {
            'total_facts': len(all_facts),
            'unique_concepts': len(concept_counts),
            'top_concepts': concept_counts.head(20).to_dict(),
            'unit_analysis': unit_analysis,
            'period_analysis': period_analysis,
            'data_types_found': list(facts_df.dtypes.to_dict().keys())
        }
    
    def _discover_unique_concepts(self, all_facts: List[Dict[str, Any]], ticker: str) -> Dict[str, Any]:
        """Discover unique/interesting concepts for this company"""
        if not all_facts:
            return {}
        
        facts_df = pd.DataFrame(all_facts)
        
        # Find concepts that might be unique to this company/industry
        concept_counts = facts_df['concept'].value_counts()
        
        # Look for industry-specific patterns
        industry_indicators = {
            'REIT': ['property', 'rental', 'real estate', 'occupancy', 'funds from operations'],
            'Bank': ['interest', 'loan', 'deposit', 'credit', 'provision'],
            'Insurance': ['premium', 'claim', 'reserve', 'underwriting'],
            'Utility': ['electric', 'gas', 'utility', 'rate', 'regulatory'],
            'Tech': ['software', 'subscription', 'license', 'platform'],
            'Retail': ['store', 'same store', 'inventory', 'merchandise']
        }
        
        detected_industries = []
        for industry, indicators in industry_indicators.items():
            for indicator in indicators:
                matching_concepts = [concept for concept in concept_counts.index 
                                   if indicator.lower() in concept.lower()]
                if matching_concepts:
                    detected_industries.append({
                        'industry': industry,
                        'indicator': indicator,
                        'matching_concepts': matching_concepts[:5]
                    })
        
        # Find unusual/unique concepts (appear infrequently but might be valuable)
        rare_concepts = concept_counts[concept_counts == 1].index.tolist()
        
        return {
            'detected_industries': detected_industries,
            'rare_concepts': rare_concepts[:20],  # Top 20 rare concepts
            'total_unique_concepts': len(concept_counts),
            'concept_diversity_score': len(concept_counts) / len(all_facts) if all_facts else 0
        }
    
    def _extract_numeric_value_safe(self, fact: Dict[str, Any]) -> Optional[float]:
        """Safely extract numeric value from fact"""
        for value_field in ['value', 'numeric_value', 'amount']:
            value = fact.get(value_field)
            if value is not None:
                try:
                    # Handle string representations
                    if isinstance(value, str):
                        # Remove common formatting
                        clean_value = value.replace(',', '').replace('$', '').replace('%', '')
                        return float(clean_value)
                    return float(value)
                except (ValueError, TypeError):
                    continue
        return None
import json
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np


class UnifiedDatasetOrganizer:
    """Organize raw XBRL cache files into unified, analysis-ready datasets"""
    
    def __init__(self, cache_dir: str = "data/cache", output_dir: str = "data/unified"):
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Standard financial concepts mapping
        self.concept_mapping = {
            'revenue': {
                'concepts': ['Revenues', 'Revenue', 'SalesRevenueNet', 'PropertyIncome', 'RentalIncome', 
                           'RentalRevenue', 'TotalRevenues', 'OperatingIncomeLoss'],
                'priority': [1, 2, 3, 4, 5, 6, 7, 8]  # Priority order for selection
            },
            'operating_cash_flow': {
                'concepts': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByOperatingActivities',
                           'CashFlowFromOperatingActivities', 'NetCashUsedInOperatingActivities'],
                'priority': [1, 2, 3, 4]
            },
            'net_income': {
                'concepts': ['NetIncomeLoss', 'NetIncome', 'ProfitLoss', 'IncomeLossFromContinuingOperations'],
                'priority': [1, 2, 3, 4]
            },
            'total_assets': {
                'concepts': ['Assets', 'TotalAssets', 'AssetsCurrent'],
                'priority': [1, 2, 3]
            },
            'total_liabilities': {
                'concepts': ['Liabilities', 'TotalLiabilities', 'LiabilitiesCurrent'],
                'priority': [1, 2, 3]
            },
            'gross_profit': {
                'concepts': ['GrossProfit', 'GrossProfitLoss'],
                'priority': [1, 2]
            },
            'operating_income': {
                'concepts': ['OperatingIncomeLoss', 'IncomeLossFromOperations'],
                'priority': [1, 2]
            },
            'shares_outstanding': {
                'concepts': ['CommonStockSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic'],
                'priority': [1, 2]
            }
        }
    
    def process_ticker(self, ticker: str) -> Dict[str, Any]:
        """Process all quarters for a ticker into unified dataset"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            print(f"❌ No cache found for {ticker}")
            return {}
        
        print(f"🔄 Processing {ticker}...")
        
        # Load metadata
        metadata_path = os.path.join(ticker_dir, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Get all quarter files
        quarter_files = [f for f in os.listdir(ticker_dir) if f.endswith('.json') and f != 'metadata.json']
        quarter_files.sort()
        
        unified_data = {
            'ticker': ticker,
            'company_name': metadata.get('company_name', f"{ticker} Corporation"),
            'last_updated': metadata.get('last_updated', datetime.now().isoformat()),
            'quarters': [],
            'summary': {
                'total_quarters': len(quarter_files),
                'date_range': '',
                'data_quality': {}
            }
        }
        
        all_quarters = []
        
        # Process each quarter
        for quarter_file in quarter_files:
            quarter_data = self._process_quarter_file(ticker_dir, quarter_file)
            if quarter_data:
                all_quarters.append(quarter_data)
        
        # Sort quarters by date (most recent first)
        all_quarters.sort(key=lambda x: x['filing_date'], reverse=True)
        unified_data['quarters'] = all_quarters
        
        # Calculate summary statistics
        if all_quarters:
            dates = [q['filing_date'] for q in all_quarters]
            unified_data['summary']['date_range'] = f"{min(dates)} to {max(dates)}"
            unified_data['summary']['data_quality'] = self._calculate_data_quality(all_quarters)
        
        return unified_data
    
    def _process_quarter_file(self, ticker_dir: str, quarter_file: str) -> Optional[Dict[str, Any]]:
        """Process a single quarter file"""
        file_path = os.path.join(ticker_dir, quarter_file)
        
        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
            
            # Extract basic information
            quarter_data = {
                'filing_date': raw_data.get('filing_date', ''),
                'quarter': self._extract_quarter(raw_data.get('filing_date', '')),
                'year': self._extract_year(raw_data.get('filing_date', '')),
                'form_type': raw_data.get('form_type', '10-Q'),
                'xbrl_object_type': raw_data.get('xbrl_object_type', 'unknown'),
                'extraction_timestamp': raw_data.get('extraction_timestamp', ''),
                'financials': {},
                'metadata': {
                    'total_facts_count': raw_data.get('total_facts_count', 0),
                    'dimensions_count': raw_data.get('dimensions_count', 0),
                    'file_size_mb': raw_data.get('original_xbrl_size_estimate', 0),
                    'extraction_success': raw_data.get('extraction_success', False)
                }
            }
            
            # Extract financial metrics from facts
            if raw_data.get('facts_json'):
                facts_df = pd.read_json(raw_data['facts_json'])
                quarter_data['financials'] = self._extract_financial_metrics(facts_df)
            
            # Add dimensions summary
            if raw_data.get('dimensions_json'):
                dimensions = json.loads(raw_data['dimensions_json'])
                quarter_data['dimensions_summary'] = {
                    'total_dimensions': len(dimensions),
                    'dimension_names': list(dimensions.keys())
                }
            
            # Add statements summary
            if raw_data.get('statements_info'):
                statements = raw_data['statements_info']
                quarter_data['statements_summary'] = {
                    'available_statements': statements.get('available_statements', []),
                    'statement_count': len(statements.get('available_statements', []))
                }
            
            return quarter_data
            
        except Exception as e:
            print(f"   ❌ Error processing {quarter_file}: {e}")
            return None
    
    def _extract_financial_metrics(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract standardized financial metrics from facts DataFrame"""
        financials = {}
        
        for metric, config in self.concept_mapping.items():
            best_value = self._find_best_concept_value(facts_df, config['concepts'], config['priority'])
            financials[metric] = best_value
        
        # Calculate derived metrics
        financials['free_cash_flow'] = self._calculate_free_cash_flow(financials)
        financials['debt_to_assets'] = self._calculate_debt_to_assets(financials)
        financials['roa'] = self._calculate_roa(financials)
        
        return financials
    
    def _find_best_concept_value(self, facts_df: pd.DataFrame, concepts: List[str], priority: List[int]) -> Dict[str, Any]:
        """Find the best value for a financial concept based on priority"""
        result = {
            'value': None,
            'concept_used': None,
            'period': None,
            'confidence': 0,
            'alternatives': []
        }
        
        # Sort concepts by priority
        concept_priority_pairs = list(zip(concepts, priority))
        concept_priority_pairs.sort(key=lambda x: x[1])
        
        for concept, priority_score in concept_priority_pairs:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            
            if len(concept_rows) > 0:
                # Find the best value (most recent, highest quality)
                best_row = self._select_best_fact_row(concept_rows)
                
                if best_row is not None:
                    value = best_row.get('value', best_row.get('numeric_value', None))
                    
                    if value is not None:
                        try:
                            numeric_value = float(value)
                            
                            # Store as main result if this is highest priority found so far
                            if result['value'] is None:
                                result.update({
                                    'value': numeric_value,
                                    'concept_used': best_row['concept'],
                                    'period': best_row.get('period', 'Unknown'),
                                    'confidence': priority_score
                                })
                            else:
                                # Store as alternative
                                result['alternatives'].append({
                                    'value': numeric_value,
                                    'concept': best_row['concept'],
                                    'period': best_row.get('period', 'Unknown'),
                                    'priority': priority_score
                                })
                        except (ValueError, TypeError):
                            continue
        
        return result
    
    def _select_best_fact_row(self, concept_rows: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Select the best row from multiple facts for the same concept"""
        if len(concept_rows) == 0:
            return None
        
        # Prefer quarterly periods over annual
        quarterly_rows = concept_rows[concept_rows['period'].str.contains('3M|Q[1-4]', case=False, na=False)]
        if len(quarterly_rows) > 0:
            # Use most recent quarterly data
            return quarterly_rows.iloc[-1].to_dict()
        
        # Fall back to most recent data
        return concept_rows.iloc[-1].to_dict()
    
    def _calculate_free_cash_flow(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate free cash flow (simplified as operating cash flow)"""
        ocf = financials.get('operating_cash_flow', {}).get('value')
        
        if ocf is not None:
            return {
                'value': ocf,  # Simplified: OCF = FCF (would need CapEx for true FCF)
                'concept_used': 'Calculated (OCF approximation)',
                'period': financials.get('operating_cash_flow', {}).get('period'),
                'confidence': 7,  # Lower confidence for derived metric
                'alternatives': []
            }
        
        return {'value': None, 'concept_used': None, 'period': None, 'confidence': 0, 'alternatives': []}
    
    def _calculate_debt_to_assets(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate debt to assets ratio"""
        liabilities = financials.get('total_liabilities', {}).get('value')
        assets = financials.get('total_assets', {}).get('value')
        
        if liabilities is not None and assets is not None and assets != 0:
            ratio = liabilities / assets
            return {
                'value': ratio,
                'concept_used': 'Calculated (Liabilities/Assets)',
                'period': 'Calculated',
                'confidence': 8,
                'alternatives': []
            }
        
        return {'value': None, 'concept_used': None, 'period': None, 'confidence': 0, 'alternatives': []}
    
    def _calculate_roa(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Return on Assets"""
        net_income = financials.get('net_income', {}).get('value')
        assets = financials.get('total_assets', {}).get('value')
        
        if net_income is not None and assets is not None and assets != 0:
            roa = net_income / assets
            return {
                'value': roa,
                'concept_used': 'Calculated (Net Income/Assets)',
                'period': 'Calculated',
                'confidence': 8,
                'alternatives': []
            }
        
        return {'value': None, 'concept_used': None, 'period': None, 'confidence': 0, 'alternatives': []}
    
    def _calculate_data_quality(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate data quality metrics across quarters"""
        total_quarters = len(quarters)
        
        metrics_availability = {}
        for metric in self.concept_mapping.keys():
            available_count = sum(1 for q in quarters if q['financials'].get(metric, {}).get('value') is not None)
            metrics_availability[metric] = {
                'available_quarters': available_count,
                'coverage_percent': round(available_count / total_quarters * 100, 1) if total_quarters > 0 else 0
            }
        
        return {
            'total_quarters': total_quarters,
            'metrics_availability': metrics_availability,
            'overall_quality_score': np.mean([m['coverage_percent'] for m in metrics_availability.values()])
        }
    
    def _extract_quarter(self, filing_date: str) -> str:
        """Extract quarter from filing date"""
        try:
            date_obj = datetime.strptime(filing_date, '%Y-%m-%d')
            month = date_obj.month
            if month <= 3:
                return "Q1"
            elif month <= 6:
                return "Q2"
            elif month <= 9:
                return "Q3"
            else:
                return "Q4"
        except:
            return "Unknown"
    
    def _extract_year(self, filing_date: str) -> int:
        """Extract year from filing date"""
        try:
            return int(filing_date.split('-')[0])
        except:
            return 0
    
    def save_unified_dataset(self, ticker: str, unified_data: Dict[str, Any]):
        """Save unified dataset to file"""
        output_file = os.path.join(self.output_dir, f"{ticker}_unified.json")
        
        with open(output_file, 'w') as f:
            json.dump(unified_data, f, indent=2)
        
        print(f"💾 Saved unified dataset: {output_file}")
        
        # Also create a CSV for easy analysis
        self._create_csv_summary(ticker, unified_data)
    
    def _create_csv_summary(self, ticker: str, unified_data: Dict[str, Any]):
        """Create CSV summary of financial metrics"""
        quarters = unified_data.get('quarters', [])
        
        if not quarters:
            return
        
        # Create DataFrame
        rows = []
        for quarter in quarters:
            row = {
                'ticker': ticker,
                'filing_date': quarter['filing_date'],
                'quarter': quarter['quarter'],
                'year': quarter['year'],
                'form_type': quarter['form_type']
            }
            
            # Add financial metrics
            for metric, data in quarter['financials'].items():
                row[f"{metric}_value"] = data.get('value')
                row[f"{metric}_concept"] = data.get('concept_used')
                row[f"{metric}_confidence"] = data.get('confidence')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        csv_file = os.path.join(self.output_dir, f"{ticker}_summary.csv")
        df.to_csv(csv_file, index=False)
        
        print(f"📊 Saved CSV summary: {csv_file}")
    
    def process_all_tickers(self):
        """Process all cached tickers into unified datasets"""
        print("🚀 Processing all cached tickers...")
        
        if not os.path.exists(self.cache_dir):
            print(f"❌ Cache directory not found: {self.cache_dir}")
            return
        
        tickers = [d for d in os.listdir(self.cache_dir) 
                  if os.path.isdir(os.path.join(self.cache_dir, d)) and d != '__pycache__']
        
        print(f"📊 Found {len(tickers)} cached tickers: {', '.join(tickers)}")
        
        for ticker in tickers:
            try:
                unified_data = self.process_ticker(ticker)
                if unified_data.get('quarters'):
                    self.save_unified_dataset(ticker, unified_data)
                    print(f"   ✅ {ticker}: {len(unified_data['quarters'])} quarters processed")
                else:
                    print(f"   ⚠️ {ticker}: No valid quarters found")
            except Exception as e:
                print(f"   ❌ {ticker}: Error - {e}")
        
        print(f"🎉 Unified dataset creation completed!")


def main():
    """Main function to run the organizer"""
    organizer = UnifiedDatasetOrganizer()
    
    # Process specific ticker (Realty Income example)
    print("🏢 Processing Realty Income (O) as example...")
    unified_data = organizer.process_ticker("O")
    
    if unified_data.get('quarters'):
        organizer.save_unified_dataset("O", unified_data)
        
        # Show summary
        print(f"\n📊 Summary for {unified_data['ticker']}:")
        print(f"   Company: {unified_data['company_name']}")
        print(f"   Quarters: {unified_data['summary']['total_quarters']}")
        print(f"   Date Range: {unified_data['summary']['date_range']}")
        print(f"   Overall Quality: {unified_data['summary']['data_quality']['overall_quality_score']:.1f}%")
        
        # Show recent quarter
        if unified_data['quarters']:
            recent = unified_data['quarters'][0]  # Most recent (sorted desc)
            print(f"\n📈 Most Recent Quarter ({recent['quarter']} {recent['year']}):")
            for metric, data in recent['financials'].items():
                if data.get('value') is not None:
                    value = data['value']
                    if abs(value) > 1000000:
                        formatted = f"${value/1000000:.1f}M"
                    elif abs(value) > 1000:
                        formatted = f"${value/1000:.1f}K"
                    else:
                        formatted = f"${value:.2f}"
                    print(f"      {metric}: {formatted} (confidence: {data.get('confidence', 0)})")
    
    # Uncomment to process all tickers
    # print(f"\n🔄 Processing all cached tickers...")
    # organizer.process_all_tickers()


class UniversalConceptMapper:
    """Universal XBRL concept mapper that learns from all companies"""
    def _rank_concepts_by_frequency(self, concepts: List[str], preferred_order: List[str]) -> List[str]:
        """Rank concepts by preferred order and frequency"""
        ranked = []
        
        # Add preferred concepts first (if they exist in the list)
        for preferred in preferred_order:
            matching = [c for c in concepts if preferred.lower() in c.lower()]
            ranked.extend(matching)
        
        # Add remaining concepts
        remaining = [c for c in concepts if c not in ranked]
        ranked.extend(remaining)
        
        return ranked
    def __init__(self):
        self.learned_concepts = {}
        self.industry_patterns = {}
        
    def analyze_all_concepts(self, cache_dir: str = "data/cache") -> Dict[str, Any]:
        """Analyze all concepts across all cached companies to build universal mapping"""
        print("🔍 Analyzing all XBRL concepts across companies...")
        
        all_concepts = {}
        industry_concepts = {}
        
        # Get all cached tickers
        tickers = [d for d in os.listdir(cache_dir) 
                  if os.path.isdir(os.path.join(cache_dir, d)) and d != '__pycache__']
        
        for ticker in tickers:
            print(f"   📊 Analyzing {ticker}...")
            ticker_concepts = self._extract_ticker_concepts(cache_dir, ticker)
            
            # Merge concepts
            for concept, data in ticker_concepts.items():
                if concept not in all_concepts:
                    all_concepts[concept] = {
                        'count': 0,
                        'tickers': [],
                        'sample_values': [],
                        'patterns': {}
                    }
                
                all_concepts[concept]['count'] += data['count']
                all_concepts[concept]['tickers'].append(ticker)
                all_concepts[concept]['sample_values'].extend(data['sample_values'][:3])
        
        # Categorize concepts by frequency and pattern
        categorized_concepts = self._categorize_universal_concepts(all_concepts)
        
        print(f"✅ Analyzed {len(all_concepts)} unique concepts across {len(tickers)} companies")
        
        return {
            'total_concepts': len(all_concepts),
            'total_tickers': len(tickers),
            'categorized_concepts': categorized_concepts,
            'universal_mapping': self._build_universal_mapping(categorized_concepts)
        }
    
    def _extract_ticker_concepts(self, cache_dir: str, ticker: str) -> Dict[str, Any]:
        """Extract all concepts from a ticker's cache files"""
        ticker_dir = os.path.join(cache_dir, ticker)
        concepts = {}
        
        quarter_files = [f for f in os.listdir(ticker_dir) if f.endswith('.json') and f != 'metadata.json']
        
        for quarter_file in quarter_files:
            file_path = os.path.join(ticker_dir, quarter_file)
            
            try:
                with open(file_path, 'r') as f:
                    raw_data = json.load(f)
                
                if raw_data.get('facts_json'):
                    facts_df = pd.read_json(raw_data['facts_json'])
                    
                    for _, row in facts_df.iterrows():
                        concept = row.get('concept', '')
                        value = row.get('value', row.get('numeric_value', None))
                        
                        if concept and value is not None:
                            if concept not in concepts:
                                concepts[concept] = {
                                    'count': 0,
                                    'sample_values': []
                                }
                            
                            concepts[concept]['count'] += 1
                            
                            try:
                                numeric_value = float(value)
                                if len(concepts[concept]['sample_values']) < 5:
                                    concepts[concept]['sample_values'].append(numeric_value)
                            except:
                                pass
            
            except Exception as e:
                continue
        
        return concepts
    
    def _categorize_universal_concepts(self, all_concepts: Dict[str, Any]) -> Dict[str, List[str]]:
        """Categorize concepts into financial statement categories"""
        categories = {
            'revenue': [],
            'operating_cash_flow': [],
            'net_income': [],
            'assets': [],
            'liabilities': [],
            'equity': [],
            'expenses': [],
            'other_income': [],
            'shares': [],
            'per_share_metrics': [],
            'segment_data': [],
            'other': []
        }
        
        # Define universal patterns (works for all companies/industries)
        patterns = {
            'revenue': [
                'revenue', 'sales', 'income', 'rental', 'property', 'service', 'product',
                'subscription', 'interest', 'fee', 'commission', 'royalty'
            ],
            'operating_cash_flow': [
                'netcashprovided', 'cashflow', 'operatingactivities', 'operating'
            ],
            'net_income': [
                'netincome', 'netloss', 'profit', 'earnings', 'comprehensive'
            ],
            'assets': [
                'assets', 'property', 'equipment', 'investment', 'cash', 'receivable',
                'inventory', 'goodwill', 'intangible'
            ],
            'liabilities': [
                'liabilities', 'debt', 'payable', 'accrued', 'deferred', 'obligation'
            ],
            'equity': [
                'equity', 'capital', 'retained', 'stockholder', 'shareholder'
            ],
            'expenses': [
                'expense', 'cost', 'depreciation', 'amortization', 'impairment'
            ],
            'shares': [
                'shares', 'stock', 'outstanding', 'issued', 'weighted'
            ],
            'per_share_metrics': [
                'pershare', 'persharebas', 'pershadilut', 'earnings', 'dividend'
            ],
            'segment_data': [
                'segment', 'geography', 'region', 'division', 'subsidiary'
            ]
        }
        
        # Categorize each concept
        for concept, data in all_concepts.items():
            concept_lower = concept.lower()
            categorized = False
            
            for category, keywords in patterns.items():
                if any(keyword in concept_lower for keyword in keywords):
                    categories[category].append(concept)
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(concept)
        
        return categories
    
    def _build_universal_mapping(self, categorized_concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """Build universal financial concept mapping"""
        universal_mapping = {}
        
        for category, concepts in categorized_concepts.items():
            if not concepts:
                continue
            
            # Rank concepts by commonality and create mapping
            # For each category, create multiple extraction strategies
            
            if category == 'revenue':
                universal_mapping['revenue'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'Revenues', 'Revenue', 'SalesRevenueNet', 'TotalRevenues'
                    ]),
                    'industry_specific': self._rank_concepts_by_frequency(concepts, [
                        'PropertyIncome', 'RentalIncome', 'InterestIncome', 'ServiceRevenue'
                    ]),
                    'fallback_concepts': concepts[:20]  # Top 20 as fallback
                }
            
            elif category == 'operating_cash_flow':
                universal_mapping['operating_cash_flow'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'NetCashProvidedByUsedInOperatingActivities',
                        'NetCashProvidedByOperatingActivities'
                    ]),
                    'fallback_concepts': concepts[:10]
                }
            
            elif category == 'net_income':
                universal_mapping['net_income'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'NetIncomeLoss', 'NetIncome', 'ProfitLoss'
                    ]),
                    'fallback_concepts': concepts[:10]
                }
            
            elif category == 'assets':
                universal_mapping['total_assets'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'Assets', 'TotalAssets'
                    ]),
                    'fallback_concepts': concepts[:15]
                }
            
            elif category == 'liabilities':
                universal_mapping['total_liabilities'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'Liabilities', 'TotalLiabilities'
                    ]),
                    'fallback_concepts': concepts[:15]
                }
        
        return universal_mapping


class EnhancedUniversalOrganizer(UnifiedDatasetOrganizer):
    """Enhanced organizer that uses universal concept mapping"""
    
    def __init__(self, cache_dir: str = "data/cache", output_dir: str = "data/unified"):
        super().__init__(cache_dir, output_dir)
        self.universal_mapper = UniversalConceptMapper()
        self.universal_concepts = None
        
    def initialize_universal_mapping(self):
        """Initialize universal concept mapping from all cached data"""
        print("🔄 Building universal concept mapping...")
        self.universal_concepts = self.universal_mapper.analyze_all_concepts(self.cache_dir)
        
        # Save universal mapping for reference
        mapping_file = os.path.join(self.output_dir, "universal_concept_mapping.json")
        with open(mapping_file, 'w') as f:
            json.dump(self.universal_concepts, f, indent=2)
        
        print(f"💾 Universal mapping saved to: {mapping_file}")
        
        return self.universal_concepts
    
    def _extract_financial_metrics(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced financial metrics extraction using universal mapping"""
        if self.universal_concepts is None:
            # Fall back to original method if universal mapping not available
            return super()._extract_financial_metrics(facts_df)
        
        financials = {}
        universal_mapping = self.universal_concepts['universal_mapping']
        
        # Use universal mapping for each metric
        for metric, mapping_config in universal_mapping.items():
            best_value = self._find_universal_concept_value(facts_df, mapping_config)
            financials[metric] = best_value
        
        # Calculate derived metrics
        financials['free_cash_flow'] = self._calculate_free_cash_flow(financials)
        financials['debt_to_assets'] = self._calculate_debt_to_assets(financials)
        financials['roa'] = self._calculate_roa(financials)
        
        # Add industry-specific metrics if detected
        financials.update(self._extract_industry_specific_metrics(facts_df))
        
        return financials
    
    def _find_universal_concept_value(self, facts_df: pd.DataFrame, mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """Find value using universal concept mapping"""
        result = {
            'value': None,
            'concept_used': None,
            'period': None,
            'confidence': 0,
            'alternatives': []
        }
        
        # Try primary concepts first
        primary_concepts = mapping_config.get('primary_concepts', [])
        for concept in primary_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    result.update({
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 9  # High confidence for primary concepts
                    })
                    return result
        
        # Try industry-specific concepts
        industry_concepts = mapping_config.get('industry_specific', [])
        for concept in industry_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    result.update({
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 7  # Medium confidence for industry-specific
                    })
                    return result
        
        # Try fallback concepts
        fallback_concepts = mapping_config.get('fallback_concepts', [])
        for concept in fallback_concepts[:10]:  # Limit fallback attempts
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    result.update({
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 5  # Lower confidence for fallback
                    })
                    return result
        
        return result
    
    def _extract_numeric_value(self, row: Dict[str, Any]) -> Optional[float]:
        """Extract numeric value from a fact row"""
        value = row.get('value', row.get('numeric_value', None))
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
        return None
    
    def _extract_industry_specific_metrics(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract industry-specific metrics based on available concepts"""
        industry_metrics = {}
        
        # REIT-specific metrics
        reit_concepts = ['FundsFromOperations', 'AdjustedFundsFromOperations', 'PropertyIncome']
        for concept in reit_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    metric_name = concept.lower().replace('funds', '').replace('from', '').replace('operations', 'ffo')
                    industry_metrics[f"reit_{metric_name}"] = {
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 8
                    }
        
        # Bank-specific metrics
        bank_concepts = ['InterestIncome', 'InterestExpense', 'NonInterestIncome', 'ProvisionForLoanLosses']
        for concept in bank_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    metric_name = concept.lower().replace('interest', '').replace('income', '').replace('expense', '')
                    industry_metrics[f"bank_{metric_name}"] = {
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 8
                    }
        
        return industry_metrics
    
    def _rank_concepts_by_frequency(self, concepts: List[str], preferred_order: List[str]) -> List[str]:
        """Rank concepts by preferred order and frequency"""
        ranked = []
        
        # Add preferred concepts first (if they exist in the list)
        for preferred in preferred_order:
            matching = [c for c in concepts if preferred.lower() in c.lower()]
            ranked.extend(matching)
        
        # Add remaining concepts
        remaining = [c for c in concepts if c not in ranked]
        ranked.extend(remaining)
        
        return ranked


def main():
    """Enhanced main function with universal mapping"""
    # Create enhanced organizer
    organizer = EnhancedUniversalOrganizer()
    
    # Initialize universal mapping from all cached data
    print("🌍 Initializing universal concept mapping...")
    universal_concepts = organizer.initialize_universal_mapping()
    
    print(f"\n📊 Universal Mapping Summary:")
    print(f"   Total concepts analyzed: {universal_concepts['total_concepts']}")
    print(f"   Companies analyzed: {universal_concepts['total_tickers']}")
    print(f"   Categories mapped: {len(universal_concepts['universal_mapping'])}")
    
    # Process specific ticker (Realty Income example)
    print(f"\n🏢 Processing Realty Income (O) with universal mapping...")
    unified_data = organizer.process_ticker("O")
    
    if unified_data.get('quarters'):
        organizer.save_unified_dataset("O", unified_data)
        
        # Show summary
        print(f"\n📊 Summary for {unified_data['ticker']}:")
        print(f"   Company: {unified_data['company_name']}")
        print(f"   Quarters: {unified_data['summary']['total_quarters']}")
        print(f"   Date Range: {unified_data['summary']['date_range']}")
        print(f"   Overall Quality: {unified_data['summary']['data_quality']['overall_quality_score']:.1f}%")
        
        # Show recent quarter
        if unified_data['quarters']:
            recent = unified_data['quarters'][0]  # Most recent (sorted desc)
            print(f"\n📈 Most Recent Quarter ({recent['quarter']} {recent['year']}):")
            for metric, data in recent['financials'].items():
                if data.get('value') is not None:
                    value = data['value']
                    if abs(value) > 1000000:
                        formatted = f"${value/1000000:.1f}M"
                    elif abs(value) > 1000:
                        formatted = f"${value/1000:.1f}K"
                    else:
                        formatted = f"${value:.2f}"
                    print(f"      {metric}: {formatted} (confidence: {data.get('confidence', 0)})")
    
    # Process all tickers with universal mapping
    print(f"\n🌍 Processing all cached tickers with universal mapping...")
    organizer.process_all_tickers()

if __name__ == "__main__":
    main()


    def _analyze_facts_structure(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the structure of facts in this quarter"""
        return {
            'total_facts': len(facts_df),
            'columns_available': list(facts_df.columns),
            'non_null_counts': facts_df.count().to_dict(),
            'sample_concepts': facts_df['concept'].head(10).tolist() if 'concept' in facts_df.columns else []
        }
    
    def _summarize_dimensions(self, dimensions: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize dimensions data"""
        return {
            'total_dimensions': len(dimensions),
            'dimension_names': list(dimensions.keys()),
            'dimensions_with_values': {name: data.get('count', 0) for name, data in dimensions.items()}
        }
    
    def _analyze_dimensions_universal(self, all_dimensions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze dimensions across all quarters"""
        if not all_dimensions:
            return {}
        
        all_dimension_names = set()
        for dim_dict in all_dimensions:
            all_dimension_names.update(dim_dict.keys())
        
        return {
            'unique_dimensions_across_quarters': list(all_dimension_names),
            'total_unique_dimensions': len(all_dimension_names),
            'quarters_with_dimensions': len(all_dimensions)
        }
    
    def _calculate_edgartools_quality(self, quarters: List[Dict[str, Any]], all_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate data quality using EdgarTools metrics"""
        if not quarters:
            return {}
        
        # Calculate coverage for core financial metrics
        core_metrics = ['revenue', 'net_income', 'total_assets', 'operating_cash_flow']
        coverage = {}
        
        for metric in core_metrics:
            quarters_with_metric = sum(1 for q in quarters 
                                     if q.get('financials', {}).get(metric, {}).get('value') is not None)
            coverage[metric] = {
                'quarters_available': quarters_with_metric,
                'coverage_percentage': round(quarters_with_metric / len(quarters) * 100, 1)
            }
        
        # Calculate confidence scores
        confidence_scores = []
        for quarter in quarters:
            for metric, data in quarter.get('financials', {}).items():
                conf_score = data.get('confidence_score', 0)
                if conf_score > 0:
                    confidence_scores.append(conf_score)
        
        avg_confidence = np.mean(confidence_scores) if confidence_scores else 0
        
        return {
            'total_quarters': len(quarters),
            'core_metrics_coverage': coverage,
            'average_confidence_score': round(avg_confidence, 1),
            'total_facts_analyzed': len(all_facts),
            'quarters_with_facts': sum(1 for q in quarters if q.get('raw_facts')),
            'data_quality_grade': self._calculate_quality_grade(coverage, avg_confidence)
        }
    
    def _calculate_quality_grade(self, coverage: Dict[str, Any], avg_confidence: float) -> str:
        """Calculate overall data quality grade"""
        # Calculate average coverage percentage
        coverage_percentages = [metric['coverage_percentage'] for metric in coverage.values()]
        avg_coverage = np.mean(coverage_percentages) if coverage_percentages else 0
        
        # Grade based on coverage and confidence
        if avg_coverage >= 90 and avg_confidence >= 8:
            return 'A'
        elif avg_coverage >= 75 and avg_confidence >= 7:
            return 'B'
        elif avg_coverage >= 60 and avg_confidence >= 6:
            return 'C'
        elif avg_coverage >= 40 and avg_confidence >= 5:
            return 'D'
        else:
            return 'F'
    
    def save_edgartools_dataset(self, ticker: str, unified_data: Dict[str, Any]):
        """Save dataset following EdgarTools patterns"""
        # Save detailed JSON
        output_file = os.path.join(self.output_dir, f"{ticker}_edgartools_unified.json")
        with open(output_file, 'w') as f:
            json.dump(unified_data, f, indent=2, default=str)
        
        print(f"💾 Saved EdgarTools-style dataset: {output_file}")
        
        # Create financial metrics CSV
        self._create_financial_metrics_csv(ticker, unified_data)
        
        # Create facts analysis CSV
        self._create_facts_analysis_csv(ticker, unified_data)
    
    def _create_financial_metrics_csv(self, ticker: str, unified_data: Dict[str, Any]):
        """Create CSV of financial metrics"""
        quarters = unified_data.get('quarters', [])
        if not quarters:
            return
        
        rows = []
        for quarter in quarters:
            row = {
                'ticker': ticker,
                'filing_date': quarter['filing_date'],
                'quarter': quarter['quarter'],
                'year': quarter['year'],
                'form_type': quarter['form_type']
            }
            
            # Add financial metrics
            for metric, data in quarter.get('financials', {}).items():
                row[f"{metric}_value"] = data.get('value')
                row[f"{metric}_concept"] = data.get('concept_used')
                row[f"{metric}_confidence"] = data.get('confidence_score')
                row[f"{metric}_method"] = data.get('extraction_method')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        csv_file = os.path.join(self.output_dir, f"{ticker}_financials_edgartools.csv")
        df.to_csv(csv_file, index=False)
        
        print(f"📊 Saved financial metrics CSV: {csv_file}")
    
    def _create_facts_analysis_csv(self, ticker: str, unified_data: Dict[str, Any]):
        """Create CSV analysis of facts data"""
        facts_analysis = unified_data.get('facts_analysis', {})
        if not facts_analysis:
            return
        
        # Create concept frequency analysis
        top_concepts = facts_analysis.get('top_concepts', {})
        if top_concepts:
            concepts_df = pd.DataFrame([
                {'ticker': ticker, 'concept': concept, 'frequency': count}
                for concept, count in top_concepts.items()
            ])
            
            concepts_file = os.path.join(self.output_dir, f"{ticker}_concepts_analysis.csv")
            concepts_df.to_csv(concepts_file, index=False)
            print(f"📊 Saved concepts analysis CSV: {concepts_file}")
    
    def _load_metadata(self, ticker_dir: str) -> Dict[str, Any]:
        """Load ticker metadata"""
        metadata_path = os.path.join(ticker_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _extract_quarter(self, filing_date: str) -> str:
        """Extract quarter from filing date"""
        try:
            date_obj = datetime.strptime(filing_date, '%Y-%m-%d')
            month = date_obj.month
            if month <= 3:
                return "Q1"
            elif month <= 6:
                return "Q2"
            elif month <= 9:
                return "Q3"
            else:
                return "Q4"
        except:
            return "Unknown"
    
    def _extract_year(self, filing_date: str) -> int:
        """Extract year from filing date"""
        try:
            return int(filing_date.split('-')[0])
        except:
            return 0
    
    def process_all_tickers_edgartools(self):
        """Process all tickers using EdgarTools methodology"""
        print("🌍 Processing all cached tickers using EdgarTools best practices...")
        
        if not os.path.exists(self.cache_dir):
            print(f"❌ Cache directory not found: {self.cache_dir}")
            return
        
        tickers = [d for d in os.listdir(self.cache_dir) 
                  if os.path.isdir(os.path.join(self.cache_dir, d)) and d != '__pycache__']
        
        print(f"📊 Found {len(tickers)} cached tickers: {', '.join(tickers)}")
        
        # Create summary of all processed tickers
        all_tickers_summary = {
            'processing_date': datetime.now().isoformat(),
            'total_tickers': len(tickers),
            'successfully_processed': [],
            'failed_processing': [],
            'industry_detection': {},
            'data_quality_overview': {}
        }
        
        for ticker in tickers:
            try:
                print(f"\n🔄 Processing {ticker} with EdgarTools methodology...")
                unified_data = self.process_ticker_edgartools_style(ticker)
                
                if unified_data.get('quarters'):
                    self.save_edgartools_dataset(ticker, unified_data)
                    
                    # Add to summary
                    all_tickers_summary['successfully_processed'].append({
                        'ticker': ticker,
                        'company_name': unified_data.get('company_name', ''),
                        'quarters_processed': len(unified_data['quarters']),
                        'data_quality_grade': unified_data.get('data_quality', {}).get('data_quality_grade', 'Unknown'),
                        'industries_detected': [ind['industry'] for ind in unified_data.get('concept_discovery', {}).get('detected_industries', [])]
                    })
                    
                    print(f"   ✅ {ticker}: {len(unified_data['quarters'])} quarters, Grade: {unified_data.get('data_quality', {}).get('data_quality_grade', 'Unknown')}")
                else:
                    all_tickers_summary['failed_processing'].append({
                        'ticker': ticker,
                        'reason': 'No valid quarters found'
                    })
                    print(f"   ⚠️ {ticker}: No valid quarters found")
                    
            except Exception as e:
                all_tickers_summary['failed_processing'].append({
                    'ticker': ticker,
                    'reason': str(e)
                })
                print(f"   ❌ {ticker}: Error - {e}")
        
        # Save overall summary
        summary_file = os.path.join(self.output_dir, "all_tickers_edgartools_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(all_tickers_summary, f, indent=2)
        
        # Create summary CSV
        self._create_summary_csv(all_tickers_summary)
        
        print(f"\n🎉 EdgarTools-style processing completed!")
        print(f"   ✅ Successfully processed: {len(all_tickers_summary['successfully_processed'])}")
        print(f"   ❌ Failed: {len(all_tickers_summary['failed_processing'])}")
        print(f"   📄 Summary saved: {summary_file}")
    
    def _create_summary_csv(self, summary_data: Dict[str, Any]):
        """Create CSV summary of all processed tickers"""
        successful = summary_data.get('successfully_processed', [])
        if not successful:
            return
        
        # Flatten the data for CSV
        rows = []
        for ticker_data in successful:
            row = {
                'ticker': ticker_data['ticker'],
                'company_name': ticker_data['company_name'],
                'quarters_processed': ticker_data['quarters_processed'],
                'data_quality_grade': ticker_data['data_quality_grade'],
                'industries_detected': ', '.join(ticker_data.get('industries_detected', []))
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        csv_file = os.path.join(self.output_dir, "all_tickers_summary_edgartools.csv")
        df.to_csv(csv_file, index=False)
        
        print(f"📊 Saved summary CSV: {csv_file}")


def inspect_realty_income_with_edgartools():
    """Inspect Realty Income using EdgarTools methodology"""
    organizer = EdgarToolsUniversalOrganizer()
    
    print("🏢 Processing Realty Income (O) with EdgarTools best practices")
    print("=" * 60)
    
    # Process using EdgarTools methodology
    unified_data = organizer.process_ticker_edgartools_style("O")
    
    if not unified_data.get('quarters'):
        print("❌ No data found for Realty Income (O)")
        print("💡 Make sure to run the app and search for 'O' first to cache the data")
        return
    
    # Save the dataset
    organizer.save_edgartools_dataset("O", unified_data)
    
    # Show detailed analysis
    print(f"\n📊 EdgarTools Analysis Summary:")
    print(f"   Company: {unified_data['company_name']}")
    print(f"   Quarters processed: {len(unified_data['quarters'])}")
    print(f"   Processing method: {unified_data['processing_method']}")
    
    # Data quality
    quality = unified_data.get('data_quality', {})
    print(f"\n📈 Data Quality Assessment:")
    print(f"   Overall grade: {quality.get('data_quality_grade', 'Unknown')}")
    print(f"   Average confidence: {quality.get('average_confidence_score', 0)}")
    print(f"   Total facts analyzed: {quality.get('total_facts_analyzed', 0)}")
    
    # Core metrics coverage
    coverage = quality.get('core_metrics_coverage', {})
    if coverage:
        print(f"\n📊 Core Metrics Coverage:")
        for metric, data in coverage.items():
            print(f"   {metric}: {data['coverage_percentage']}% ({data['quarters_available']} quarters)")
    
    # Industry detection
    concept_discovery = unified_data.get('concept_discovery', {})
    industries = concept_discovery.get('detected_industries', [])
    if industries:
        print(f"\n🏭 Detected Industries:")
        for industry_info in industries[:5]:  # Show top 5
            print(f"   {industry_info['industry']}: {industry_info['indicator']} (concepts: {len(industry_info['matching_concepts'])})")
    
    # Show most recent quarter details
    if unified_data['quarters']:
        recent = unified_data['quarters'][0]  # Most recent
        print(f"\n📈 Most Recent Quarter ({recent['quarter']} {recent['year']}):")
        print(f"   Filing date: {recent['filing_date']}")
        print(f"   Facts count: {recent['extraction_metadata']['total_facts_count']}")
        
        # Show key financials
        financials = recent.get('financials', {})
        key_metrics = ['revenue', 'net_income', 'operating_cash_flow', 'total_assets']
        
        for metric in key_metrics:
            data = financials.get(metric, {})
            if data.get('value') is not None:
                value = data['value']
                concept = data.get('concept_used', 'Unknown')
                confidence = data.get('confidence_score', 0)
                
                # Format value
                if abs(value) > 1000000:
                    formatted = f"${value/1000000:.1f}M"
                else:
                    formatted = f"${value:,.0f}"
                
                print(f"   {metric}: {formatted} (confidence: {confidence}/10)")
                print(f"      └─ Concept: {concept}")
    
    # Facts analysis
    facts_analysis = unified_data.get('facts_analysis', {})
    if facts_analysis:
        print(f"\n📊 Facts Analysis:")
        print(f"   Total facts across all quarters: {facts_analysis.get('total_facts', 0)}")
        print(f"   Unique concepts found: {facts_analysis.get('unique_concepts', 0)}")
        
        top_concepts = facts_analysis.get('top_concepts', {})
        if top_concepts:
            print(f"   Top 5 most frequent concepts:")
            for i, (concept, count) in enumerate(list(top_concepts.items())[:5], 1):
                print(f"      {i}. {concept}: {count} occurrences")
    
    return unified_data


def main():
    """Main function using EdgarTools best practices"""
    print("🚀 Universal Dataset Organizer - EdgarTools Edition")
    print("=" * 60)
    
    # Inspect Realty Income as example
    unified_data = inspect_realty_income_with_edgartools()
    
    if unified_data:
        print(f"\n✅ Realty Income processed successfully!")
        print(f"📄 Files created:")
        print(f"   • O_edgartools_unified.json (complete dataset)")
        print(f"   • O_financials_edgartools.csv (financial metrics)")
        print(f"   • O_concepts_analysis.csv (concept frequency)")
    
    # Offer to process all tickers
    print(f"\n🌍 To process all cached tickers with EdgarTools methodology:")
    print(f"   organizer = EdgarToolsUniversalOrganizer()")
    print(f"   organizer.process_all_tickers_edgartools()")


if __name__ == "__main__":
    main()        # Show recent quarter# tools/unified_dataset_organizer.py - Convert raw XBRL cache to unified datasets

import json
import os
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import numpy as np


class UnifiedDatasetOrganizer:
    """Organize raw XBRL cache files into unified, analysis-ready datasets"""
    
    def __init__(self, cache_dir: str = "data/cache", output_dir: str = "data/unified"):
        self.cache_dir = cache_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Standard financial concepts mapping
        self.concept_mapping = {
            'revenue': {
                'concepts': ['Revenues', 'Revenue', 'SalesRevenueNet', 'PropertyIncome', 'RentalIncome', 
                           'RentalRevenue', 'TotalRevenues', 'OperatingIncomeLoss'],
                'priority': [1, 2, 3, 4, 5, 6, 7, 8]  # Priority order for selection
            },
            'operating_cash_flow': {
                'concepts': ['NetCashProvidedByUsedInOperatingActivities', 'NetCashProvidedByOperatingActivities',
                           'CashFlowFromOperatingActivities', 'NetCashUsedInOperatingActivities'],
                'priority': [1, 2, 3, 4]
            },
            'net_income': {
                'concepts': ['NetIncomeLoss', 'NetIncome', 'ProfitLoss', 'IncomeLossFromContinuingOperations'],
                'priority': [1, 2, 3, 4]
            },
            'total_assets': {
                'concepts': ['Assets', 'TotalAssets', 'AssetsCurrent'],
                'priority': [1, 2, 3]
            },
            'total_liabilities': {
                'concepts': ['Liabilities', 'TotalLiabilities', 'LiabilitiesCurrent'],
                'priority': [1, 2, 3]
            },
            'gross_profit': {
                'concepts': ['GrossProfit', 'GrossProfitLoss'],
                'priority': [1, 2]
            },
            'operating_income': {
                'concepts': ['OperatingIncomeLoss', 'IncomeLossFromOperations'],
                'priority': [1, 2]
            },
            'shares_outstanding': {
                'concepts': ['CommonStockSharesOutstanding', 'WeightedAverageNumberOfSharesOutstandingBasic'],
                'priority': [1, 2]
            }
        }
    
    def process_ticker(self, ticker: str) -> Dict[str, Any]:
        """Process all quarters for a ticker into unified dataset"""
        ticker = ticker.upper()
        ticker_dir = os.path.join(self.cache_dir, ticker)
        
        if not os.path.exists(ticker_dir):
            print(f"❌ No cache found for {ticker}")
            return {}
        
        print(f"🔄 Processing {ticker}...")
        
        # Load metadata
        metadata_path = os.path.join(ticker_dir, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        # Get all quarter files
        quarter_files = [f for f in os.listdir(ticker_dir) if f.endswith('.json') and f != 'metadata.json']
        quarter_files.sort()
        
        unified_data = {
            'ticker': ticker,
            'company_name': metadata.get('company_name', f"{ticker} Corporation"),
            'last_updated': metadata.get('last_updated', datetime.now().isoformat()),
            'quarters': [],
            'summary': {
                'total_quarters': len(quarter_files),
                'date_range': '',
                'data_quality': {}
            }
        }
        
        all_quarters = []
        
        # Process each quarter
        for quarter_file in quarter_files:
            quarter_data = self._process_quarter_file(ticker_dir, quarter_file)
            if quarter_data:
                all_quarters.append(quarter_data)
        
        # Sort quarters by date (most recent first)
        all_quarters.sort(key=lambda x: x['filing_date'], reverse=True)
        unified_data['quarters'] = all_quarters
        
        # Calculate summary statistics
        if all_quarters:
            dates = [q['filing_date'] for q in all_quarters]
            unified_data['summary']['date_range'] = f"{min(dates)} to {max(dates)}"
            unified_data['summary']['data_quality'] = self._calculate_data_quality(all_quarters)
        
        return unified_data
    
    def _process_quarter_file(self, ticker_dir: str, quarter_file: str) -> Optional[Dict[str, Any]]:
        """Process a single quarter file"""
        file_path = os.path.join(ticker_dir, quarter_file)
        
        try:
            with open(file_path, 'r') as f:
                raw_data = json.load(f)
            
            # Extract basic information
            quarter_data = {
                'filing_date': raw_data.get('filing_date', ''),
                'quarter': self._extract_quarter(raw_data.get('filing_date', '')),
                'year': self._extract_year(raw_data.get('filing_date', '')),
                'form_type': raw_data.get('form_type', '10-Q'),
                'xbrl_object_type': raw_data.get('xbrl_object_type', 'unknown'),
                'extraction_timestamp': raw_data.get('extraction_timestamp', ''),
                'financials': {},
                'metadata': {
                    'total_facts_count': raw_data.get('total_facts_count', 0),
                    'dimensions_count': raw_data.get('dimensions_count', 0),
                    'file_size_mb': raw_data.get('original_xbrl_size_estimate', 0),
                    'extraction_success': raw_data.get('extraction_success', False)
                }
            }
            
            # Extract financial metrics from facts
            if raw_data.get('facts_json'):
                import io
                facts_df = pd.read_json(io.StringIO(raw_data['facts_json']))
                quarter_data['financials'] = self._extract_financial_metrics(facts_df)
            
            # Add dimensions summary
            if raw_data.get('dimensions_json'):
                dimensions = json.loads(raw_data['dimensions_json'])
                quarter_data['dimensions_summary'] = {
                    'total_dimensions': len(dimensions),
                    'dimension_names': list(dimensions.keys())
                }
            
            # Add statements summary
            if raw_data.get('statements_info'):
                statements = raw_data['statements_info']
                quarter_data['statements_summary'] = {
                    'available_statements': statements.get('available_statements', []),
                    'statement_count': len(statements.get('available_statements', []))
                }
            
            return quarter_data
            
        except Exception as e:
            print(f"   ❌ Error processing {quarter_file}: {e}")
            return None
    
    def _extract_financial_metrics(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract standardized financial metrics from facts DataFrame"""
        financials = {}
        
        for metric, config in self.concept_mapping.items():
            best_value = self._find_best_concept_value(facts_df, config['concepts'], config['priority'])
            financials[metric] = best_value
        
        # Calculate derived metrics
        financials['free_cash_flow'] = self._calculate_free_cash_flow(financials)
        financials['debt_to_assets'] = self._calculate_debt_to_assets(financials)
        financials['roa'] = self._calculate_roa(financials)
        
        return financials
    
    def _find_best_concept_value(self, facts_df: pd.DataFrame, concepts: List[str], priority: List[int]) -> Dict[str, Any]:
        """Find the best value for a financial concept based on priority"""
        result = {
            'value': None,
            'concept_used': None,
            'period': None,
            'confidence': 0,
            'alternatives': []
        }
        
        # Sort concepts by priority
        concept_priority_pairs = list(zip(concepts, priority))
        concept_priority_pairs.sort(key=lambda x: x[1])
        
        for concept, priority_score in concept_priority_pairs:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            
            if len(concept_rows) > 0:
                # Find the best value (most recent, highest quality)
                best_row = self._select_best_fact_row(concept_rows)
                
                if best_row is not None:
                    value = best_row.get('value', best_row.get('numeric_value', None))
                    
                    if value is not None:
                        try:
                            numeric_value = float(value)
                            
                            # Store as main result if this is highest priority found so far
                            if result['value'] is None:
                                result.update({
                                    'value': numeric_value,
                                    'concept_used': best_row['concept'],
                                    'period': best_row.get('period', 'Unknown'),
                                    'confidence': priority_score
                                })
                            else:
                                # Store as alternative
                                result['alternatives'].append({
                                    'value': numeric_value,
                                    'concept': best_row['concept'],
                                    'period': best_row.get('period', 'Unknown'),
                                    'priority': priority_score
                                })
                        except (ValueError, TypeError):
                            continue
        
        return result
    
    def _select_best_fact_row(self, concept_rows: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Select the best row from multiple facts for the same concept"""
        if len(concept_rows) == 0:
            return None
        
        # Prefer quarterly periods over annual
        quarterly_rows = concept_rows[concept_rows['period'].str.contains('3M|Q[1-4]', case=False, na=False)]
        if len(quarterly_rows) > 0:
            # Use most recent quarterly data
            return quarterly_rows.iloc[-1].to_dict()
        
        # Fall back to most recent data
        return concept_rows.iloc[-1].to_dict()
    
    def _calculate_free_cash_flow(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate free cash flow (simplified as operating cash flow)"""
        ocf = financials.get('operating_cash_flow', {}).get('value')
        
        if ocf is not None:
            return {
                'value': ocf,  # Simplified: OCF = FCF (would need CapEx for true FCF)
                'concept_used': 'Calculated (OCF approximation)',
                'period': financials.get('operating_cash_flow', {}).get('period'),
                'confidence': 7,  # Lower confidence for derived metric
                'alternatives': []
            }
        
        return {'value': None, 'concept_used': None, 'period': None, 'confidence': 0, 'alternatives': []}
    
    def _calculate_debt_to_assets(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate debt to assets ratio"""
        liabilities = financials.get('total_liabilities', {}).get('value')
        assets = financials.get('total_assets', {}).get('value')
        
        if liabilities is not None and assets is not None and assets != 0:
            ratio = liabilities / assets
            return {
                'value': ratio,
                'concept_used': 'Calculated (Liabilities/Assets)',
                'period': 'Calculated',
                'confidence': 8,
                'alternatives': []
            }
        
        return {'value': None, 'concept_used': None, 'period': None, 'confidence': 0, 'alternatives': []}
    
    def _calculate_roa(self, financials: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Return on Assets"""
        net_income = financials.get('net_income', {}).get('value')
        assets = financials.get('total_assets', {}).get('value')
        
        if net_income is not None and assets is not None and assets != 0:
            roa = net_income / assets
            return {
                'value': roa,
                'concept_used': 'Calculated (Net Income/Assets)',
                'period': 'Calculated',
                'confidence': 8,
                'alternatives': []
            }
        
        return {'value': None, 'concept_used': None, 'period': None, 'confidence': 0, 'alternatives': []}
    
    def _calculate_data_quality(self, quarters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate data quality metrics across quarters"""
        total_quarters = len(quarters)
        
        metrics_availability = {}
        for metric in self.concept_mapping.keys():
            available_count = sum(1 for q in quarters if q['financials'].get(metric, {}).get('value') is not None)
            metrics_availability[metric] = {
                'available_quarters': available_count,
                'coverage_percent': round(available_count / total_quarters * 100, 1) if total_quarters > 0 else 0
            }
        
        return {
            'total_quarters': total_quarters,
            'metrics_availability': metrics_availability,
            'overall_quality_score': np.mean([m['coverage_percent'] for m in metrics_availability.values()])
        }
    
    def _extract_quarter(self, filing_date: str) -> str:
        """Extract quarter from filing date"""
        try:
            date_obj = datetime.strptime(filing_date, '%Y-%m-%d')
            month = date_obj.month
            if month <= 3:
                return "Q1"
            elif month <= 6:
                return "Q2"
            elif month <= 9:
                return "Q3"
            else:
                return "Q4"
        except:
            return "Unknown"
    
    def _extract_year(self, filing_date: str) -> int:
        """Extract year from filing date"""
        try:
            return int(filing_date.split('-')[0])
        except:
            return 0
    
    def save_unified_dataset(self, ticker: str, unified_data: Dict[str, Any]):
        """Save unified dataset to file"""
        output_file = os.path.join(self.output_dir, f"{ticker}_unified.json")
        
        with open(output_file, 'w') as f:
            json.dump(unified_data, f, indent=2)
        
        print(f"💾 Saved unified dataset: {output_file}")
        
        # Also create a CSV for easy analysis
        self._create_csv_summary(ticker, unified_data)
    
    def _create_csv_summary(self, ticker: str, unified_data: Dict[str, Any]):
        """Create CSV summary of financial metrics"""
        quarters = unified_data.get('quarters', [])
        
        if not quarters:
            return
        
        # Create DataFrame
        rows = []
        for quarter in quarters:
            row = {
                'ticker': ticker,
                'filing_date': quarter['filing_date'],
                'quarter': quarter['quarter'],
                'year': quarter['year'],
                'form_type': quarter['form_type']
            }
            
            # Add financial metrics
            for metric, data in quarter['financials'].items():
                row[f"{metric}_value"] = data.get('value')
                row[f"{metric}_concept"] = data.get('concept_used')
                row[f"{metric}_confidence"] = data.get('confidence')
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        csv_file = os.path.join(self.output_dir, f"{ticker}_summary.csv")
        df.to_csv(csv_file, index=False)
        
        print(f"📊 Saved CSV summary: {csv_file}")
    
    def process_all_tickers(self):
        """Process all cached tickers into unified datasets"""
        print("🚀 Processing all cached tickers...")
        
        if not os.path.exists(self.cache_dir):
            print(f"❌ Cache directory not found: {self.cache_dir}")
            return
        
        tickers = [d for d in os.listdir(self.cache_dir) 
                  if os.path.isdir(os.path.join(self.cache_dir, d)) and d != '__pycache__']
        
        print(f"📊 Found {len(tickers)} cached tickers: {', '.join(tickers)}")
        
        for ticker in tickers:
            try:
                unified_data = self.process_ticker(ticker)
                if unified_data.get('quarters'):
                    self.save_unified_dataset(ticker, unified_data)
                    print(f"   ✅ {ticker}: {len(unified_data['quarters'])} quarters processed")
                else:
                    print(f"   ⚠️ {ticker}: No valid quarters found")
            except Exception as e:
                print(f"   ❌ {ticker}: Error - {e}")
        
        print(f"🎉 Unified dataset creation completed!")


def main():
    """Main function to run the organizer"""
    organizer = UnifiedDatasetOrganizer()
    
    # Process specific ticker (Realty Income example)
    print("🏢 Processing Realty Income (O) as example...")
    unified_data = organizer.process_ticker("O")
    
    if unified_data.get('quarters'):
        organizer.save_unified_dataset("O", unified_data)
        
        # Show summary
        print(f"\n📊 Summary for {unified_data['ticker']}:")
        print(f"   Company: {unified_data['company_name']}")
        print(f"   Quarters: {unified_data['summary']['total_quarters']}")
        print(f"   Date Range: {unified_data['summary']['date_range']}")
        print(f"   Overall Quality: {unified_data['summary']['data_quality']['overall_quality_score']:.1f}%")
        
        # Show recent quarter
        if unified_data['quarters']:
            recent = unified_data['quarters'][0]  # Most recent (sorted desc)
            print(f"\n📈 Most Recent Quarter ({recent['quarter']} {recent['year']}):")
            for metric, data in recent['financials'].items():
                if data.get('value') is not None:
                    value = data['value']
                    if abs(value) > 1000000:
                        formatted = f"${value/1000000:.1f}M"
                    elif abs(value) > 1000:
                        formatted = f"${value/1000:.1f}K"
                    else:
                        formatted = f"${value:.2f}"
                    print(f"      {metric}: {formatted} (confidence: {data.get('confidence', 0)})")
    
    # Uncomment to process all tickers
    # print(f"\n🔄 Processing all cached tickers...")
    # organizer.process_all_tickers()


class UniversalConceptMapper:
    """Universal XBRL concept mapper that learns from all companies"""
    
    def __init__(self):
        self.learned_concepts = {}
        self.industry_patterns = {}
        
    def analyze_all_concepts(self, cache_dir: str = "data/cache") -> Dict[str, Any]:
        """Analyze all concepts across all cached companies to build universal mapping"""
        print("🔍 Analyzing all XBRL concepts across companies...")
        
        all_concepts = {}
        industry_concepts = {}
        
        # Get all cached tickers
        tickers = [d for d in os.listdir(cache_dir) 
                  if os.path.isdir(os.path.join(cache_dir, d)) and d != '__pycache__']
        
        for ticker in tickers:
            print(f"   📊 Analyzing {ticker}...")
            ticker_concepts = self._extract_ticker_concepts(cache_dir, ticker)
            
            # Merge concepts
            for concept, data in ticker_concepts.items():
                if concept not in all_concepts:
                    all_concepts[concept] = {
                        'count': 0,
                        'tickers': [],
                        'sample_values': [],
                        'patterns': {}
                    }
                
                all_concepts[concept]['count'] += data['count']
                all_concepts[concept]['tickers'].append(ticker)
                all_concepts[concept]['sample_values'].extend(data['sample_values'][:3])
        
        # Categorize concepts by frequency and pattern
        categorized_concepts = self._categorize_universal_concepts(all_concepts)
        
        print(f"✅ Analyzed {len(all_concepts)} unique concepts across {len(tickers)} companies")
        
        return {
            'total_concepts': len(all_concepts),
            'total_tickers': len(tickers),
            'categorized_concepts': categorized_concepts,
            'universal_mapping': self._build_universal_mapping(categorized_concepts)
        }
    
    def _extract_ticker_concepts(self, cache_dir: str, ticker: str) -> Dict[str, Any]:
        """Extract all concepts from a ticker's cache files"""
        ticker_dir = os.path.join(cache_dir, ticker)
        concepts = {}
        
        quarter_files = [f for f in os.listdir(ticker_dir) if f.endswith('.json') and f != 'metadata.json']
        
        for quarter_file in quarter_files:
            file_path = os.path.join(ticker_dir, quarter_file)
            
            try:
                with open(file_path, 'r') as f:
                    raw_data = json.load(f)
                
                if raw_data.get('facts_json'):
                    facts_df = pd.read_json(raw_data['facts_json'])
                    
                    for _, row in facts_df.iterrows():
                        concept = row.get('concept', '')
                        value = row.get('value', row.get('numeric_value', None))
                        
                        if concept and value is not None:
                            if concept not in concepts:
                                concepts[concept] = {
                                    'count': 0,
                                    'sample_values': []
                                }
                            
                            concepts[concept]['count'] += 1
                            
                            try:
                                numeric_value = float(value)
                                if len(concepts[concept]['sample_values']) < 5:
                                    concepts[concept]['sample_values'].append(numeric_value)
                            except:
                                pass
            
            except Exception as e:
                continue
        
        return concepts
    
    def _categorize_universal_concepts(self, all_concepts: Dict[str, Any]) -> Dict[str, List[str]]:
        """Categorize concepts into financial statement categories"""
        categories = {
            'revenue': [],
            'operating_cash_flow': [],
            'net_income': [],
            'assets': [],
            'liabilities': [],
            'equity': [],
            'expenses': [],
            'other_income': [],
            'shares': [],
            'per_share_metrics': [],
            'segment_data': [],
            'other': []
        }
        
        # Define universal patterns (works for all companies/industries)
        patterns = {
            'revenue': [
                'revenue', 'sales', 'income', 'rental', 'property', 'service', 'product',
                'subscription', 'interest', 'fee', 'commission', 'royalty'
            ],
            'operating_cash_flow': [
                'netcashprovided', 'cashflow', 'operatingactivities', 'operating'
            ],
            'net_income': [
                'netincome', 'netloss', 'profit', 'earnings', 'comprehensive'
            ],
            'assets': [
                'assets', 'property', 'equipment', 'investment', 'cash', 'receivable',
                'inventory', 'goodwill', 'intangible'
            ],
            'liabilities': [
                'liabilities', 'debt', 'payable', 'accrued', 'deferred', 'obligation'
            ],
            'equity': [
                'equity', 'capital', 'retained', 'stockholder', 'shareholder'
            ],
            'expenses': [
                'expense', 'cost', 'depreciation', 'amortization', 'impairment'
            ],
            'shares': [
                'shares', 'stock', 'outstanding', 'issued', 'weighted'
            ],
            'per_share_metrics': [
                'pershare', 'persharebas', 'pershadilut', 'earnings', 'dividend'
            ],
            'segment_data': [
                'segment', 'geography', 'region', 'division', 'subsidiary'
            ]
        }
        
        # Categorize each concept
        for concept, data in all_concepts.items():
            concept_lower = concept.lower()
            categorized = False
            
            for category, keywords in patterns.items():
                if any(keyword in concept_lower for keyword in keywords):
                    categories[category].append(concept)
                    categorized = True
                    break
            
            if not categorized:
                categories['other'].append(concept)
        
        return categories
    
    def _build_universal_mapping(self, categorized_concepts: Dict[str, List[str]]) -> Dict[str, Any]:
        """Build universal financial concept mapping"""
        universal_mapping = {}
        
        for category, concepts in categorized_concepts.items():
            if not concepts:
                continue
            
            # Rank concepts by commonality and create mapping
            # For each category, create multiple extraction strategies
            
            if category == 'revenue':
                universal_mapping['revenue'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'Revenues', 'Revenue', 'SalesRevenueNet', 'TotalRevenues'
                    ]),
                    'industry_specific': self._rank_concepts_by_frequency(concepts, [
                        'PropertyIncome', 'RentalIncome', 'InterestIncome', 'ServiceRevenue'
                    ]),
                    'fallback_concepts': concepts[:20]  # Top 20 as fallback
                }
            
            elif category == 'operating_cash_flow':
                universal_mapping['operating_cash_flow'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'NetCashProvidedByUsedInOperatingActivities',
                        'NetCashProvidedByOperatingActivities'
                    ]),
                    'fallback_concepts': concepts[:10]
                }
            
            elif category == 'net_income':
                universal_mapping['net_income'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'NetIncomeLoss', 'NetIncome', 'ProfitLoss'
                    ]),
                    'fallback_concepts': concepts[:10]
                }
            
            elif category == 'assets':
                universal_mapping['total_assets'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'Assets', 'TotalAssets'
                    ]),
                    'fallback_concepts': concepts[:15]
                }
            
            elif category == 'liabilities':
                universal_mapping['total_liabilities'] = {
                    'primary_concepts': self._rank_concepts_by_frequency(concepts, [
                        'Liabilities', 'TotalLiabilities'
                    ]),
                    'fallback_concepts': concepts[:15]
                }
        
        return universal_mapping


class EnhancedUniversalOrganizer(UnifiedDatasetOrganizer):
    """Enhanced organizer that uses universal concept mapping"""
    
    def __init__(self, cache_dir: str = "data/cache", output_dir: str = "data/unified"):
        super().__init__(cache_dir, output_dir)
        self.universal_mapper = UniversalConceptMapper()
        self.universal_concepts = None
        
    def initialize_universal_mapping(self):
        """Initialize universal concept mapping from all cached data"""
        print("🔄 Building universal concept mapping...")
        self.universal_concepts = self.universal_mapper.analyze_all_concepts(self.cache_dir)
        
        # Save universal mapping for reference
        mapping_file = os.path.join(self.output_dir, "universal_concept_mapping.json")
        with open(mapping_file, 'w') as f:
            json.dump(self.universal_concepts, f, indent=2)
        
        print(f"💾 Universal mapping saved to: {mapping_file}")
        
        return self.universal_concepts
    
    def _extract_financial_metrics(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Enhanced financial metrics extraction using universal mapping"""
        if self.universal_concepts is None:
            # Fall back to original method if universal mapping not available
            return super()._extract_financial_metrics(facts_df)
        
        financials = {}
        universal_mapping = self.universal_concepts['universal_mapping']
        
        # Use universal mapping for each metric
        for metric, mapping_config in universal_mapping.items():
            best_value = self._find_universal_concept_value(facts_df, mapping_config)
            financials[metric] = best_value
        
        # Calculate derived metrics
        financials['free_cash_flow'] = self._calculate_free_cash_flow(financials)
        financials['debt_to_assets'] = self._calculate_debt_to_assets(financials)
        financials['roa'] = self._calculate_roa(financials)
        
        # Add industry-specific metrics if detected
        financials.update(self._extract_industry_specific_metrics(facts_df))
        
        return financials
    
    def _find_universal_concept_value(self, facts_df: pd.DataFrame, mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """Find value using universal concept mapping"""
        result = {
            'value': None,
            'concept_used': None,
            'period': None,
            'confidence': 0,
            'alternatives': []
        }
        
        # Try primary concepts first
        primary_concepts = mapping_config.get('primary_concepts', [])
        for concept in primary_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    result.update({
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 9  # High confidence for primary concepts
                    })
                    return result
        
        # Try industry-specific concepts
        industry_concepts = mapping_config.get('industry_specific', [])
        for concept in industry_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    result.update({
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 7  # Medium confidence for industry-specific
                    })
                    return result
        
        # Try fallback concepts
        fallback_concepts = mapping_config.get('fallback_concepts', [])
        for concept in fallback_concepts[:10]:  # Limit fallback attempts
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    result.update({
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 5  # Lower confidence for fallback
                    })
                    return result
        
        return result
    
    def _extract_numeric_value(self, row: Dict[str, Any]) -> Optional[float]:
        """Extract numeric value from a fact row"""
        value = row.get('value', row.get('numeric_value', None))
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
        return None
    
    def _extract_industry_specific_metrics(self, facts_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract industry-specific metrics based on available concepts"""
        industry_metrics = {}
        
        # REIT-specific metrics
        reit_concepts = ['FundsFromOperations', 'AdjustedFundsFromOperations', 'PropertyIncome']
        for concept in reit_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    metric_name = concept.lower().replace('funds', '').replace('from', '').replace('operations', 'ffo')
                    industry_metrics[f"reit_{metric_name}"] = {
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 8
                    }
        
        # Bank-specific metrics
        bank_concepts = ['InterestIncome', 'InterestExpense', 'NonInterestIncome', 'ProvisionForLoanLosses']
        for concept in bank_concepts:
            concept_rows = facts_df[facts_df['concept'].str.contains(concept, case=False, na=False)]
            if len(concept_rows) > 0:
                best_row = self._select_best_fact_row(concept_rows)
                if best_row and self._extract_numeric_value(best_row):
                    metric_name = concept.lower().replace('interest', '').replace('income', '').replace('expense', '')
                    industry_metrics[f"bank_{metric_name}"] = {
                        'value': self._extract_numeric_value(best_row),
                        'concept_used': best_row['concept'],
                        'period': best_row.get('period', 'Unknown'),
                        'confidence': 8
                    }
        
        return industry_metrics
    
    def _rank_concepts_by_frequency(self, concepts: List[str], preferred_order: List[str]) -> List[str]:
        """Rank concepts by preferred order and frequency"""
        ranked = []
        
        # Add preferred concepts first (if they exist in the list)
        for preferred in preferred_order:
            matching = [c for c in concepts if preferred.lower() in c.lower()]
            ranked.extend(matching)
        
        # Add remaining concepts
        remaining = [c for c in concepts if c not in ranked]
        ranked.extend(remaining)
        
        return ranked


def main():
    """Enhanced main function with universal mapping"""
    # Create enhanced organizer
    organizer = EnhancedUniversalOrganizer()
    
    # Initialize universal mapping from all cached data
    print("🌍 Initializing universal concept mapping...")
    universal_concepts = organizer.initialize_universal_mapping()
    
    print(f"\n📊 Universal Mapping Summary:")
    print(f"   Total concepts analyzed: {universal_concepts['total_concepts']}")
    print(f"   Companies analyzed: {universal_concepts['total_tickers']}")
    print(f"   Categories mapped: {len(universal_concepts['universal_mapping'])}")
    
    # Process specific ticker (Realty Income example)
    print(f"\n🏢 Processing Realty Income (O) with universal mapping...")
    unified_data = organizer.process_ticker("O")
    
    if unified_data.get('quarters'):
        organizer.save_unified_dataset("O", unified_data)
        
        # Show summary
        print(f"\n📊 Summary for {unified_data['ticker']}:")
        print(f"   Company: {unified_data['company_name']}")
        print(f"   Quarters: {unified_data['summary']['total_quarters']}")
        print(f"   Date Range: {unified_data['summary']['date_range']}")
        print(f"   Overall Quality: {unified_data['summary']['data_quality']['overall_quality_score']:.1f}%")
        
        # Show recent quarter
        if unified_data['quarters']:
            recent = unified_data['quarters'][0]  # Most recent (sorted desc)
            print(f"\n📈 Most Recent Quarter ({recent['quarter']} {recent['year']}):")
            for metric, data in recent['financials'].items():
                if data.get('value') is not None:
                    value = data['value']
                    if abs(value) > 1000000:
                        formatted = f"${value/1000000:.1f}M"
                    elif abs(value) > 1000:
                        formatted = f"${value/1000:.1f}K"
                    else:
                        formatted = f"${value:.2f}"
                    print(f"      {metric}: {formatted} (confidence: {data.get('confidence', 0)})")
    
    # Process all tickers with universal mapping
    print(f"\n🌍 Processing all cached tickers with universal mapping...")
    organizer.process_all_tickers()


if __name__ == "__main__":
    main()