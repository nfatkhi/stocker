import finnhub
import json

# Replace with your actual Finnhub API key
api_key = "d16hmcpr01qvtdbil250d16hmcpr01qvtdbil25g"

# Set up the Finnhub client
try:
    finnhub_client = finnhub.Client(api_key=api_key)
except Exception as e:
    print(f"Error initializing Finnhub client: {e}")
    exit()

# Define the stock symbol
symbol = 'TSLA'

try:
    # Fetch quarterly financials as reported
    financials = finnhub_client.financials_reported(symbol=symbol, freq='quarterly')

    # Pretty-print the raw JSON data
    print(json.dumps(financials, indent=4))

except finnhub.FinnhubAPIException as e:
    print(f"Finnhub API Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")