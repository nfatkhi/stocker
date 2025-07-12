# components/xbrl_extractor.py - Multi-row XBRL extractor with period_end filtering for clean cache

import json
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import Counter


@dataclass
class XBRLFactRow:
    """Single XBRL fact row with all context information"""
    concept: str
    value: Optional[str] = None
    numeric_value: Optional[float] = None
    context_ref: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    instant: Optional[str] = None
    unit_ref: Optional[str] = None
    decimals: Optional[str] = None
    dimensions: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


@dataclass
class MultiRowFinancialData:
    """Multi-row financial data with all fact rows for 49 universal concepts"""
    # Metadata
    ticker: str
    filing_date: str
    quarter: str
    year: int
    company_name: str
    
    # Document Entity Information (8 concepts) - Lists of fact rows
    dei_entity_central_index_key: List[XBRLFactRow] = None
    dei_document_fiscal_period_focus: List[XBRLFactRow] = None
    dei_document_fiscal_year_focus: List[XBRLFactRow] = None
    dei_document_period_end_date: List[XBRLFactRow] = None
    dei_document_type: List[XBRLFactRow] = None
    dei_entity_registrant_name: List[XBRLFactRow] = None
    dei_entity_common_stock_shares_outstanding: List[XBRLFactRow] = None
    dei_current_fiscal_year_end_date: List[XBRLFactRow] = None
    
    # Income Statement (10 concepts) - Lists of fact rows - UPDATED: Added 2 revenue concepts
    revenues: List[XBRLFactRow] = None
    revenue_from_contract_with_customer_excluding_assessed_tax: List[XBRLFactRow] = None
    research_and_development_expense: List[XBRLFactRow] = None
    selling_general_administrative_expense: List[XBRLFactRow] = None
    net_income_loss: List[XBRLFactRow] = None
    earnings_per_share_basic: List[XBRLFactRow] = None
    earnings_per_share_diluted: List[XBRLFactRow] = None
    weighted_average_shares_outstanding_basic: List[XBRLFactRow] = None
    weighted_average_shares_outstanding_diluted: List[XBRLFactRow] = None
    other_comprehensive_income_loss_net_of_tax: List[XBRLFactRow] = None
    
    # Balance Sheet - Assets (7 concepts) - Lists of fact rows
    cash_and_cash_equivalents: List[XBRLFactRow] = None
    accounts_receivable_net_current: List[XBRLFactRow] = None
    prepaid_expense_and_other_assets_current: List[XBRLFactRow] = None
    assets_current: List[XBRLFactRow] = None
    property_plant_equipment_net: List[XBRLFactRow] = None
    intangible_assets_net_excluding_goodwill: List[XBRLFactRow] = None
    assets_total: List[XBRLFactRow] = None
    
    # Balance Sheet - Liabilities & Equity (11 concepts) - Lists of fact rows
    accounts_payable_current: List[XBRLFactRow] = None
    liabilities_current: List[XBRLFactRow] = None
    long_term_debt_noncurrent: List[XBRLFactRow] = None
    other_liabilities_noncurrent: List[XBRLFactRow] = None
    liabilities_total: List[XBRLFactRow] = None
    common_stock_shares_authorized: List[XBRLFactRow] = None
    common_stock_shares_outstanding: List[XBRLFactRow] = None
    common_stock_value: List[XBRLFactRow] = None
    additional_paid_in_capital: List[XBRLFactRow] = None
    retained_earnings_accumulated_deficit: List[XBRLFactRow] = None
    stockholders_equity: List[XBRLFactRow] = None
    
    # Cash Flow Statement (8 concepts) - Lists of fact rows
    share_based_compensation: List[XBRLFactRow] = None
    net_cash_operating_activities: List[XBRLFactRow] = None
    payments_to_acquire_ppe: List[XBRLFactRow] = None
    net_cash_investing_activities: List[XBRLFactRow] = None
    net_cash_financing_activities: List[XBRLFactRow] = None
    cash_restricted_cash_equivalents: List[XBRLFactRow] = None
    increase_decrease_accounts_payable: List[XBRLFactRow] = None
    adjustments_additional_paid_in_capital_share_compensation: List[XBRLFactRow] = None
    
    # Other Important (5 concepts) - Lists of fact rows
    liabilities_and_stockholders_equity: List[XBRLFactRow] = None
    common_stock_par_stated_value_per_share: List[XBRLFactRow] = None
    accumulated_other_comprehensive_income_loss: List[XBRLFactRow] = None
    operating_lease_right_of_use_asset: List[XBRLFactRow] = None
    operating_lease_liability_noncurrent: List[XBRLFactRow] = None
    
    # Extraction metadata
    extraction_timestamp: str = ""
    concepts_extracted: int = 0
    total_fact_rows: int = 0
    extraction_success: bool = False
    most_common_period_end: str = ""  # NEW: Track the filtering period
    period_end_filtering_applied: bool = False  # NEW: Track if filtering was applied
    
    def __post_init__(self):
        # Initialize empty lists for None values - UPDATED: Added revenue fields
        for field_name, field_type in self.__annotations__.items():
            if field_name.startswith(('dei_', 'revenues', 'revenue_from_contract', 'research_', 'selling_', 'net_', 'earnings_', 'weighted_', 'other_comprehensive',
                                   'cash_', 'accounts_', 'prepaid_', 'assets_', 'property_', 'intangible_',
                                   'liabilities_', 'long_term_', 'common_stock_', 'additional_', 'retained_', 'stockholders_',
                                   'share_based_', 'payments_', 'increase_', 'adjustments_', 'accumulated_', 'operating_')):
                if getattr(self, field_name) is None:
                    setattr(self, field_name, [])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary with fact rows as dicts"""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, list) and value and isinstance(value[0], dict):
                result[key] = value  # Already dict format
            elif isinstance(value, list) and value and hasattr(value[0], 'to_dict'):
                result[key] = [fact.to_dict() for fact in value]
            else:
                result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary with fact rows"""
        # Convert fact row dicts back to XBRLFactRow objects
        converted_data = {}
        for key, value in data.items():
            if isinstance(value, list) and value and isinstance(value[0], dict) and 'concept' in value[0]:
                converted_data[key] = [XBRLFactRow.from_dict(fact_dict) for fact_dict in value]
            else:
                converted_data[key] = value
        return cls(**converted_data)


