import requests
import json
import pandas as pd
import os

# --- Configuration ---
API_KEY = "tlbdvnfH2xmkfhl9qMLkOHP760puN6lW"
# You can change the symbol to any stock ticker you're interested in, e.g., 'TSLA'
SYMBOL = 'AAPL' 
OUTPUT_DIR = 'fmp_financial_data'
# The free FMP plan typically provides the last 5 years of data.
# Set the limit for how many past quarters you want.
LIMIT = 20 # 4 quarters/year * 5 years = 20 quarters

# --- Functions ---

def get_fmp_data(statement_type, symbol, api_key, limit):
    """
    Fetches financial statement data from the Financial Modeling Prep API.
    
    Args:
        statement_type (str): Type of statement (e.g., 'income-statement').
        symbol (str): The stock ticker symbol.
        api_key (str): Your FMP API key.
        limit (int): The number of periods to retrieve.

    Returns:
        list: A list of dictionaries containing the financial data, or None on error.
    """
    url = (
        f"https://financialmodelingprep.com/api/v3/{statement_type}/{symbol}"
        f"?period=quarter&limit={limit}&apikey={api_key}"
    )
    try:
        print(f"Fetching {statement_type} for {symbol}...")
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception for bad status codes (4xx or 5xx)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            print(f"Successfully fetched {len(data)} quarters of data.")
            return data
        else:
            print(f"Warning: No data received for {statement_type}. Response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during API request for {statement_type}: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON response for {statement_type}. Response text: {response.text}")
    return None

def save_as_json(data, directory):
    """Saves the complete raw data to a JSON file."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filepath = os.path.join(directory, f'{SYMBOL}_quarterly_financials_raw.json')
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"\nRaw data for all statements successfully saved to {filepath}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

def save_as_csv(data, directory):
    """Saves each financial statement into a separate CSV file."""
    if not os.path.exists(directory):
        os.makedirs(directory)

    print("\nProcessing and saving data to CSV files...")
    try:
        for statement_name, statement_data in data.items():
            if statement_data:
                df = pd.DataFrame(statement_data)
                filepath = os.path.join(directory, f'{SYMBOL}_{statement_name}.csv')
                df.to_csv(filepath, index=False)
                print(f"Successfully saved {statement_name} to {filepath}")
            else:
                print(f"No data to save for {statement_name}.")
    except Exception as e:
        print(f"Error saving CSV files: {e}")

# --- Main Execution ---

if __name__ == "__main__":
    # 1. Fetch data for each financial statement
    income_statement = get_fmp_data('income-statement', SYMBOL, API_KEY, LIMIT)
    balance_sheet = get_fmp_data('balance-sheet-statement', SYMBOL, API_KEY, LIMIT)
    cash_flow_statement = get_fmp_data('cash-flow-statement', SYMBOL, API_KEY, LIMIT)

    # 2. Combine all fetched data into a single dictionary
    all_financial_data = {
        "income_statement": income_statement,
        "balance_sheet_statement": balance_sheet,
        "cash_flow_statement": cash_flow_statement
    }

    # 3. Save the combined raw data as a single JSON file
    if any(all_financial_data.values()): # Only save if at least one statement has data
        save_as_json(all_financial_data, OUTPUT_DIR)
        
        # 4. Process and save the data into multiple CSV files
        save_as_csv(all_financial_data, OUTPUT_DIR)
    else:
        print("\nNo data was fetched. Exiting without saving files.")