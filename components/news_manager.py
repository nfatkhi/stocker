# components/news_manager.py
class NewsManager:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        print("NewsManager initialized")