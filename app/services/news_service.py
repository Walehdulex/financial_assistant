import requests
from datetime import datetime, timedelta
import time

class NewsService:
    def __init__(self, marketService):
        self.market_service = marketService
        self.api_key = self.market_service.api_key
        self.base_url = 'https://www.alphavantage.co/query'

    def get_news_for_portfolio(self, holdings, limit=6):
        news_items = []
        symbols = [holding.symbol for holding in holdings]

        for symbol in symbols:
            news = self.get_company_news(symbol)
            if news:
                news_items.extend(news)
            time.sleep(1)  # Rate Limiter

        # Sorting by date
        news_items.sort(key=lambda x: x.get('published_at', ''), reverse=True)

        # Grouping by sentiment
        positive_news = [item for item in news_items if item['sentiment'] in ['bullish', 'somewhat-bullish']]
        neutral_news = [item for item in news_items if item['sentiment'] == 'neutral']
        negative_news = [item for item in news_items if item['sentiment'] in ['bearish', 'somewhat-bearish']]

        # Selecting a mix of news (prioritizing diverse sentiment)
        result = []
        if negative_news: result.append(negative_news[0])
        if positive_news: result.append(positive_news[0])
        if neutral_news: result.append(neutral_news[0])

        # Filling the  remaining slots with most recent news
        remaining_count = limit - len(result)
        if remaining_count > 0:
            remaining_news = [n for n in news_items if n not in result]
            result.extend(remaining_news[:remaining_count])

        return result[:limit]

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

            # # Debug: Print raw data structure
            # print(f"Raw response for {symbol}: {data}")

            if 'feed' in data:
                news_items = [self._format_news_item(item, symbol) for item in data['feed']]

                # Debug: Count sentiment distribution
                sentiment_counts = {}
                for item in news_items:
                    sentiment = item['sentiment']
                    sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
                # print(f"Sentiment distribution for {symbol}: {sentiment_counts}")

                return news_items
            return []
        except Exception as e:
            print(f"Error fetching news for {symbol}: {e}")
            return []

    def _format_news_item(self, item, symbol):
        # Get the sentiment values
        overall_sentiment_score = float(item.get('overall_sentiment_score', 0))
        overall_sentiment_label = item.get('overall_sentiment_label', 'Neutral')

        # Look for ticker-specific sentiment if available
        ticker_sentiment = None
        for ticker_data in item.get('ticker_sentiment', []):
            if ticker_data.get('ticker') == symbol:
                ticker_sentiment_score = float(ticker_data.get('ticker_sentiment_score', 0))
                ticker_sentiment_label = ticker_data.get('ticker_sentiment_label', 'Neutral')
                ticker_sentiment = ticker_sentiment_label.lower()
                break

        # Using the ticker-specific sentiment if available, otherwise use overall
        sentiment = ticker_sentiment if ticker_sentiment else overall_sentiment_label.lower()

        # Map to simpler categories for UI
        if sentiment in ['bullish', 'somewhat-bullish']:
            display_sentiment = 'positive'
        elif sentiment in ['bearish', 'somewhat-bearish']:
            display_sentiment = 'negative'
        else:
            display_sentiment = 'neutral'

        return {
            'title': item.get('title', 'No Title'),
            'summary': item.get('summary', 'No Summary available'),
            'url': item.get('url', '#'),
            'source': item.get('source', 'Unknown'),
            'published_at': item.get('time_published', ''),
            'sentiment': display_sentiment,
            'symbol': symbol
        }

    def get_general_market_news(self, limit=5):
        try:
            params = {
                'function': 'NEWS_SENTIMENT',
                'topics': 'financial_markets,economy_macro',
                'apikey': self.api_key,
                'limit': limit
            }

            response = requests.get(self.base_url, params=params)
            data = response.json()

            news_items = []
            if 'feed' in data:
                for item in data['feed'][:limit]:
                    news_items.append(self._format_news_item(item, ''))
            return news_items
        except Exception as e:
            print(f"Error fetching market news: {e}")
            return []