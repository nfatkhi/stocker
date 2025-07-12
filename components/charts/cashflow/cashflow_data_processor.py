# components/charts/cashflow/cashflow_data_processor.py - FCF data processing with intelligent value selection

import math
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
from dataclasses import dataclass


class CashflowDataPoint(NamedTuple):
    """Financial quarter data with YoY metrics"""
    quarter_label: str
    date: str
    fcf_dollars: float
    operating_cf: float = float('nan')
    capex: float = float('nan')
    yoy_change_pct: float = float('nan')
    yoy_label: str = "N/A"
    yoy_description: str = "No previous year quarter"
    data_source: str = "Cache"
    calculation_method: str = "direct"


@dataclass
class CashflowMetrics:
    """Summary metrics for cash flow analysis"""
    latest_fcf: float
    average_fcf: float
    total_quarters: int
    recent_growth: str
    data_quality: str
    conversion_success: bool


class CashflowDataProcessor:
    """Process multi-row XBRL cache data into cash flow metrics"""
    
    def __init__(self):
        # Cash flow concept mappings
        self.operating_cf_concepts = [
            'net_cash_operating_activities',
            'us-gaap:NetCashProvidedByUsedInOperatingActivities'
        ]
        
        self.capex_concepts = [
            'payments_to_acquire_ppe',
            'us-gaap:PaymentsToAcquirePropertyPlantAndEquipment'
        ]
        
        self.investing_cf_concepts = [
            'net_cash_investing_activities',
            'us-gaap:NetCashProvidedByUsedInInvestingActivities'
        ]
    
    def process_cashflow_data(self, financial_data: List[Any], max_quarters: int = 12) -> Tuple[List[CashflowDataPoint], CashflowMetrics]:
        """
        Process financial data into cash flow data points
        
        Args:
            financial_data: List of MultiRowFinancialData objects from cache
            max_quarters: Maximum quarters to process
            
        Returns:
            Tuple of (processed data points, summary metrics)
        """
        print(f"🔄 Processing {len(financial_data)} quarters for cash flow analysis")
        
        # Step 1: Convert cumulative to actual quarters if needed
        converted_data = self._attempt_quarterly_conversion(financial_data[:max_quarters])
        
        # Step 2: Extract cash flow data points
        data_points = self._extract_cashflow_points(converted_data)
        
        # Step 3: Calculate YoY changes
        data_points_with_yoy = self._calculate_yoy_changes(data_points)
        
        # Step 4: Generate summary metrics
        metrics = self._calculate_summary_metrics(data_points_with_yoy)
        
        print(f"✅ Processed {len(data_points_with_yoy)} quarters with FCF data")
        return data_points_with_yoy, metrics
    
    def _attempt_quarterly_conversion(self, raw_data: List[Any]) -> List[Any]:
        """Attempt to convert cumulative to actual quarterly amounts"""
        try:
            # Try multiple import paths for quarterly converter
            try:
                from .quarterly_converter import convert_financial_data_to_actual_quarters
                print(f"✅ Imported quarterly converter from local path")
            except ImportError:
                try:
                    from components.charts.quarterly_converter import convert_financial_data_to_actual_quarters
                    print(f"✅ Imported quarterly converter from components path")
                except ImportError:
                    raise ImportError("Quarterly converter not available")
            
            print(f"🔄 Converting {len(raw_data)} quarters to actual amounts...")
            converted_data = convert_financial_data_to_actual_quarters(raw_data)
            print(f"✅ Conversion successful: {len(converted_data)} quarters")
            return converted_data
            
        except Exception as e:
            print(f"⚠️ Quarterly conversion failed: {e}")
            print(f"⚠️ Using raw data (may contain cumulative amounts)")
            return raw_data
    
    def _extract_cashflow_points(self, financial_data: List[Any]) -> List[CashflowDataPoint]:
        """Extract cash flow data points from financial data"""
        data_points = []
        
        for financial in reversed(financial_data):  # Reverse to get chronological order
            # Extract quarter and date information
            quarter_label = self._extract_quarter_label(financial)
            date = getattr(financial, 'filing_date', '')
            
            # Extract operating cash flow
            operating_cf = self._extract_operating_cashflow(financial)
            
            # Extract capital expenditures
            capex = self._extract_capex(financial)
            
            # Calculate FCF
            fcf, calculation_method = self._calculate_fcf(operating_cf, capex, financial)
            
            # Determine data source
            is_actual = getattr(financial, 'is_actual_quarterly', False)
            data_source = "Cache (Actual Q)" if is_actual else "Cache (Raw)"
            
            data_point = CashflowDataPoint(
                quarter_label=quarter_label,
                date=date,
                fcf_dollars=fcf,
                operating_cf=operating_cf,
                capex=capex,
                data_source=data_source,
                calculation_method=calculation_method
            )
            
            data_points.append(data_point)
            
            # Debug output
            if not math.isnan(fcf):
                print(f"   💰 {quarter_label}: FCF ${fcf/1e6:.1f}M (Op: ${operating_cf/1e6:.1f}M, CapEx: ${capex/1e6:.1f}M)")
        
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
                
                # Determine quarter from month
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
    
    def _extract_operating_cashflow(self, financial: Any) -> float:
        """Extract operating cash flow from multi-row financial data"""
        
        # Try direct attribute first (converted data)
        if hasattr(financial, 'cash') and financial.cash != 0:
            return float(financial.cash)
        
        # Try multi-row XBRL data
        for concept in self.operating_cf_concepts:
            if hasattr(financial, concept):
                fact_rows = getattr(financial, concept)
                if fact_rows:
                    value = self._select_best_cashflow_value(fact_rows, concept)
                    if not math.isnan(value):
                        return value
        
        return float('nan')
    
    def _extract_capex(self, financial: Any) -> float:
        """Extract capital expenditures from multi-row financial data"""
        
        # First try direct CapEx concepts
        for concept in self.capex_concepts:
            if hasattr(financial, concept):
                fact_rows = getattr(financial, concept)
                if fact_rows:
                    value = self._select_best_cashflow_value(fact_rows, concept)
                    if not math.isnan(value):
                        # CapEx is usually negative in cash flow, make it positive for FCF calc
                        return abs(value)
        
        # Fallback: Try to extract CapEx from investing activities
        # Many companies report CapEx as part of investing activities
        for concept in self.investing_cf_concepts:
            if hasattr(financial, concept):
                fact_rows = getattr(financial, concept)
                if fact_rows:
                    investing_cf = self._select_best_cashflow_value(fact_rows, concept)
                    if not math.isnan(investing_cf) and investing_cf < 0:
                        # Investing CF is negative, includes CapEx and other investments
                        # This is an approximation - actual CapEx could be different
                        return abs(investing_cf)
        
        return float('nan')
    
    def _select_best_cashflow_value(self, fact_rows: List[Any], concept: str) -> float:
        """Select best cash flow value from multiple fact rows"""
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
            # Take the first consolidated fact (should be most relevant)
            return float(consolidated_facts[0].numeric_value)
        
        # Fallback: take first fact with numeric value
        for fact in fact_rows:
            if hasattr(fact, 'numeric_value') and fact.numeric_value is not None:
                return float(fact.numeric_value)
        
        return float('nan')
    
    def _calculate_fcf(self, operating_cf: float, capex: float, financial: Any) -> Tuple[float, str]:
        """Calculate free cash flow with method tracking"""
        
        # Method 1: Operating CF - CapEx
        if not math.isnan(operating_cf) and not math.isnan(capex):
            fcf = operating_cf - capex
            return fcf, "operating_cf_minus_capex"
        
        # Method 2: Direct FCF from legacy data structure
        if hasattr(financial, 'cash') and financial.cash != 0:
            return float(financial.cash), "direct_fcf"
        
        # Method 3: Operating CF only (when CapEx not available)
        if not math.isnan(operating_cf):
            return operating_cf, "operating_cf_only"
        
        return float('nan'), "no_data"
    
    def _calculate_yoy_changes(self, data_points: List[CashflowDataPoint]) -> List[CashflowDataPoint]:
        """Calculate year-over-year changes for cash flow data"""
        processed = []
        
        for i, dp in enumerate(data_points):
            # Look for same quarter previous year (4 quarters back)
            yoy_index = i - 4
            
            if yoy_index >= 0 and yoy_index < len(data_points):
                prev_year_dp = data_points[yoy_index]
                curr_val = dp.fcf_dollars
                prev_val = prev_year_dp.fcf_dollars
                
                if math.isnan(curr_val) or math.isnan(prev_val):
                    yoy_pct, yoy_label, yoy_desc = float('nan'), "N/A", "Insufficient data"
                elif prev_val == 0:
                    yoy_pct, yoy_label = float('inf'), "New+"
                    yoy_desc = f"${curr_val/1e6:.1f}M from $0 (vs {prev_year_dp.quarter_label})"
                else:
                    yoy_pct = ((curr_val - prev_val) / abs(prev_val)) * 100
                    yoy_label = f"{yoy_pct:+.1f}%" if abs(yoy_pct) <= 999 else f"{yoy_pct/100:+.0f}x"
                    prev_fmt = f"${prev_val/1e6:.1f}M"
                    curr_fmt = f"${curr_val/1e6:.1f}M"
                    yoy_desc = f"{prev_fmt} → {curr_fmt} (vs {prev_year_dp.quarter_label})"
                
                processed_dp = dp._replace(
                    yoy_change_pct=yoy_pct,
                    yoy_label=yoy_label,
                    yoy_description=yoy_desc
                )
            else:
                processed_dp = dp
            
            processed.append(processed_dp)
        
        return processed
    
    def _calculate_summary_metrics(self, data_points: List[CashflowDataPoint]) -> CashflowMetrics:
        """Calculate summary metrics for cash flow analysis"""
        
        # Filter to valid FCF data
        valid_data = [dp for dp in data_points if not math.isnan(dp.fcf_dollars)]
        
        if not valid_data:
            return CashflowMetrics(
                latest_fcf=0.0,
                average_fcf=0.0,
                total_quarters=0,
                recent_growth="N/A",
                data_quality="No Data",
                conversion_success=False
            )
        
        # Basic metrics
        latest_fcf = valid_data[-1].fcf_dollars
        average_fcf = sum(dp.fcf_dollars for dp in valid_data) / len(valid_data)
        total_quarters = len(valid_data)
        
        # Calculate recent growth
        recent_growth = "N/A"
        recent_yoy_data = [dp for dp in valid_data[-4:] if not math.isnan(dp.yoy_change_pct) and not math.isinf(dp.yoy_change_pct)]
        
        if recent_yoy_data:
            avg_yoy = sum(dp.yoy_change_pct for dp in recent_yoy_data) / len(recent_yoy_data)
            recent_growth = f"{avg_yoy:+.1f}%"
        
        # Assess data quality
        conversion_success = any("Actual Q" in dp.data_source for dp in valid_data)
        
        if total_quarters >= 8:
            data_quality = "Excellent"
        elif total_quarters >= 4:
            data_quality = "Good"
        else:
            data_quality = "Limited"
        
        return CashflowMetrics(
            latest_fcf=latest_fcf,
            average_fcf=average_fcf,
            total_quarters=total_quarters,
            recent_growth=recent_growth,
            data_quality=data_quality,
            conversion_success=conversion_success
        )


