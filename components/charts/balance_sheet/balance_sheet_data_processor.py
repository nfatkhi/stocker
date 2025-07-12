# components/charts/balance_sheet/balance_sheet_data_processor.py - Balance sheet data processing with financial ratios

import math
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass


class BalanceSheetDataPoint(NamedTuple):
    """Balance sheet quarter data with financial ratios"""
    quarter_label: str
    date: str
    
    # Core balance sheet items (in dollars)
    total_assets: float = float('nan')
    current_assets: float = float('nan')
    cash_and_equivalents: float = float('nan')
    
    total_liabilities: float = float('nan')
    current_liabilities: float = float('nan')
    long_term_debt: float = float('nan')
    
    stockholders_equity: float = float('nan')
    
    # Calculated ratios
    current_ratio: float = float('nan')
    quick_ratio: float = float('nan')
    debt_to_equity: float = float('nan')
    debt_to_assets: float = float('nan')
    equity_ratio: float = float('nan')
    cash_ratio: float = float('nan')
    
    # Data quality indicators
    data_source: str = "Cache"
    calculation_method: str = "direct"


@dataclass
class BalanceSheetMetrics:
    """Summary metrics for balance sheet analysis"""
    latest_total_assets: float
    latest_equity: float
    latest_debt: float
    latest_current_ratio: float
    latest_debt_to_equity: float
    
    avg_current_ratio: float
    avg_debt_to_equity: float
    
    total_quarters: int
    data_quality: str
    financial_strength: str  # Strong/Moderate/Weak based on ratios


