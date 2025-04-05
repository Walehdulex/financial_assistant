from http.client import responses

import numpy as np
from datetime import datetime, timedelta
import pandas as pd
import requests
from config import Config


class RiskService:
    def __init__(self, market_service):
        self.market_service = market_service
        self.risk_free_rate = 0.04 #(setting this at 4% risk_free rate)
        self.api_key = Config.ALPHA_VANTAGE_API_KEY
        self.base_url = 'https://www.alphavantage.co/query'

    def calculate_portfolio_risk(self, portfolio):
        try:
            # Getting Historical data for all Stocks
            symbols = [holding.symbol for holding in portfolio.holdings]
            if not symbols:
                return {
                    'volatility': 0,
                    'sharpe_ratio': 0,
                    'diversification_score': 0,
                    'risk_level': 'N/A',
                    'individual_stock_risks': {}
                }

            historical_data = self._get_historical_prices(symbols)

            # historical_data = historical_data.ffill()  # Forward-filling  missing values

            # Calculating returns
            returns = historical_data.pct_change().dropna()

            if returns.empty:
                return {
                    'volatility': 0,
                    'sharpe_ratio': 0,
                    'diversification_score': 0,
                    'risk_level': 'N/A',
                    'individual_stock_risks': {}
                }

            # Calculating Porfolio weights
            total_value = 0
            for holding in portfolio.holdings:
                stock_data = self.market_service.get_stock_data(holding.symbol)
                if stock_data:
                    total_value += (holding.quantity * stock_data['current_price'])

            weights = []
            for holding in portfolio.holdings:
                stock_data = self.market_service.get_stock_data(holding.symbol)
                if stock_data:
                    weights.append(holding.quantity * stock_data['current_price'] / total_value if total_value > 0 else 0)


            # Calculating Portfolio Metrics
            portfolio_volatility = self._calculate_portfolio_volatility(returns, weights)
            sharpe_ratio = self._calculate_sharpe_ratio(returns, weights)
            diversification_score = self._calculate_diversification_score(weights)

            return {
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'diversification_score': diversification_score,
                'risk_level': self.determine_risk_level(portfolio_volatility),
                'individual_stock_risks': self.calculate_individual_stock_risks(returns)
            }

        except Exception as e:
            print(f"Error calculating portfolio risk: {e}")
            return {
                'volatility': 0,
                'sharpe_ratio': 0,
                'diversification_score': 0,
                'risk_level': 'Error',
                'individual_stock_risks': {}
            }

    def _get_historical_prices(self, symbols, period='1y'):
        data = pd.DataFrame()

        for symbol in symbols:
            #Api configuration for daily time series
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.api_key,
                'outputsize': 'compact' #Just the last 100 data points
            }

            try:
                print(f"Fetching historical data for {symbol}...")
                response = requests.get(self.base_url, params=params)
                result = response.json()

                if 'Time Series (Daily)' in result:
                    time_series = result['Time Series (Daily)']


                    #Converting the time Series to DataFrame
                    dates = []
                    prices = []
                    for date, values in time_series.items():
                        dates.append(date)
                        prices.append(float(values['4. close']))

                    # #Adding Data to main DataFrame
                    symbol_df = pd.DataFrame({symbol: prices}, index=pd.DatetimeIndex(dates))


                    #Appending to main dataframe
                    if data.empty:
                        data = symbol_df
                    else:
                        data = data.join(symbol_df, how='outer')

            except Exception as e:
                print(f"Error fetching historical data for {symbol}: {e}")

            #Delay to avoid rate limiting
            import time
            time.sleep(1)

        return data

    def _calculate_portfolio_volatility(self, returns, weights):
        if returns.empty or not weights:
            return 0

        cov_matrix = returns.cov() * 252 # Annualized
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        return np.sqrt(portfolio_variance)

    def _calculate_sharpe_ratio(self, returns, weights):
        if returns.empty or not weights:
            return 0

        portfolio_returns = np.sum(returns.mean() * weights) * 252 # Annualized
        porfolio_volatility = self._calculate_portfolio_volatility(returns, weights)

        if porfolio_volatility == 0:
            return 0

        return (portfolio_returns - self.risk_free_rate) / porfolio_volatility

    def _calculate_diversification_score(self, weights):
        # diversification score based on Herfindahl-Hirschman Index
        if not weights:
            return 0

        return 1 - sum(w**2 for w in weights)

    def determine_risk_level(self, volatility):
        if volatility < 0.15:
            return 'Low'
        elif volatility < 0.25:
            return 'Medium'
        else:
            return 'High'

    def calculate_individual_stock_risks(self, returns):
        risks ={}
        for column in returns.columns:
            volatility = returns[column].std() * np.sqrt(252) # Annualized
            risks[column] = {
                'volatility': volatility,
                'risk_level': self.determine_risk_level(volatility)
            }
        return risks