# Convenience function for external use
def process_cashflow_data(financial_data: List[Any], max_quarters: int = 12) -> Tuple[List[CashflowDataPoint], CashflowMetrics]:
    """
    Process financial data into cash flow analysis
    
    Args:
        financial_data: List of financial data objects
        max_quarters: Maximum quarters to process
        
    Returns:
        Tuple of (data points, summary metrics)
    """
    processor = CashflowDataProcessor()
    return processor.process_cashflow_data(financial_data, max_quarters)


if __name__ == "__main__":
    print("🧪 Testing Cash Flow Data Processor")
    print("=" * 40)
    
    processor = CashflowDataProcessor()
    
    print(f"📊 Operating CF concepts: {len(processor.operating_cf_concepts)}")
    for concept in processor.operating_cf_concepts:
        print(f"   • {concept}")
    
    print(f"📊 CapEx concepts: {len(processor.capex_concepts)}")
    for concept in processor.capex_concepts:
        print(f"   • {concept}")
    
    print(f"📊 Investing CF concepts: {len(processor.investing_cf_concepts)}")
    for concept in processor.investing_cf_concepts:
        print(f"   • {concept}")
    
    print("\n✅ Cash Flow Data Processor ready!")
    print("🔧 Features:")
    print("   • Operating CF extraction from multi-row XBRL")
    print("   • CapEx extraction with investing CF fallback")
    print("   • FCF calculation: Operating CF - CapEx")
    print("   • YoY analysis with 4-quarter lookback")
    print("   • Data quality assessment")
    print("   • Quarterly conversion integration")