class BalanceSheetDataProcessor:
    """Process multi-row XBRL cache data into balance sheet metrics and ratios"""
    
    def __init__(self):
        # Balance sheet concept mappings
        self.asset_concepts = {
            'total_assets': 'assets_total',
            'current_assets': 'assets_current', 
            'cash_and_equivalents': 'cash_and_cash_equivalents'
        }
        
        self.liability_concepts = {
            'current_liabilities': 'liabilities_current',
            'long_term_debt': 'long_term_debt_noncurrent'
        }
        
        self.equity_concepts = {
            'stockholders_equity': 'stockholders_equity'
        }
    
    def process_balance_sheet_data(self, financial_data: List[Any], max_quarters: int = 12) -> Tuple[List[BalanceSheetDataPoint], BalanceSheetMetrics]:
        """
        Process financial data into balance sheet data points with ratios
        
        Args:
            financial_data: List of MultiRowFinancialData objects from cache
            max_quarters: Maximum quarters to process
            
        Returns:
            Tuple of (processed data points, summary metrics)
        """
        print(f"🔄 Processing {len(financial_data)} quarters for balance sheet analysis")
        
        # Extract balance sheet data points
        data_points = self._extract_balance_sheet_points(financial_data[:max_quarters])
        
        # Calculate financial ratios
        data_points_with_ratios = self._calculate_financial_ratios(data_points)
        
        # Generate summary metrics
        metrics = self._calculate_summary_metrics(data_points_with_ratios)
        
        print(f"✅ Processed {len(data_points_with_ratios)} quarters with balance sheet data")
        return data_points_with_ratios, metrics
    
    def _extract_balance_sheet_points(self, financial_data: List[Any]) -> List[BalanceSheetDataPoint]:
        """Extract balance sheet data points from financial data"""
        data_points = []
        
        for financial in reversed(financial_data):  # Reverse to get chronological order
            # Extract quarter and date information
            quarter_label = self._extract_quarter_label(financial)
            date = getattr(financial, 'filing_date', '')
            
            # Extract balance sheet components
            assets = self._extract_balance_sheet_components(financial, self.asset_concepts)
            liabilities = self._extract_balance_sheet_components(financial, self.liability_concepts)
            equity = self._extract_balance_sheet_components(financial, self.equity_concepts)
            
            # Create data point
            data_point = BalanceSheetDataPoint(
                quarter_label=quarter_label,
                date=date,
                total_assets=assets.get('total_assets', float('nan')),
                current_assets=assets.get('current_assets', float('nan')),
                cash_and_equivalents=assets.get('cash_and_equivalents', float('nan')),
                current_liabilities=liabilities.get('current_liabilities', float('nan')),
                long_term_debt=liabilities.get('long_term_debt', float('nan')),
                stockholders_equity=equity.get('stockholders_equity', float('nan')),
                data_source="Cache"
            )
            
            data_points.append(data_point)
            
            # Debug output
            if not math.isnan(data_point.total_assets):
                print(f"   📊 {quarter_label}: Assets ${data_point.total_assets/1e9:.1f}B, Equity ${data_point.stockholders_equity/1e9:.1f}B")
        
        return data_points
    
    def _extract_quarter_label(self, financial: Any) -> str:
        """Extract quarter label from financial data"""
        # Try XBRL quarter information first
        xbrl_quarter = getattr(financial, 'quarter', None)
        xbrl_year = getattr(financial, 'year', None)
        
        if xbrl_quarter and xbrl_year and xbrl_quarter != "Unknown":
            return f"{xbrl_year}{xbrl_quarter}"
        
        # Fallback to parsing from date
        date = getattr(financial, 'filing_date', '')
        if date:
            try:
                year = date[:4]
                month = int(date[5:7])
                
                if month <= 3:
                    return f"{year}Q1"
                elif month <= 6:
                    return f"{year}Q2"
                elif month <= 9:
                    return f"{year}Q3"
                else:
                    return f"{year}Q4"
            except:
                pass
        
        return "Unknown"
    
    def _extract_balance_sheet_components(self, financial: Any, concept_mapping: Dict[str, str]) -> Dict[str, float]:
        """Extract balance sheet components from multi-row financial data"""
        results = {}
        
        for result_key, concept_field in concept_mapping.items():
            if hasattr(financial, concept_field):
                fact_rows = getattr(financial, concept_field)
                if fact_rows:
                    value = self._select_best_balance_sheet_value(fact_rows, concept_field)
                    results[result_key] = value if not math.isnan(value) else float('nan')
                else:
                    results[result_key] = float('nan')
            else:
                results[result_key] = float('nan')
        
        return results
    
    def _select_best_balance_sheet_value(self, fact_rows: List[Any], concept: str) -> float:
        """Select best balance sheet value from multiple fact rows"""
        if not fact_rows:
            return float('nan')
        
        # Filter to facts with valid numeric values and no dimensions (consolidated)
        consolidated_facts = []
        
        for fact in fact_rows:
            if hasattr(fact, 'numeric_value') and fact.numeric_value is not None:
                # Prefer facts without dimensions (consolidated)
                dimensions = getattr(fact, 'dimensions', None)
                if not dimensions or dimensions == {}:
                    consolidated_facts.append(fact)
        
        if consolidated_facts:
            # Take the first consolidated fact (most relevant)
            return float(consolidated_facts[0].numeric_value)
        
        # Fallback: take first fact with numeric value
        for fact in fact_rows:
            if hasattr(fact, 'numeric_value') and fact.numeric_value is not None:
                return float(fact.numeric_value)
        
        return float('nan')
    
    def _calculate_financial_ratios(self, data_points: List[BalanceSheetDataPoint]) -> List[BalanceSheetDataPoint]:
        """Calculate financial ratios for each data point"""
        processed = []
        
        for dp in data_points:
            # Calculate current ratio (Current Assets / Current Liabilities)
            current_ratio = float('nan')
            if not math.isnan(dp.current_assets) and not math.isnan(dp.current_liabilities) and dp.current_liabilities != 0:
                current_ratio = dp.current_assets / dp.current_liabilities
            
            # Calculate quick ratio (Cash / Current Liabilities) - conservative approach
            quick_ratio = float('nan')
            if not math.isnan(dp.cash_and_equivalents) and not math.isnan(dp.current_liabilities) and dp.current_liabilities != 0:
                quick_ratio = dp.cash_and_equivalents / dp.current_liabilities
            
            # Calculate debt-to-equity ratio
            debt_to_equity = float('nan')
            if not math.isnan(dp.long_term_debt) and not math.isnan(dp.stockholders_equity) and dp.stockholders_equity != 0:
                debt_to_equity = dp.long_term_debt / dp.stockholders_equity
            
            # Calculate debt-to-assets ratio
            debt_to_assets = float('nan')
            if not math.isnan(dp.long_term_debt) and not math.isnan(dp.total_assets) and dp.total_assets != 0:
                debt_to_assets = dp.long_term_debt / dp.total_assets
            
            # Calculate equity ratio (Equity / Total Assets)
            equity_ratio = float('nan')
            if not math.isnan(dp.stockholders_equity) and not math.isnan(dp.total_assets) and dp.total_assets != 0:
                equity_ratio = dp.stockholders_equity / dp.total_assets
            
            # Calculate cash ratio (Cash / Total Assets)
            cash_ratio = float('nan')
            if not math.isnan(dp.cash_and_equivalents) and not math.isnan(dp.total_assets) and dp.total_assets != 0:
                cash_ratio = dp.cash_and_equivalents / dp.total_assets
            
            # Create updated data point with ratios
            processed_dp = dp._replace(
                current_ratio=current_ratio,
                quick_ratio=quick_ratio,
                debt_to_equity=debt_to_equity,
                debt_to_assets=debt_to_assets,
                equity_ratio=equity_ratio,
                cash_ratio=cash_ratio,
                calculation_method="calculated_ratios"
            )
            
            processed.append(processed_dp)
        
        return processed
    
    def _calculate_summary_metrics(self, data_points: List[BalanceSheetDataPoint]) -> BalanceSheetMetrics:
        """Calculate summary metrics for balance sheet analysis"""
        
        # Filter to valid data
        valid_data = [dp for dp in data_points if not math.isnan(dp.total_assets)]
        
        if not valid_data:
            return BalanceSheetMetrics(
                latest_total_assets=0.0,
                latest_equity=0.0,
                latest_debt=0.0,
                latest_current_ratio=0.0,
                latest_debt_to_equity=0.0,
                avg_current_ratio=0.0,
                avg_debt_to_equity=0.0,
                total_quarters=0,
                data_quality="No Data",
                financial_strength="Unknown"
            )
        
        # Latest values
        latest = valid_data[-1]
        latest_total_assets = latest.total_assets
        latest_equity = latest.stockholders_equity if not math.isnan(latest.stockholders_equity) else 0.0
        latest_debt = latest.long_term_debt if not math.isnan(latest.long_term_debt) else 0.0
        latest_current_ratio = latest.current_ratio if not math.isnan(latest.current_ratio) else 0.0
        latest_debt_to_equity = latest.debt_to_equity if not math.isnan(latest.debt_to_equity) else 0.0
        
        # Average ratios
        valid_current_ratios = [dp.current_ratio for dp in valid_data if not math.isnan(dp.current_ratio)]
        valid_debt_to_equity = [dp.debt_to_equity for dp in valid_data if not math.isnan(dp.debt_to_equity)]
        
        avg_current_ratio = sum(valid_current_ratios) / len(valid_current_ratios) if valid_current_ratios else 0.0
        avg_debt_to_equity = sum(valid_debt_to_equity) / len(valid_debt_to_equity) if valid_debt_to_equity else 0.0
        
        # Data quality assessment
        total_quarters = len(valid_data)
        if total_quarters >= 8:
            data_quality = "Excellent"
        elif total_quarters >= 4:
            data_quality = "Good"
        else:
            data_quality = "Limited"
        
        # Financial strength assessment
        financial_strength = self._assess_financial_strength(latest_current_ratio, latest_debt_to_equity, latest.equity_ratio)
        
        return BalanceSheetMetrics(
            latest_total_assets=latest_total_assets,
            latest_equity=latest_equity,
            latest_debt=latest_debt,
            latest_current_ratio=latest_current_ratio,
            latest_debt_to_equity=latest_debt_to_equity,
            avg_current_ratio=avg_current_ratio,
            avg_debt_to_equity=avg_debt_to_equity,
            total_quarters=total_quarters,
            data_quality=data_quality,
            financial_strength=financial_strength
        )
    
    def _assess_financial_strength(self, current_ratio: float, debt_to_equity: float, equity_ratio: float) -> str:
        """Assess overall financial strength based on key ratios"""
        scores = []
        
        # Current ratio assessment (higher is better, >1.5 is good)
        if not math.isnan(current_ratio):
            if current_ratio >= 2.0:
                scores.append(3)  # Strong
            elif current_ratio >= 1.5:
                scores.append(2)  # Moderate
            else:
                scores.append(1)  # Weak
        
        # Debt-to-equity assessment (lower is better, <0.5 is good)
        if not math.isnan(debt_to_equity):
            if debt_to_equity <= 0.3:
                scores.append(3)  # Strong
            elif debt_to_equity <= 0.6:
                scores.append(2)  # Moderate
            else:
                scores.append(1)  # Weak
        
        # Equity ratio assessment (higher is better, >0.5 is good)
        if not math.isnan(equity_ratio):
            if equity_ratio >= 0.6:
                scores.append(3)  # Strong
            elif equity_ratio >= 0.4:
                scores.append(2)  # Moderate
            else:
                scores.append(1)  # Weak
        
        if not scores:
            return "Unknown"
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 2.5:
            return "Strong"
        elif avg_score >= 1.5:
            return "Moderate"
        else:
            return "Weak"


