# main.py
import tkinter as tk
import sys
import os
from config import API_KEYS
print(f"API Keys configured: {list(API_KEYS.keys())}")
print(f"FMP key present: {bool(API_KEYS.get('financial_modeling_prep'))}")

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import StockerApp

def main():
    print("Starting Stocker...")
    
    # Create main window
    root = tk.Tk()
    root.title("Stocker")
    root.geometry("800x600")
    
    # Create and run app
    try:
        app = StockerApp(root)
        app.run()
    except Exception as e:
        print("Error while creating StockerApp:", e)
        raise

if __name__ == "__main__":
    main()