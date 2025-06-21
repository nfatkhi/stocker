# data/models.py
"""Data models used throughout the application"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

@dataclass
class StockData:
    """Container for all stock data"""
    ticker: str
    company_info: Dict[str, Any]
    price_history: pd.DataFrame
    financials: pd.DataFrame
    news: List[Dict[str, str]]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class AnalysisResult:
    """Results from stock analysis"""
    ticker: str
    score: float
    revenue_growth: float
    free_cash_flow: float
    debt_to_equity: float
    recommendation: str
    key_metrics: Dict[str, float]
    warnings: List[str]
    strengths: List[str]