import finnhub
import json
import pandas as pd
import os

# --- Configuration ---
API_KEY = "d16hmcpr01qvtdbil250d16hmcpr01qvtdbil25g"
SYMBOL = 'TSLA'
OUTPUT_DIR = 'financial_data'

# --- Functions ---

def get_quarterly_financials(api_key, symbol):
    """Fetches quarterly financial data from Finnhub."""
    try:
        finnhub_client = finnhub.Client(api_key=api_key)
        print(f"Fetching quarterly financials for {symbol}...")
        financials = finnhub_client.financials_reported(symbol=symbol, freq='quarterly')
        print("Data fetched successfully.")
        return financials
    except finnhub.FinnhubAPIException as e:
        print(f"Finnhub API Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during data fetching: {e}")
    return None

def save_as_json(data, symbol, directory):
    """Saves the complete raw data to a JSON file."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filepath = os.path.join(directory, f'{symbol}_quarterly_financials.json')
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Raw data successfully saved to {filepath}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

def save_as_csv(data, symbol, directory):
    """Processes and saves financial statements into separate CSV files."""
    if not data or 'data' not in data:
        print("No data available to process for CSV export.")
        return

    if not os.path.exists(directory):
        os.makedirs(directory)

    # A dictionary to hold DataFrames for each report type
    reports = {'income_statement': [], 'balance_sheet': [], 'cash_flow': []}

    for quarterly_report in data['data']:
        report_date = quarterly_report.get('endDate')
        report_year = quarterly_report.get('year')
        report_quarter = quarterly_report.get('quarter')
        
        # Process Income Statement (ic)
        if 'ic' in quarterly_report['report']:
            for item in quarterly_report['report']['ic']:
                reports['income_statement'].append({
                    'endDate': report_date,
                    'year': report_year,
                    'quarter': report_quarter,
                    'concept': item.get('concept'),
                    'label': item.get('label'),
                    'unit': item.get('unit'),
                    'value': item.get('value')
                })

        # Process Balance Sheet (bs)
        if 'bs' in quarterly_report['report']:
            for item in quarterly_report['report']['bs']:
                reports['balance_sheet'].append({
                    'endDate': report_date,
                    'year': report_year,
                    'quarter': report_quarter,
                    'concept': item.get('concept'),
                    'label': item.get('label'),
                    'unit': item.get('unit'),
                    'value': item.get('value')
                })

        # Process Cash Flow (cf)
        if 'cf' in quarterly_report['report']:
            for item in quarterly_report['report']['cf']:
                reports['cash_flow'].append({
                    'endDate': report_date,
                    'year': report_year,
                    'quarter': report_quarter,
                    'concept': item.get('concept'),
                    'label': item.get('label'),
                    'unit': item.get('unit'),
                    'value': item.get('value')
                })

    # Save each report to a separate CSV file
    try:
        for report_name, report_data in reports.items():
            if report_data:
                df = pd.DataFrame(report_data)
                filepath = os.path.join(directory, f'{symbol}_{report_name}.csv')
                df.to_csv(filepath, index=False)
                print(f"Successfully saved {report_name} to {filepath}")
    except Exception as e:
        print(f"Error saving CSV files: {e}")

# --- Main Execution ---

if __name__ == "__main__":
    # 1. Get the financial data
    financial_data = get_quarterly_financials(API_KEY, SYMBOL)
    
    if financial_data:
        # 2. Save the raw data as a single JSON file
        save_as_json(financial_data, SYMBOL, OUTPUT_DIR)
        
        print("-" * 30)
        
        # 3. Process and save the data into multiple CSV files
        save_as_csv(financial_data, SYMBOL, OUTPUT_DIR)