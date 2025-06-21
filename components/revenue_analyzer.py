# components/revenue_analyzer.py
class RevenueAnalyzer:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        print("RevenueAnalyzer initialized")