class MultiRowXBRLExtractor:
    """Extract all fact rows for 49 universal XBRL concepts with period_end filtering"""
    
    def __init__(self):
        # 49 Universal concepts mapping to field names - UPDATED: Added 2 revenue concepts
        self.concept_mappings = {
            # Document Entity Information (8 concepts)
            'dei_entity_central_index_key': 'dei:EntityCentralIndexKey',
            'dei_document_fiscal_period_focus': 'dei:DocumentFiscalPeriodFocus',
            'dei_document_fiscal_year_focus': 'dei:DocumentFiscalYearFocus',
            'dei_document_period_end_date': 'dei:DocumentPeriodEndDate',
            'dei_document_type': 'dei:DocumentType',
            'dei_entity_registrant_name': 'dei:EntityRegistrantName',
            'dei_entity_common_stock_shares_outstanding': 'dei:EntityCommonStockSharesOutstanding',
            'dei_current_fiscal_year_end_date': 'dei:CurrentFiscalYearEndDate',
            
            # Income Statement (10 concepts) - UPDATED: Added revenue concepts
            'revenues': 'us-gaap:Revenues',
            'revenue_from_contract_with_customer_excluding_assessed_tax': 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax',
            'research_and_development_expense': 'us-gaap:ResearchAndDevelopmentExpense',
            'selling_general_administrative_expense': 'us-gaap:SellingGeneralAndAdministrativeExpense',
            'net_income_loss': 'us-gaap:NetIncomeLoss',
            'earnings_per_share_basic': 'us-gaap:EarningsPerShareBasic',
            'earnings_per_share_diluted': 'us-gaap:EarningsPerShareDiluted',
            'weighted_average_shares_outstanding_basic': 'us-gaap:WeightedAverageNumberOfSharesOutstandingBasic',
            'weighted_average_shares_outstanding_diluted': 'us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding',
            'other_comprehensive_income_loss_net_of_tax': 'us-gaap:OtherComprehensiveIncomeLossNetOfTax',
            
            # Balance Sheet - Assets (7 concepts)
            'cash_and_cash_equivalents': 'us-gaap:CashAndCashEquivalentsAtCarryingValue',
            'accounts_receivable_net_current': 'us-gaap:AccountsReceivableNetCurrent',
            'prepaid_expense_and_other_assets_current': 'us-gaap:PrepaidExpenseAndOtherAssetsCurrent',
            'assets_current': 'us-gaap:AssetsCurrent',
            'property_plant_equipment_net': 'us-gaap:PropertyPlantAndEquipmentNet',
            'intangible_assets_net_excluding_goodwill': 'us-gaap:IntangibleAssetsNetExcludingGoodwill',
            'assets_total': 'us-gaap:Assets',
            
            # Balance Sheet - Liabilities & Equity (11 concepts)
            'accounts_payable_current': 'us-gaap:AccountsPayableCurrent',
            'liabilities_current': 'us-gaap:LiabilitiesCurrent',
            'long_term_debt_noncurrent': 'us-gaap:LongTermDebtNoncurrent',
            'other_liabilities_noncurrent': 'us-gaap:OtherLiabilitiesNoncurrent',
            'liabilities_total': 'us-gaap:Liabilities',
            'common_stock_shares_authorized': 'us-gaap:CommonStockSharesAuthorized',
            'common_stock_shares_outstanding': 'us-gaap:CommonStockSharesOutstanding',
            'common_stock_value': 'us-gaap:CommonStockValue',
            'additional_paid_in_capital': 'us-gaap:AdditionalPaidInCapital',
            'retained_earnings_accumulated_deficit': 'us-gaap:RetainedEarningsAccumulatedDeficit',
            'stockholders_equity': 'us-gaap:StockholdersEquity',
            
            # Cash Flow Statement (8 concepts)
            'share_based_compensation': 'us-gaap:ShareBasedCompensation',
            'net_cash_operating_activities': 'us-gaap:NetCashProvidedByUsedInOperatingActivities',
            'payments_to_acquire_ppe': 'us-gaap:PaymentsToAcquirePropertyPlantAndEquipment',
            'net_cash_investing_activities': 'us-gaap:NetCashProvidedByUsedInInvestingActivities',
            'net_cash_financing_activities': 'us-gaap:NetCashProvidedByUsedInFinancingActivities',
            'cash_restricted_cash_equivalents': 'us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents',
            'increase_decrease_accounts_payable': 'us-gaap:IncreaseDecreaseInAccountsPayable',
            'adjustments_additional_paid_in_capital_share_compensation': 'us-gaap:AdjustmentsToAdditionalPaidInCapitalSharebasedCompensationRequisiteServicePeriodRecognitionValue',
            
            # Other Important (5 concepts)
            'liabilities_and_stockholders_equity': 'us-gaap:LiabilitiesAndStockholdersEquity',
            'common_stock_par_stated_value_per_share': 'us-gaap:CommonStockParOrStatedValuePerShare',
            'accumulated_other_comprehensive_income_loss': 'us-gaap:AccumulatedOtherComprehensiveIncomeLossNetOfTax',
            'operating_lease_right_of_use_asset': 'us-gaap:OperatingLeaseRightOfUseAsset',
            'operating_lease_liability_noncurrent': 'us-gaap:OperatingLeaseLiabilityNoncurrent'
        }
    
    def extract_multi_row_data(self, raw_filing) -> MultiRowFinancialData:
        """Extract all fact rows for 49 universal concepts with period_end filtering"""
        
        print(f"🔧 Multi-row extraction for {raw_filing.ticker} - {raw_filing.filing_date}")
        print(f"📊 Extracting ALL rows for 49 universal concepts with period_end filtering")
        
        multi_row_data = MultiRowFinancialData(
            ticker=raw_filing.ticker,
            filing_date=raw_filing.filing_date,
            quarter="Unknown",
            year=0,
            company_name=raw_filing.company_name,
            extraction_timestamp=datetime.now().isoformat()
        )
        
        if not raw_filing.facts_json:
            print(f"❌ No facts_json data available")
            multi_row_data.extraction_success = False
            return multi_row_data
        
        try:
            facts_data = json.loads(raw_filing.facts_json)
            
            if not facts_data:
                print(f"❌ Empty facts data after JSON parsing")
                multi_row_data.extraction_success = False
                return multi_row_data
            
            facts_df = pd.DataFrame(facts_data)
            print(f"📊 Processing {len(facts_df)} total facts for 49 universal concepts...")
            
            # NEW: Find most common period_end across ALL facts for filtering
            most_common_period_end = self._find_most_common_period_end(facts_df)
            
            if most_common_period_end:
                print(f"🎯 Most common period_end: {most_common_period_end}")
                print(f"📅 Will filter to this period_end + include null/empty values")
                multi_row_data.most_common_period_end = most_common_period_end
                multi_row_data.period_end_filtering_applied = True
            else:
                print(f"⚠️ No common period_end found - extracting all facts (including nulls)")
                multi_row_data.period_end_filtering_applied = False
            
            concepts_extracted = 0
            total_fact_rows = 0
            
            # Extract all fact rows for each of the 49 concepts with filtering
            for field_name, xbrl_concept in self.concept_mappings.items():
                fact_rows = self._extract_all_concept_rows_filtered(
                    facts_df, xbrl_concept, field_name, most_common_period_end
                )
                
                if fact_rows:
                    setattr(multi_row_data, field_name, fact_rows)
                    concepts_extracted += 1
                    total_fact_rows += len(fact_rows)
                    print(f"   ✅ {field_name}: {len(fact_rows)} fact rows (filtered)")
                else:
                    print(f"   ❌ {field_name}: No fact rows found after filtering")
            
            # Try to extract quarter/year from DEI concepts
            quarter, year = self._extract_quarter_year_from_dei(multi_row_data)
            multi_row_data.quarter = quarter
            multi_row_data.year = year
            
            # Set extraction results
            multi_row_data.concepts_extracted = concepts_extracted
            multi_row_data.total_fact_rows = total_fact_rows
            multi_row_data.extraction_success = concepts_extracted >= 20  # At least 20/49 concepts
            
            print(f"📊 Multi-row extraction complete:")
            print(f"   Concepts extracted: {concepts_extracted}/49")
            print(f"   Total fact rows: {total_fact_rows} (filtered to period_end: {most_common_period_end} + nulls)")
            print(f"   Success: {multi_row_data.extraction_success}")
            
            return multi_row_data
            
        except Exception as e:
            print(f"❌ Error in multi-row extraction: {e}")
            import traceback
            traceback.print_exc()
            multi_row_data.extraction_success = False
            return multi_row_data
    
    def _find_most_common_period_end(self, facts_df: pd.DataFrame) -> Optional[str]:
        """
        Find the most common period_end date across ALL facts in the filing
        Note: Ignores null/empty values for determining the main period, but these will still be included
        
        Args:
            facts_df: DataFrame containing all facts
            
        Returns:
            Most common period_end date string, or None if no valid dates
        """
        if 'period_end' not in facts_df.columns:
            print("   ⚠️ No period_end column found in facts DataFrame")
            return None
        
        # Extract all period_end dates, excluding null/empty values for analysis
        period_ends = []
        null_count = 0
        
        for _, row in facts_df.iterrows():
            period_end = row.get('period_end')
            
            # Check if period_end is null/empty
            if (pd.isna(period_end) or 
                period_end is None or 
                str(period_end).strip() in ['', 'None', 'null', 'N/A', 'nan']):
                null_count += 1
                continue
            
            period_ends.append(str(period_end).strip())
        
        if not period_ends:
            print(f"   ⚠️ No valid period_end dates found in facts ({null_count} null/empty values)")
            return None
        
        # Find most common date
        date_counter = Counter(period_ends)
        most_common_date, most_common_count = date_counter.most_common(1)[0]
        
        print(f"   📅 Period_end analysis: {len(date_counter)} unique dates, {null_count} null/empty values")
        print(f"   🎯 Most common period_end: {most_common_date} ({most_common_count} facts)")
        print(f"   📊 Null/empty period_end facts: {null_count} (will be included)")
        
        if len(date_counter) > 1:
            print(f"   📊 Other period_end dates found:")
            for date, count in sorted(date_counter.items(), key=lambda x: x[1], reverse=True)[1:6]:  # Show top 5 others
                print(f"      {date}: {count} facts")
        
        return most_common_date
    
    def _extract_all_concept_rows_filtered(self, facts_df: pd.DataFrame, xbrl_concept: str, 
                                         field_name: str, filter_period_end: Optional[str]) -> List[XBRLFactRow]:
        """Extract ALL fact rows for a specific XBRL concept, filtered by period_end (including null values)"""
        
        if 'concept' not in facts_df.columns:
            return []
        
        # Find all rows with this concept
        concept_matches = facts_df[facts_df['concept'] == xbrl_concept]
        
        if len(concept_matches) == 0:
            return []
        
        # NEW: Apply period_end filtering if available, but INCLUDE null/empty values
        if filter_period_end and 'period_end' in concept_matches.columns:
            original_count = len(concept_matches)
            
            # Create filter that includes:
            # 1. Facts matching the most common period_end
            # 2. Facts with null/empty period_end values (these might be important metadata or instant facts)
            period_end_filter = (
                (concept_matches['period_end'] == filter_period_end) |
                (concept_matches['period_end'].isna()) |
                (concept_matches['period_end'].isnull()) |
                (concept_matches['period_end'] == '') |
                (concept_matches['period_end'] == 'None') |
                (concept_matches['period_end'] == 'null') |
                (concept_matches['period_end'] == 'N/A') |
                (concept_matches['period_end'] == 'nan')
            )
            
            concept_matches = concept_matches[period_end_filter]
            filtered_count = len(concept_matches)
            null_count = original_count - len(facts_df[facts_df['concept'] == xbrl_concept][facts_df[facts_df['concept'] == xbrl_concept]['period_end'] == filter_period_end])
            
            if original_count > filtered_count:
                print(f"      🎯 {field_name}: Filtered {original_count} → {filtered_count} facts (kept {null_count} null period_end)")
        
        if len(concept_matches) == 0:
            return []
        
        fact_rows = []
        
        for _, row in concept_matches.iterrows():
            # Parse numeric value
            numeric_value = self._parse_numeric_value(row)
            
            # Extract all available columns into fact row
            fact_row = XBRLFactRow(
                concept=xbrl_concept,
                value=str(row.get('value', '')),
                numeric_value=numeric_value,
                context_ref=str(row.get('context_ref', '')),
                period_start=str(row.get('period_start', '')),
                period_end=str(row.get('period_end', '')),
                instant=str(row.get('instant', '')),
                unit_ref=str(row.get('unit_ref', '')),
                decimals=str(row.get('decimals', '')),
                dimensions=self._extract_dimensions(row)
            )
            
            fact_rows.append(fact_row)
        
        return fact_rows
    
    def _parse_numeric_value(self, row: pd.Series) -> Optional[float]:
        """Parse numeric value from fact row"""
        value_columns = ['numeric_value', 'value', 'amount']
        
        for col in value_columns:
            if col in row.index and pd.notna(row[col]):
                try:
                    value = row[col]
                    if isinstance(value, (int, float)):
                        return float(value)
                    elif isinstance(value, str):
                        clean_value = value.replace(',', '').replace('(', '-').replace(')', '').strip()
                        if clean_value.replace('.', '').replace('-', '').isdigit():
                            return float(clean_value)
                except (ValueError, TypeError):
                    continue
        return None
    
    def _extract_dimensions(self, row: pd.Series) -> Optional[Dict]:
        """Extract dimension information from fact row"""
        dimensions = {}
        
        # Look for dimension-related columns
        for col in row.index:
            if 'dimension' in str(col).lower() or 'axis' in str(col).lower():
                if pd.notna(row[col]):
                    dimensions[col] = str(row[col])
        
        return dimensions if dimensions else None
    
    def _extract_quarter_year_from_dei(self, multi_row_data: MultiRowFinancialData) -> Tuple[str, int]:
        """Extract quarter and year from DEI concepts"""
        quarter = "Unknown"
        year = 0
        
        # Try to get quarter from DocumentFiscalPeriodFocus
        if multi_row_data.dei_document_fiscal_period_focus:
            for fact_row in multi_row_data.dei_document_fiscal_period_focus:
                if fact_row.value and fact_row.value.strip():
                    quarter = fact_row.value.strip()
                    if quarter == "FY":
                        quarter = "Q4"
                    break
        
        # Try to get year from DocumentFiscalYearFocus
        if multi_row_data.dei_document_fiscal_year_focus:
            for fact_row in multi_row_data.dei_document_fiscal_year_focus:
                try:
                    if fact_row.numeric_value:
                        year = int(fact_row.numeric_value)
                        break
                    elif fact_row.value and fact_row.value.strip().isdigit():
                        year = int(fact_row.value.strip())
                        break
                except (ValueError, TypeError):
                    continue
        
        return quarter, year


