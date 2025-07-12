# components/charts/revenue/revenue_data_processor.py - FIXED revenue selection with period_end consistency

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math
from collections import Counter


@dataclass
class ProcessedRevenueData:
    """Processed revenue data for chart consumption"""
    date: str
    revenue: float
    revenues: float  # Alias for compatibility
    quarter: str
    year: int
    filing_date: str
    document_fiscal_period_focus: str
    document_fiscal_year_focus: int
    
    # Revenue source metadata
    revenues_source: str  # 'quarterly_10q' or 'annual_10k'
    revenues_period_days: int  # Number of days in period
    revenues_needs_q4_calculation: bool = False
    revenues_value_selection: str = ""  # How value was selected
    
    # Compatibility for existing chart code
    def __getattr__(self, name):
        if name in ['revenue', 'revenues']:
            return self.revenue
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


class RevenueDataProcessor:
    """Process multi-row cache data into clean revenue data for charts"""
    
    def __init__(self):
        self.verbose = True
    
    def process_revenue_data(self, quarterly_cache_data: List[Dict]) -> List[ProcessedRevenueData]:
        """
        Process multi-row cache data into clean revenue data
        
        Args:
            quarterly_cache_data: List of quarter dicts from multi-row cache
            
        Returns:
            List of ProcessedRevenueData objects ready for charts
        """
        if self.verbose:
            print(f"🔄 Processing {len(quarterly_cache_data)} quarters for revenue data")
        
        processed_data = []
        
        for quarter_data in quarterly_cache_data:
            revenue_result = self._process_quarter_revenue(quarter_data)
            if revenue_result:
                processed_data.append(revenue_result)
        
        if self.verbose:
            print(f"✅ Processed {len(processed_data)} quarters with revenue data")
            
        return processed_data
    
    def _process_quarter_revenue(self, quarter_data: Dict) -> Optional[ProcessedRevenueData]:
        """Process revenue data for a single quarter"""
        
        ticker = quarter_data.get('ticker', 'UNKNOWN')
        filing_date = quarter_data.get('filing_date', '')
        quarter = quarter_data.get('quarter', 'Unknown')
        year = quarter_data.get('year', 0)
        
        if self.verbose:
            print(f"   📊 Processing {ticker} {quarter} {year} ({filing_date})")
        
        # Check BOTH revenue concepts and select larger value
        revenues_1 = quarter_data.get('revenues', [])
        revenues_2 = quarter_data.get('revenue_from_contract_with_customer_excluding_assessed_tax', [])
        
        # Get best value from each concept
        concept_1_result = None
        concept_2_result = None
        
        if revenues_1:
            concept_1_result = self._select_best_revenue_value(revenues_1)
            if concept_1_result[0] and self.verbose:
                print(f"      📊 Concept 1 (revenues): {len(revenues_1)} facts → ${concept_1_result[0]/1e6:.1f}M")
            elif self.verbose:
                print(f"      📊 Concept 1 (revenues): {len(revenues_1)} facts → No valid value")
        
        if revenues_2:
            concept_2_result = self._select_best_revenue_value(revenues_2)
            if concept_2_result[0] and self.verbose:
                print(f"      📊 Concept 2 (revenue_from_contract...): {len(revenues_2)} facts → ${concept_2_result[0]/1e6:.1f}M")
            elif self.verbose:
                print(f"      📊 Concept 2 (revenue_from_contract...): {len(revenues_2)} facts → No valid value")
        
        # Select the larger value between the two concepts
        revenue_value = None
        selection_method = ""
        period_classification = "unknown"
        period_days = 0
        
        if concept_1_result and concept_1_result[0] and concept_2_result and concept_2_result[0]:
            # Both concepts have values - select larger
            if concept_1_result[0] >= concept_2_result[0]:
                revenue_value, selection_method, period_classification, period_days = concept_1_result
                selection_method = f"concept1_larger_{selection_method}"
                if self.verbose:
                    print(f"      🎯 Selected Concept 1 (larger): ${revenue_value/1e6:.1f}M vs ${concept_2_result[0]/1e6:.1f}M")
            else:
                revenue_value, selection_method, period_classification, period_days = concept_2_result
                selection_method = f"concept2_larger_{selection_method}"
                if self.verbose:
                    print(f"      🎯 Selected Concept 2 (larger): ${revenue_value/1e6:.1f}M vs ${concept_1_result[0]/1e6:.1f}M")
        elif concept_1_result and concept_1_result[0]:
            # Only concept 1 has value
            revenue_value, selection_method, period_classification, period_days = concept_1_result
            selection_method = f"concept1_only_{selection_method}"
            if self.verbose:
                print(f"      📊 Using Concept 1 (only available): ${revenue_value/1e6:.1f}M")
        elif concept_2_result and concept_2_result[0]:
            # Only concept 2 has value
            revenue_value, selection_method, period_classification, period_days = concept_2_result
            selection_method = f"concept2_only_{selection_method}"
            if self.verbose:
                print(f"      📊 Using Concept 2 (only available): ${revenue_value/1e6:.1f}M")
        else:
            # No valid revenue found
            if self.verbose:
                print(f"      ❌ No valid revenue values found in either concept")
            return None
        
        if revenue_value is None or math.isnan(revenue_value):
            if self.verbose:
                print(f"      ❌ No valid revenue value found")
            return None
        
        # Determine if Q4 calculation needed
        needs_q4_calc = (period_classification == 'annual' and quarter == 'Q4')
        
        if self.verbose:
            print(f"      ✅ Final Revenue: ${revenue_value/1e6:.1f}M ({period_classification}, {period_days} days)")
            print(f"         Selection: {selection_method}")
            if needs_q4_calc:
                print(f"         Q4 calculation needed: {needs_q4_calc}")
        
        # Create processed data
        processed = ProcessedRevenueData(
            date=filing_date,
            revenue=revenue_value,
            revenues=revenue_value,
            quarter=quarter,
            year=year,
            filing_date=filing_date,
            document_fiscal_period_focus=quarter,
            document_fiscal_year_focus=year,
            revenues_source=f"{period_classification}_{'10k' if period_classification == 'annual' else '10q'}",
            revenues_period_days=period_days,
            revenues_needs_q4_calculation=needs_q4_calc,
            revenues_value_selection=selection_method
        )
        
        return processed
    
    def _find_most_common_period_end(self, revenue_facts: List[Dict]) -> Optional[str]:
        """
        Find the most common period_end date across all revenue facts
        
        Args:
            revenue_facts: List of revenue fact dictionaries
            
        Returns:
            Most common period_end date string, or None if no valid dates
        """
        if not revenue_facts:
            return None
        
        # Extract all period_end dates
        period_ends = []
        for fact in revenue_facts:
            period_end = fact.get('period_end')
            if period_end and period_end != 'None' and period_end.strip():
                period_ends.append(period_end.strip())
        
        if not period_ends:
            return None
        
        # Find most common date
        date_counter = Counter(period_ends)
        most_common_date = date_counter.most_common(1)[0][0]
        
        if self.verbose and len(date_counter) > 1:
            print(f"      📅 Multiple period_end dates found: {dict(date_counter)}")
            print(f"      🎯 Using most common: {most_common_date}")
        
        return most_common_date
    
    def _select_best_revenue_value(self, revenue_facts: List[Dict]) -> Tuple[Optional[float], str, str, int]:
        """
        FIXED: Select best revenue value with period_end consistency
        
        NEW LOGIC:
        1. Find most common period_end date across all facts
        2. Filter facts to only those with that period_end date
        3. Apply existing selection priority on filtered facts
        
        Priority (after filtering):
        1. Quarterly consolidated (< 120 days, no dimensions)
        2. Annual consolidated (≥ 120 days, no dimensions) 
        3. Quarterly with dimensions (< 120 days)
        4. Annual with dimensions (≥ 120 days)
        
        Returns:
            (revenue_value, selection_method, period_classification, period_days)
        """
        
        if not revenue_facts:
            return float('nan'), "no_facts", "unknown", 0
        
        # STEP 1: Find most common period_end date
        most_common_period_end = self._find_most_common_period_end(revenue_facts)
        
        if not most_common_period_end:
            if self.verbose:
                print(f"      ❌ No valid period_end dates found")
            return float('nan'), "no_valid_period_end", "unknown", 0
        
        # STEP 2: Filter facts to only those with the most common period_end
        filtered_facts = []
        for fact in revenue_facts:
            period_end = fact.get('period_end', '').strip()
            if period_end == most_common_period_end:
                filtered_facts.append(fact)
        
        if not filtered_facts:
            if self.verbose:
                print(f"      ❌ No facts match most common period_end: {most_common_period_end}")
            return float('nan'), "no_facts_matching_period_end", "unknown", 0
        
        if self.verbose:
            print(f"      📅 Filtered to {len(filtered_facts)}/{len(revenue_facts)} facts with period_end: {most_common_period_end}")
        
        # STEP 3: Apply existing selection logic on filtered facts
        classified_facts = []
        
        for fact in filtered_facts:
            period_start = fact.get('period_start', '')
            period_end = fact.get('period_end', '')
            numeric_value = fact.get('numeric_value')
            dimensions = fact.get('dimensions')
            
            # Calculate period length
            period_days = self._calculate_period_days(period_start, period_end)
            
            # Classify as quarterly or annual
            if period_days > 0 and period_days < 120:
                period_classification = 'quarterly'
            elif period_days >= 120:
                period_classification = 'annual'
            else:
                period_classification = 'unknown'
            
            # Check if this is consolidated (no dimensions)
            is_consolidated = (dimensions is None or len(dimensions) == 0)
            
            classified_facts.append({
                'numeric_value': numeric_value,
                'period_days': period_days,
                'period_classification': period_classification,
                'is_consolidated': is_consolidated,
                'dimensions': dimensions,
                'fact': fact
            })
        
        # Filter valid facts
        valid_facts = [f for f in classified_facts if f['numeric_value'] is not None and f['numeric_value'] > 0]
        
        if not valid_facts:
            if self.verbose:
                print(f"      ❌ No valid numeric values in filtered facts")
            return float('nan'), "no_valid_values_after_filter", "unknown", 0
        
        # Apply selection priority on filtered facts
        consolidated_facts = [f for f in valid_facts if f['is_consolidated']]
        
        if consolidated_facts:
            # Prefer quarterly over annual within consolidated facts
            quarterly_consolidated = [f for f in consolidated_facts if f['period_classification'] == 'quarterly']
            
            if quarterly_consolidated:
                best_fact = max(quarterly_consolidated, key=lambda x: x['numeric_value'])
                selection_method = f"quarterly_consolidated_filtered_of_{len(quarterly_consolidated)}"
            else:
                annual_consolidated = [f for f in consolidated_facts if f['period_classification'] == 'annual']
                if annual_consolidated:
                    best_fact = max(annual_consolidated, key=lambda x: x['numeric_value'])
                    selection_method = f"annual_consolidated_filtered_of_{len(annual_consolidated)}"
                else:
                    best_fact = max(consolidated_facts, key=lambda x: x['numeric_value'])
                    selection_method = f"consolidated_unknown_period_filtered_of_{len(consolidated_facts)}"
        else:
            # No consolidated facts, look at facts with dimensions
            quarterly_with_dims = [f for f in valid_facts if f['period_classification'] == 'quarterly']
            
            if quarterly_with_dims:
                best_fact = max(quarterly_with_dims, key=lambda x: x['numeric_value'])
                selection_method = f"quarterly_with_dimensions_filtered_of_{len(quarterly_with_dims)}"
            else:
                annual_with_dims = [f for f in valid_facts if f['period_classification'] == 'annual']
                if annual_with_dims:
                    best_fact = max(annual_with_dims, key=lambda x: x['numeric_value'])
                    selection_method = f"annual_with_dimensions_filtered_of_{len(annual_with_dims)}"
                else:
                    best_fact = max(valid_facts, key=lambda x: x['numeric_value'])
                    selection_method = f"fallback_any_valid_filtered_of_{len(valid_facts)}"
        
        return (
            best_fact['numeric_value'],
            selection_method,
            best_fact['period_classification'],
            best_fact['period_days']
        )
    
    def _calculate_period_days(self, period_start: str, period_end: str) -> int:
        """Calculate number of days in period"""
        
        if not period_start or not period_end or period_start == 'None' or period_end == 'None':
            return 0
        
        try:
            start_date = self._parse_date(period_start)
            end_date = self._parse_date(period_end)
            
            if start_date and end_date:
                delta = end_date - start_date
                return delta.days
            else:
                return 0
                
        except Exception:
            return 0
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string into datetime object"""
        
        if not date_str or date_str == 'None':
            return None
        
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None


# Interface function for charts
def get_processed_revenue_data(quarterly_cache_data: List[Dict]) -> List[ProcessedRevenueData]:
    """
    Main interface function to get processed revenue data for charts
    
    Args:
        quarterly_cache_data: Multi-row cache data from cache manager
        
    Returns:
        List of ProcessedRevenueData objects ready for revenue charts
    """
    processor = RevenueDataProcessor()
    return processor.process_revenue_data(quarterly_cache_data)