# Convenience function for external use
def process_balance_sheet_data(financial_data: List[Any], max_quarters: int = 12) -> Tuple[List[BalanceSheetDataPoint], BalanceSheetMetrics]:
    """
    Process financial data into balance sheet analysis
    
    Args:
        financial_data: List of financial data objects
        max_quarters: Maximum quarters to process
        
    Returns:
        Tuple of (data points, summary metrics)
    """
    processor = BalanceSheetDataProcessor()
    return processor.process_balance_sheet_data(financial_data, max_quarters)


if __name__ == "__main__":
    print("🧪 Testing Balance Sheet Data Processor")
    print("=" * 45)
    
    processor = BalanceSheetDataProcessor()
    
    print(f"📊 Asset concepts: {len(processor.asset_concepts)}")
    for key, concept in processor.asset_concepts.items():
        print(f"   • {key}: {concept}")
    
    print(f"📊 Liability concepts: {len(processor.liability_concepts)}")
    for key, concept in processor.liability_concepts.items():
        print(f"   • {key}: {concept}")
    
    print(f"📊 Equity concepts: {len(processor.equity_concepts)}")
    for key, concept in processor.equity_concepts.items():
        print(f"   • {key}: {concept}")
    
    print("\n✅ Balance Sheet Data Processor ready!")
    print("🔧 Features:")
    print("   • Asset, liability, and equity extraction from multi-row XBRL")
    print("   • Financial ratio calculations (Current, D/E, Equity ratios)")
    print("   • Liquidity analysis (Current ratio, Quick ratio)")
    print("   • Financial strength assessment")
    print("   • Data quality evaluation")
    print("   • Consolidated fact preference")