# Global instance
_multi_row_extractor_instance = MultiRowXBRLExtractor()


def extract_multi_row_financials(raw_filing) -> MultiRowFinancialData:
    """Extract 49 universal concepts with all fact rows and period_end filtering"""
    return _multi_row_extractor_instance.extract_multi_row_data(raw_filing)


if __name__ == "__main__":
    print("🧪 Testing Multi-Row XBRL Extractor with Period End Filtering")
    print("=" * 60)
    
    # Test the concept mappings
    extractor = MultiRowXBRLExtractor()
    print(f"📊 Configured for {len(extractor.concept_mappings)} universal concepts:")
    
    categories = {
        'DEI': [k for k in extractor.concept_mappings.keys() if k.startswith('dei_')],
        'Income': [k for k in extractor.concept_mappings.keys() if any(k.startswith(x) for x in ['revenues', 'revenue_from_contract', 'research_', 'selling_', 'net_', 'earnings_', 'weighted_', 'other_comprehensive'])],
        'Assets': [k for k in extractor.concept_mappings.keys() if any(k.startswith(x) for x in ['cash_', 'accounts_receivable', 'prepaid_', 'assets_', 'property_', 'intangible_'])],
        'Liab/Equity': [k for k in extractor.concept_mappings.keys() if any(k.startswith(x) for x in ['liabilities_', 'long_term_', 'common_stock_', 'additional_', 'retained_', 'stockholders_'])],
        'Cash Flow': [k for k in extractor.concept_mappings.keys() if any(k.startswith(x) for x in ['share_based_', 'net_cash_', 'payments_', 'increase_', 'adjustments_'])],
        'Other': [k for k in extractor.concept_mappings.keys() if any(k.startswith(x) for x in ['accumulated_', 'operating_'])]
    }
    
    for category, concepts in categories.items():
        print(f"   {category}: {len(concepts)} concepts")
    
    print(f"\n✅ Multi-row extractor ready for 49 universal concepts!")
    print(f"🎯 NEW: Period_end filtering applied at extraction level")
    print(f"📅 Most common period_end facts + null/empty period_end facts included")
    print(f"🔄 Each concept will collect matching fact rows for main period + nulls")
    print(f"📊 Complete context information preserved for each fact")
    print(f"💾 Cache files will be cleaner while preserving important null data")