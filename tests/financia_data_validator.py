# financial_data_validator.py - Comprehensive validation and testing suite for financial data accuracy

"""
Financial Data Validation & Testing Suite
Comprehensive validation and testing for financial data accuracy
"""

import unittest
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd


class FinancialDataValidator:
    """Comprehensive financial data validation and testing suite"""
    
    def __init__(self):
        self.validation_results = {}
        self.warnings = []
        self.errors = []
    
    def validate_quarterly_data(self, financials: List, ticker: str) -> Dict[str, any]:
        """
        Comprehensive validation of quarterly financial data
        Returns validation report with scores and recommendations
        """
        print(f"\n🔍 VALIDATING FINANCIAL DATA FOR {ticker}")
        print("="*60)
        
        report = {
            'ticker': ticker,
            'total_quarters': len(financials),
            'validation_score': 0,
            'data_quality': 'Unknown',
            'tests_passed': 0,
            'tests_failed': 0,
            'warnings': [],
            'errors': [],
            'recommendations': []
        }
        
        if not financials:
            report['errors'].append("No financial data available")
            report['data_quality'] = 'CRITICAL'
            return report
        
        # Test Suite
        tests = [
            self._test_data_completeness,
            self._test_revenue_consistency,
            self._test_margin_reasonableness,
            self._test_balance_sheet_logic,
            self._test_growth_patterns,
            self._test_date_consistency,
            self._test_numerical_validity,
            self._test_cross_validation
        ]
        
        total_score = 0
        max_score = len(tests) * 10  # Each test worth 10 points
        
        for test in tests:
            try:
                score, issues = test(financials, ticker)
                total_score += score
                
                if score == 10:
                    report['tests_passed'] += 1
                    print(f"✅ {test.__name__.replace('_test_', '').replace('_', ' ').title()}: PASS ({score}/10)")
                elif score >= 7:
                    report['tests_passed'] += 1
                    print(f"⚠️  {test.__name__.replace('_test_', '').replace('_', ' ').title()}: PASS with warnings ({score}/10)")
                    report['warnings'].extend(issues)
                else:
                    report['tests_failed'] += 1
                    print(f"❌ {test.__name__.replace('_test_', '').replace('_', ' ').title()}: FAIL ({score}/10)")
                    report['errors'].extend(issues)
                    
            except Exception as e:
                report['tests_failed'] += 1
                error_msg = f"Test {test.__name__} failed with error: {str(e)}"
                report['errors'].append(error_msg)
                print(f"❌ {test.__name__}: ERROR - {str(e)}")
        
        # Calculate final scores
        report['validation_score'] = (total_score / max_score) * 100
        
        if report['validation_score'] >= 90:
            report['data_quality'] = 'EXCELLENT'
        elif report['validation_score'] >= 80:
            report['data_quality'] = 'GOOD'
        elif report['validation_score'] >= 70:
            report['data_quality'] = 'ACCEPTABLE'
        elif report['validation_score'] >= 60:
            report['data_quality'] = 'POOR'
        else:
            report['data_quality'] = 'CRITICAL'
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report, financials)
        
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"Overall Score: {report['validation_score']:.1f}/100")
        print(f"Data Quality: {report['data_quality']}")
        print(f"Tests Passed: {report['tests_passed']}")
        print(f"Tests Failed: {report['tests_failed']}")
        print(f"Warnings: {len(report['warnings'])}")
        print(f"Errors: {len(report['errors'])}")
        
        return report
    
    def _test_data_completeness(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Test data completeness and coverage"""
        issues = []
        score = 10
        
        # Check minimum quarters
        if len(financials) < 4:
            issues.append(f"Insufficient data: only {len(financials)} quarters (need ≥4)")
            score -= 4
        
        # Check for missing key fields
        required_fields = ['revenue', 'net_income', 'assets', 'cash', 'debt']
        missing_counts = {field: 0 for field in required_fields}
        
        for f in financials:
            for field in required_fields:
                value = getattr(f, field, None)
                if value is None or value == 0:
                    missing_counts[field] += 1
        
        for field, count in missing_counts.items():
            if count > len(financials) * 0.5:  # >50% missing
                issues.append(f"High missing data for {field}: {count}/{len(financials)} quarters")
                score -= 1
        
        return max(0, score), issues
    
    def _test_revenue_consistency(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Test revenue data for consistency and reasonableness"""
        issues = []
        score = 10
        
        revenues = [f.revenue for f in financials if f.revenue and f.revenue > 0]
        
        if len(revenues) < 2:
            return 0, ["Insufficient revenue data for consistency testing"]
        
        # Test for extreme outliers
        median_revenue = np.median(revenues)
        for i, revenue in enumerate(revenues):
            if revenue > median_revenue * 5 or revenue < median_revenue * 0.2:
                issues.append(f"Revenue outlier in quarter {i}: ${revenue/1e9:.1f}B vs median ${median_revenue/1e9:.1f}B")
                score -= 1
        
        # Test for unrealistic quarter-to-quarter changes
        for i in range(1, len(revenues)):
            qoq_change = (revenues[i] / revenues[i-1] - 1) * 100
            if abs(qoq_change) > 50:  # >50% QoQ change is suspicious
                issues.append(f"Extreme QoQ revenue change: {qoq_change:+.1f}% in quarter {i}")
                score -= 1
        
        return max(0, score), issues
    
    def _test_margin_reasonableness(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Test profit margins for reasonableness"""
        issues = []
        score = 10
        
        for i, f in enumerate(financials):
            if not f.revenue or f.revenue <= 0:
                continue
            
            # Test gross margin
            if hasattr(f, 'gross_profit') and f.gross_profit is not None:
                gross_margin = (f.gross_profit / f.revenue) * 100
                if gross_margin > 95:
                    issues.append(f"Unrealistic gross margin in Q{i}: {gross_margin:.1f}%")
                    score -= 1
                elif gross_margin < -50:
                    issues.append(f"Extreme negative gross margin in Q{i}: {gross_margin:.1f}%")
                    score -= 1
            
            # Test net margin
            if f.net_income is not None:
                net_margin = (f.net_income / f.revenue) * 100
                if net_margin > 60:
                    issues.append(f"Unrealistic net margin in Q{i}: {net_margin:.1f}%")
                    score -= 1
                elif net_margin < -100:
                    issues.append(f"Extreme negative net margin in Q{i}: {net_margin:.1f}%")
                    score -= 1
        
        return max(0, score), issues
    
    def _test_balance_sheet_logic(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Test balance sheet relationships for logical consistency"""
        issues = []
        score = 10
        
        for i, f in enumerate(financials):
            # Test: Cash should be <= Assets
            if f.assets and f.cash and f.cash > f.assets:
                issues.append(f"Cash > Assets in Q{i}: ${f.cash/1e9:.1f}B > ${f.assets/1e9:.1f}B")
                score -= 2
            
            # Test: Debt should be <= Assets (typically)
            if f.assets and f.debt and f.debt > f.assets * 1.5:
                issues.append(f"Excessive debt/assets ratio in Q{i}: {(f.debt/f.assets)*100:.1f}%")
                score -= 1
            
            # Test: Liabilities should be <= Assets (accounting identity)
            if f.assets and f.liabilities and f.liabilities > f.assets * 1.2:
                issues.append(f"Liabilities > Assets in Q{i}: ${f.liabilities/1e9:.1f}B > ${f.assets/1e9:.1f}B")
                score -= 2
        
        return max(0, score), issues
    
    def _test_growth_patterns(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Test growth patterns for reasonableness"""
        issues = []
        score = 10
        
        if len(financials) < 8:  # Need at least 2 years for meaningful growth analysis
            return 8, ["Insufficient data for comprehensive growth analysis"]
        
        revenues = [f.revenue for f in financials if f.revenue and f.revenue > 0]
        
        if len(revenues) >= 4:
            # Calculate YoY growth rates
            yoy_growth_rates = []
            for i in range(4, len(revenues)):
                yoy_growth = (revenues[i] / revenues[i-4] - 1) * 100
                yoy_growth_rates.append(yoy_growth)
            
            # Check for unrealistic growth
            for i, growth in enumerate(yoy_growth_rates):
                if growth > 300:  # >300% YoY growth is suspicious
                    issues.append(f"Extreme YoY growth: {growth:.1f}% in year {i+2}")
                    score -= 1
                elif growth < -80:  # >80% decline is concerning
                    issues.append(f"Extreme YoY decline: {growth:.1f}% in year {i+2}")
                    score -= 1
        
        return max(0, score), issues
    
    def _test_date_consistency(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Test date consistency and proper quarterly progression"""
        issues = []
        score = 10
        
        dates = []
        for f in financials:
            try:
                date_obj = datetime.strptime(f.date.split(' ')[0], '%Y-%m-%d')
                dates.append(date_obj)
            except ValueError:
                issues.append(f"Invalid date format: {f.date}")
                score -= 1
        
        if len(dates) > 1:
            # Check for proper chronological order
            for i in range(1, len(dates)):
                if dates[i] < dates[i-1]:
                    issues.append(f"Dates not in chronological order: {dates[i]} < {dates[i-1]}")
                    score -= 1
            
            # Check for reasonable quarterly spacing
            for i in range(1, len(dates)):
                days_diff = (dates[i] - dates[i-1]).days
                if days_diff < 60 or days_diff > 120:  # Should be ~90 days between quarters
                    issues.append(f"Unusual gap between quarters: {days_diff} days")
                    score -= 0.5
        
        return max(0, score), issues
    
    def _test_numerical_validity(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Test for numerical validity (NaN, infinity, etc.)"""
        issues = []
        score = 10
        
        numeric_fields = ['revenue', 'net_income', 'assets', 'cash', 'debt', 'liabilities']
        
        for i, f in enumerate(financials):
            for field in numeric_fields:
                value = getattr(f, field, None)
                if value is not None:
                    if np.isnan(value) or np.isinf(value):
                        issues.append(f"Invalid numeric value for {field} in Q{i}: {value}")
                        score -= 1
                    elif abs(value) > 1e15:  # > $1 quadrillion is unrealistic
                        issues.append(f"Unrealistic value for {field} in Q{i}: ${value/1e12:.1f}T")
                        score -= 1
        
        return max(0, score), issues
    
    def _test_cross_validation(self, financials: List, ticker: str) -> Tuple[int, List[str]]:
        """Cross-validate financial relationships"""
        issues = []
        score = 10
        
        for i, f in enumerate(financials):
            # Revenue should generally be larger than net income
            if f.revenue and f.net_income and f.net_income > f.revenue * 1.1:
                issues.append(f"Net income > Revenue in Q{i}: unusual but possible")
                score -= 0.5
            
            # Assets should be positive for established companies
            if f.assets and f.assets <= 0:
                issues.append(f"Non-positive assets in Q{i}: ${f.assets/1e9:.1f}B")
                score -= 2
            
            # Operating income should be between gross profit and net income (if available)
            if (hasattr(f, 'gross_profit') and hasattr(f, 'operating_income') and 
                f.gross_profit and f.operating_income and f.net_income):
                
                if f.operating_income > f.gross_profit * 1.1:
                    issues.append(f"Operating income > Gross profit in Q{i}")
                    score -= 1
                    
                if f.net_income > f.operating_income * 1.5:
                    issues.append(f"Net income significantly > Operating income in Q{i}")
                    score -= 0.5
        
        return max(0, score), issues
    
    def _generate_recommendations(self, report: Dict, financials: List) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        if report['validation_score'] < 70:
            recommendations.append("⚠️ Data quality is below acceptable threshold. Consider alternative data sources.")
        
        if report['tests_failed'] > 2:
            recommendations.append("🔧 Multiple data quality issues detected. Implement additional data cleaning.")
        
        if len(financials) < 8:
            recommendations.append("📈 Limited historical data. Consider fetching more quarters for better analysis.")
        
        if 'Revenue outlier' in str(report['errors']):
            recommendations.append("📊 Revenue outliers detected. Review data source and consider smoothing techniques.")
        
        if 'margin' in str(report['errors']).lower():
            recommendations.append("💰 Margin calculations show inconsistencies. Verify source data accuracy.")
        
        if 'date' in str(report['errors']).lower():
            recommendations.append("📅 Date formatting issues detected. Implement robust date parsing.")
        
        # Positive recommendations
        if report['validation_score'] >= 90:
            recommendations.append("✅ Excellent data quality! Safe to use for analysis and decision-making.")
        elif report['validation_score'] >= 80:
            recommendations.append("👍 Good data quality with minor issues. Proceed with analysis.")
        
        return recommendations
    
    def generate_validation_report(self, report: Dict, save_path: Optional[str] = None) -> str:
        """Generate a detailed validation report"""
        report_text = f"""
FINANCIAL DATA VALIDATION REPORT
{'='*50}

Company: {report['ticker']}
Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Quarters Analyzed: {report['total_quarters']}

OVERALL ASSESSMENT
{'='*20}
Validation Score: {report['validation_score']:.1f}/100
Data Quality: {report['data_quality']}
Tests Passed: {report['tests_passed']}
Tests Failed: {report['tests_failed']}

ISSUES IDENTIFIED
{'='*20}
Errors ({len(report['errors'])}):
"""
        
        for i, error in enumerate(report['errors'], 1):
            report_text += f"{i}. {error}\n"
        
        report_text += f"\nWarnings ({len(report['warnings'])}):\n"
        for i, warning in enumerate(report['warnings'], 1):
            report_text += f"{i}. {warning}\n"
        
        report_text += f"\nRECOMMENDATIONS\n{'='*20}\n"
        for i, rec in enumerate(report['recommendations'], 1):
            report_text += f"{i}. {rec}\n"
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report_text)
            print(f"📄 Report saved to: {save_path}")
        
        return report_text


class FinancialDataTester:
    """Unit tests for financial data accuracy"""
    
    def __init__(self):
        self.test_results = []
    
    def run_accuracy_tests(self, data_fetcher, test_tickers: List[str]) -> Dict:
        """Run comprehensive accuracy tests on multiple tickers"""
        print("\n🧪 RUNNING FINANCIAL DATA ACCURACY TESTS")
        print("="*60)
        
        results = {
            'tickers_tested': len(test_tickers),
            'successful_fetches': 0,
            'failed_fetches': 0,
            'average_quality_score': 0,
            'ticker_results': {}
        }
        
        validator = FinancialDataValidator()
        total_score = 0
        successful_tests = 0
        
        for ticker in test_tickers:
            print(f"\n🎯 Testing {ticker}...")
            
            try:
                # Mock event for testing
                class MockEvent:
                    def __init__(self, ticker):
                        self.data = {'ticker': ticker}
                
                # Test data fetching
                event = MockEvent(ticker)
                stock_data = self._test_data_fetch(data_fetcher, event)
                
                if stock_data and hasattr(stock_data, 'quarterly_financials'):
                    # Validate the data
                    validation_report = validator.validate_quarterly_data(
                        stock_data.quarterly_financials, ticker
                    )
                    
                    results['ticker_results'][ticker] = validation_report
                    results['successful_fetches'] += 1
                    total_score += validation_report['validation_score']
                    successful_tests += 1
                    
                    print(f"✅ {ticker}: {validation_report['data_quality']} ({validation_report['validation_score']:.1f}/100)")
                    
                else:
                    results['failed_fetches'] += 1
                    results['ticker_results'][ticker] = {'error': 'Failed to fetch data'}
                    print(f"❌ {ticker}: Data fetch failed")
                    
            except Exception as e:
                results['failed_fetches'] += 1
                results['ticker_results'][ticker] = {'error': str(e)}
                print(f"❌ {ticker}: Error - {str(e)}")
        
        if successful_tests > 0:
            results['average_quality_score'] = total_score / successful_tests
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"Tickers Tested: {results['tickers_tested']}")
        print(f"Successful: {results['successful_fetches']}")
        print(f"Failed: {results['failed_fetches']}")
        print(f"Average Quality Score: {results['average_quality_score']:.1f}/100")
        
        return results
    
    def _test_data_fetch(self, data_fetcher, event):
        """Test data fetching for a specific ticker"""
        # This would need to be integrated with your actual DataFetcher
        # For now, returning None to indicate testing framework
        return None
    
    def benchmark_against_known_values(self, ticker: str, expected_values: Dict) -> Dict:
        """Benchmark fetched data against known correct values"""
        print(f"\n📏 BENCHMARKING {ticker} AGAINST KNOWN VALUES")
        
        benchmark_results = {
            'ticker': ticker,
            'total_comparisons': len(expected_values),
            'matches': 0,
            'close_matches': 0,  # Within 5%
            'mismatches': 0,
            'accuracy_score': 0,
            'details': []
        }
        
        # This would compare fetched values against expected values
        # Implementation would depend on your specific data structure
        
        return benchmark_results


# Usage Example and Test Configuration
class FinancialDataTestSuite:
    """Complete test suite for financial data accuracy"""
    
    def __init__(self):
        self.validator = FinancialDataValidator()
        self.tester = FinancialDataTester()
    
    def run_complete_test_suite(self, data_fetcher) -> Dict:
        """Run the complete test suite"""
        print("\n🚀 STARTING COMPLETE FINANCIAL DATA TEST SUITE")
        print("="*70)
        
        # Test tickers - mix of large cap, mid cap, and challenging cases
        test_tickers = [
            'AAPL',   # Large cap tech
            'MSFT',   # Large cap tech
            'BRK-B',  # Berkshire Hathaway (complex structure)
            'TSLA',   # High growth, volatile
            'O',      # REIT (different financial structure)
            'KO',     # Stable consumer goods
            'GOOGL',  # Class A shares
            'JNJ',    # Healthcare/pharma
        ]
        
        # Run accuracy tests
        accuracy_results = self.tester.run_accuracy_tests(data_fetcher, test_tickers)
        
        # Generate summary report
        summary = self._generate_test_summary(accuracy_results)
        
        return {
            'accuracy_results': accuracy_results,
            'summary': summary,
            'recommendations': self._generate_test_recommendations(accuracy_results)
        }
    
    def _generate_test_summary(self, results: Dict) -> Dict:
        """Generate test summary"""
        return {
            'overall_success_rate': (results['successful_fetches'] / results['tickers_tested']) * 100,
            'data_quality_distribution': self._analyze_quality_distribution(results),
            'common_issues': self._identify_common_issues(results)
        }
    
    def _analyze_quality_distribution(self, results: Dict) -> Dict:
        """Analyze distribution of data quality scores"""
        scores = []
        quality_levels = {'EXCELLENT': 0, 'GOOD': 0, 'ACCEPTABLE': 0, 'POOR': 0, 'CRITICAL': 0}
        
        for ticker_result in results['ticker_results'].values():
            if 'validation_score' in ticker_result:
                scores.append(ticker_result['validation_score'])
                quality_levels[ticker_result['data_quality']] += 1
        
        return {
            'average_score': np.mean(scores) if scores else 0,
            'median_score': np.median(scores) if scores else 0,
            'quality_distribution': quality_levels
        }
    
    def _identify_common_issues(self, results: Dict) -> List[str]:
        """Identify common issues across tickers"""
        issue_counts = {}
        
        for ticker_result in results['ticker_results'].values():
            if 'errors' in ticker_result:
                for error in ticker_result['errors']:
                    # Categorize errors
                    if 'revenue' in error.lower():
                        issue_counts['Revenue Issues'] = issue_counts.get('Revenue Issues', 0) + 1
                    elif 'margin' in error.lower():
                        issue_counts['Margin Issues'] = issue_counts.get('Margin Issues', 0) + 1
                    elif 'date' in error.lower():
                        issue_counts['Date Issues'] = issue_counts.get('Date Issues', 0) + 1
                    elif 'balance' in error.lower():
                        issue_counts['Balance Sheet Issues'] = issue_counts.get('Balance Sheet Issues', 0) + 1
        
        # Return top issues
        return sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
    
    def _generate_test_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        success_rate = (results['successful_fetches'] / results['tickers_tested']) * 100
        
        if success_rate < 80:
            recommendations.append("🔧 Low success rate - investigate data fetching reliability")
        
        if results['average_quality_score'] < 75:
            recommendations.append("📊 Low average quality - enhance data validation")
        
        if results['failed_fetches'] > 2:
            recommendations.append("🛠️ Multiple fetch failures - review error handling")
        
        recommendations.append("✅ Regular testing recommended to maintain data quality")
        
        return recommendations


# Example usage:
if __name__ == "__main__":
    # Initialize test suite
    test_suite = FinancialDataTestSuite()
    
    # Example: Test specific ticker data
    validator = FinancialDataValidator()
    
    # Mock financial data for testing
    class MockFinancial:
        def __init__(self, date, revenue, net_income, assets, cash, debt):
            self.date = date
            self.revenue = revenue
            self.net_income = net_income
            self.assets = assets
            self.cash = cash
            self.debt = debt
            self.liabilities = debt * 1.2  # Mock liabilities
            self.gross_profit = revenue * 0.4  # Mock gross profit
    
    # Example test data
    mock_data = [
        MockFinancial("2024-03-31", 95e9, 20e9, 400e9, 50e9, 100e9),
        MockFinancial("2023-12-31", 92e9, 18e9, 395e9, 48e9, 102e9),
        MockFinancial("2023-09-30", 89e9, 19e9, 390e9, 45e9, 105e9),
        MockFinancial("2023-06-30", 87e9, 17e9, 385e9, 43e9, 107e9),
    ]
    
    # Run validation
    report = validator.validate_quarterly_data(mock_data, "TEST")
    
    # Generate detailed report
    detailed_report = validator.generate_validation_report(report)
    print(detailed_report)