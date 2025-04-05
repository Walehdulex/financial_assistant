import requests
from datetime import datetime, timedelta
import time




class NewsService:
    def __init__(self, marketService):
        self.market_service = marketService
        self.api_key = self.market_service.api_key
        self.base_url = 'https://www.alphavantage.co/query'

    def get_news_for_portfolio(self, holdings, limit=3):
        news_items = []
        symbols = [holding.symbol for holding in holdings]


        for symbol in symbols:
            news = self.get_company_news(symbols)
            if news:
                news_items.extend(news)
            time.sleep(1) #Rate Limiter

        #Sort by date and limit
        news_items.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        return news_items[:limit]

    def get_company_news(self, symbol):
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'tickers': symbol,
                'apikey': self.api_key,
                'limit': 5
            }

            response = requests.get(self.base_url, params=params)
            data = response.json()

            if 'feed' in data:
                return [self._format_news_item(item, symbol) for item in data['feed']]
            return []
        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            return []

    def _format_news_item(self, item, symbol):
        return {
            'title': item.get('title', 'No Title'),
            'summary': item.get('summary', 'No Summary available'),
            'url': item.get('url', '#'),
            'source': item.get('source', 'Unknown'),
            'published_at': item.get('time_published', ''),
            'sentiment': item.get('overall_sentiment', 'neutral'),
            'symbol': symbol
        }
