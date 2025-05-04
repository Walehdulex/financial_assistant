import requests
import numpy as np
from datetime import datetime, timedelta
from flask_migrate import current

from app.models.user import UserSettings

from app.models.user import User


class RecommendationService:
    def __init__(self, market_service, risk_service):
        self.market_service = market_service
        self.risk_service = risk_service
        self.sector_targets = {
            'Technology': 0.25,
            'Healthcare': 0.15,
            'Financials': 0.15,
            'Consumer Cyclical': 0.10,
            'Industrials': 0.10,
            'Communication Services': 0.10,
            'Consumer Defensive': 0.05,
            'Energy': 0.05,
            'Utilities': 0.05,
            'Materials': 0.05
        }

    def generate_recommendations(self, portfolio):
        try:
            recommendations = []

            # Get current portfolio allocation and handle it properly
            try:
                holdings = list(portfolio.holdings.all()) # Trying different access method
                # print(f"DEBUG: Found {len(holdings)} holdings")
            except Exception as e:
                # print(f"DEBUG: Error getting holdings: {e}")
                holdings = []

            if not holdings:
                return [{
                    'type': 'general',
                    'recommendation': 'Start building your portfolio by adding diverse stocks across different sectors',
                    'reasoning': 'A diversified portfolio helps reduce risk while maintaining returns',
                    'priority': 'high'
                }]

            # Get portfolio risk metrics
            risk_data = self.risk_service.calculate_portfolio_risk(portfolio)

            # Check diversification
            diversification_rec = self._check_diversification(portfolio, risk_data)
            if diversification_rec:
                recommendations.append(diversification_rec)

            # Modify how we pass the portfolio to these methods
            sector_recs = self._check_sector_allocation(holdings,portfolio)
            recommendations.extend(sector_recs)

            risk_recs = self._check_risk_alignment(portfolio, risk_data)
            if risk_recs:
                recommendations.append(risk_recs)

            rebalance_rec = self._check_rebalancing_needs(portfolio, holdings)
            if rebalance_rec:
                recommendations.append(rebalance_rec)

            # Modify the stock specific recommendations too
            stock_recs = self._generate_stock_specific_recommendations(holdings, portfolio ,risk_data)
            recommendations.extend(stock_recs)

            return recommendations

        except Exception as e:
            print(f"Error generating recommendations: {e}")
            import traceback
            traceback.print_exc()  # Print the full stack trace for debugging
            return [{
                'type': 'error',
                'recommendation': 'Unable to generate recommendations at this time',
                'reasoning': 'There was an error analyzing your portfolio',
                'priority': 'medium'
            }]

    def _check_diversification(self, portfolio, risk_data):
        if risk_data['diversification_score'] < 0.6:
            return {
                'type': 'diversification',
                'recommendation': 'Increase portfolio diversification by adding more stocks from different sectors',
                'reasoning': f'Your diversification score is {risk_data["diversification_score"]:.2f}, which indicates high concentration risk',
                'priority': 'high'
            }
        return None

    def _check_sector_allocation(self, holdings, portfolio):
        """Generating recommendations based on sector allocation"""
        # print(f"Checking sector allocation for portfolio with {len(holdings) if holdings else 0} holdings")

        recommendations = []

        # Guard against empty holdings list
        if not holdings or len(holdings) == 0:
            print("No holdings found for sector allocation")
            return recommendations

        # Print holdings info for debugging
        # for holding in holdings:
        #     print(f"Holding: {holding.symbol if hasattr(holding, 'symbol') else 'Unknown'}")

        # Getting Sector Information for each stock
        sectors = {}
        sector_weights = {}
        total_value = 0

        try:
            # Getting total portfolio value
            for holding in holdings:
                try:
                    if not hasattr(holding, 'symbol') or not hasattr(holding, 'quantity'):
                        print(f"Invalid holding object: {holding}")
                        continue

                    stock_data = self.market_service.get_stock_data(holding.symbol)
                    if stock_data and 'current_price' in stock_data:
                        value = holding.quantity * stock_data['current_price']
                        total_value += value
                        # print(f"Added ${value:.2f} for {holding.symbol} to total value")
                except Exception as e:
                    print(f"Error calculating value for holding: {str(e)}")

            # print(f"Total portfolio value: ${total_value:.2f}")

            # If no value, return empty recommendations
            if total_value <= 0:
                # print("Portfolio has no measurable value")
                return recommendations

            # Getting Sector for each stock and calculate weight
            for holding in holdings:
                try:
                    if not hasattr(holding, 'symbol'):
                        # print(f"Skipping holding without symbol attribute")
                        continue

                    # Getting the company overview from Alpha Vantage
                    params = {
                        'function': 'OVERVIEW',
                        'symbol': holding.symbol,
                        'apikey': self.market_service.api_key
                    }


                except Exception as e:
                    print(f"Error getting sector information for {holding.symbol if hasattr(holding, 'symbol') else 'unknown'}: {str(e)}")

        except Exception as e:
            print(f"Error in sector allocation: {str(e)}")

        return recommendations

    def _check_risk_alignment(self, portfolio, risk_data):
        # Debug the portfolio object
        # print(f"Portfolio ID: {portfolio.id}, User ID: {portfolio.user_id}")

        #Getting user's risk tolerance from user model
        user = User.query.get(portfolio.user_id)

        # getting the ACTUAL user's risk tolerance
        user_settings = UserSettings.query.filter_by(user_id=user.id).first()

        # print(f"User ID from query: {user.id}")
        # print(f"Settings found: {user_settings is not None}")

        if user_settings:
            # print(f"Risk tolerance from DB: {user_settings.risk_tolerance}")
            user_risk_tolerance = user_settings.risk_tolerance
        else:
            # print("No settings found, using default 'Moderate'")
            user_risk_tolerance = 'Moderate'

        # #Debugging my user settings
        # print(f"User risk tolerance: {user_risk_tolerance}")

        #Converting user risk tolerance to numerical boundaries
        risk_tolerance_map = {
            'Conservative': {'max_volatility': 0.12, 'target_sharpe': 0.75},
            'Moderate': {'max_volatility': 0.20, 'target_sharpe': 0.60},
            'Aggressive': {'max_volatility': 0.30, 'target_sharpe': 0.45}
        }

        tolerance_settings = risk_tolerance_map.get(user_risk_tolerance, risk_tolerance_map['Moderate'])

        # # Debugging again
        # print(f"Using tolerance settings: {tolerance_settings}")
        # print(f"Current volatility: {risk_data['volatility'] * 100:.1f}%")


        #Checking if portfolio risk exceeds user's tolerance
        if risk_data['volatility'] > tolerance_settings['max_volatility']:
            return {
                'type': 'risk',
                'recommendation': f"Your portfolio volatility exceeds your {user_risk_tolerance.lower()} risk preference",
                'reasoning': f"Current volatility is {risk_data['volatility'] * 100:.1f}%, which is higher than the {tolerance_settings['max_volatility'] * 100:.1f}% target for your risk profile",
                'priority': 'high'
            }

        #Checking if Sharpe ratio is below target
        if risk_data['sharpe_ratio'] < tolerance_settings['target_sharpe']:
            return {
                'type': 'risk_efficiency',
                'recommendation': "Your portfolio has suboptimal risk-adjusted returns",
                'reasoning': f"Current Sharpe ratio is {risk_data['sharpe_ratio']:.2f}, below the target of {tolerance_settings['target_sharpe']:.2f} for your risk profile",
                'priority': 'medium'
            }
        return None

    def _check_rebalancing_needs(self, portfolio, holdings):
        if not holdings:
            holdings = list(portfolio.holdings.all())
        total_value = 0
        current_weights = {}

        #Calculating Current weights
        for holding in holdings:
            stock_data = self.market_service.get_stock_data(holding.symbol)
            if stock_data:
                current_price = stock_data['current_price']
                value = holding.quantity * current_price
                total_value += value
                current_weights[holding.symbol] = {
                    'value': value,
                    'weight': 0   #Calculates after getting total
                }
        #Updating weights
        for symbol in current_weights:
            current_weights[symbol]['weight'] = current_weights[symbol]['value'] / total_value if total_value > 0 else 0

        #Calculating target weights  (for simplicity, equal weight strategy)
        count = len(current_weights)
        target_weight = 1.0 / count if count > 0 else 0

        #Identifyin Positions that need rebalancing
        rebalance_needed = False
        positions_to_increase = []
        positions_to_decrease = []

        for symbol, data in current_weights.items():
            current = data['weight']

            #Checking if it needs rebalancing( more than 5% off target)
            if abs(current - target_weight) > 0.05:
                rebalance_needed = True

                if current < target_weight:
                    positions_to_increase.append({
                        'symbol': symbol,
                        'current': current,
                        'target': target_weight,
                        'gap': target_weight - current
                    })
                else:
                    positions_to_decrease.append({
                        'symbol': symbol,
                        'current': current,
                        'target': target_weight,
                        'gap': current - target_weight
                    })

        if rebalance_needed:
            #Sort by the largest gaps
            positions_to_increase.sort(key=lambda x: x['gap'], reverse=True)
            positions_to_decrease.sort(key=lambda x: x['gap'], reverse=True)

            increase_text = ", ".join([p['symbol'] for p in positions_to_increase[:3]])
            decrease_text = ", ".join([p['symbol'] for p in positions_to_decrease[:3]])

            rebalance_msg = "Consider rebalancing your portfolio "
            if positions_to_increase:
                rebalance_msg += f"Increase {increase_text}"
            if positions_to_increase and positions_to_decrease:
                rebalance_msg += " and "
            if positions_to_decrease:
                rebalance_msg += f" Decrease {decrease_text}"

            return {
                'type': 'rebalance',
                'recommendation': rebalance_msg,
                'reasoning': "Some positions have drifted significantly from their target allocations, which may increase risk or reduce returns",
                'priority': 'medium' if abs(positions_to_increase[0]['gap'] if positions_to_increase else 0) > 0.1 else 'low'
            }

        return None

    def _generate_stock_specific_recommendations(self, holdings, portfolio, risk_data):
        recommendations = []

        for symbol, risk in risk_data['individual_stock_risks'].items():
            if risk['volatility'] > 0.3:
                recommendations.append({
                    'type': 'stock_specific',
                    'symbol': symbol,
                    'recommendation':  f'Consider reducing your position in {symbol}',
                    'reasoning': f'{symbol} has high volatility ({risk["volatility"]:.2f}) which increases your portfolio risk',
                    'priority': 'medium'
                })
        return recommendations

    def _generate_sector_recommendations(self, portfolio, risk_tolerance, preferred_sectors=None):
        """Generating recommendations based on sector allocation"""
        recommendations = []

        # Skipping if portfolio is empty
        holdings = list(portfolio.holdings.all())
        if not holdings:
            return recommendations

        # Getting all the symbols
        symbols = [holding.symbol for holding in holdings]

        # Gettting sector for each stock
        sector_map = self._get_stock_sectors(symbols)

        # Calculating sector allocation by value
        total_value = 0
        sector_values = {}

        for holding in holdings:
            symbol = holding.symbol
            stock_data = self.market_service.get_stock_data(symbol)
            if stock_data:
                sector = sector_map.get(symbol, 'Unknown')
                value = holding.quantity * stock_data['current_price']

                if sector not in sector_values:
                    sector_values[sector] = 0

                sector_values[sector] += value
                total_value += value

        # Calculating percentages
        sector_allocation = {}
        for sector, value in sector_values.items():
            sector_allocation[sector] = value / total_value if total_value > 0 else 0

        # Debugging output
        # # print("Current sector allocation:")
        # for sector, allocation in sector_allocation.items():
        #     print(f"  {sector}: {allocation:.2%}")

        # Identifying underrepresented sectors (less than 5%)
        underrepresented = []
        major_sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer Defensive', 'Energy']

        for sector in major_sectors:
            allocation = sector_allocation.get(sector, 0)
            if allocation < 0.05:
                underrepresented.append(sector)

        # Skipping recommendation for  sectors that are already well-represented
        if 'Technology' in sector_allocation and sector_allocation['Technology'] >= 0.15:
            if 'Technology' in underrepresented:
                underrepresented.remove('Technology')

        # Generating recommendations for underrepresented sectors
        for sector in underrepresented:
            # Skippping it if it is a preferred sector that user doesn't want
            if preferred_sectors and sector not in preferred_sectors:
                continue

            recommendations.append({
                'type': 'sector',
                'sector': sector,
                'action': f'Consider adding {sector.lower()} exposure',
                'reasoning': f'{sector} sector is underrepresented in your portfolio',
                'priority': 'low'
            })

            return recommendations

    def _get_stock_sectors(self, symbols):
        """Getting sectors for a list of stock symbols"""
        sector_map = {}

        # pre-defined mapping for common stocks
        SECTOR_MAPPING = {
            # Technology
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'GOOG': 'Technology', 'META': 'Technology', 'AMZN': 'Technology',
            'NFLX': 'Technology', 'NVDA': 'Technology', 'AMD': 'Technology',
            'INTC': 'Technology', 'CSCO': 'Technology', 'ORCL': 'Technology',
            'IBM': 'Technology', 'ADBE': 'Technology', 'CRM': 'Technology',
            'AAME': 'Technology',

            # Healthcare
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare',
            'ABBV': 'Healthcare', 'MRK': 'Healthcare', 'TMO': 'Healthcare',
            'ABT': 'Healthcare', 'DHR': 'Healthcare', 'BMY': 'Healthcare',

            # Financials
            'JPM': 'Financials', 'BAC': 'Financials', 'WFC': 'Financials',
            'C': 'Financials', 'GS': 'Financials', 'MS': 'Financials',
            'BLK': 'Financials', 'AXP': 'Financials', 'V': 'Financials',
            'MA': 'Financials',

            # Consumer Defensive
            'PG': 'Consumer Defensive', 'KO': 'Consumer Defensive', 'PEP': 'Consumer Defensive',
            'WMT': 'Consumer Defensive', 'COST': 'Consumer Defensive',

            # Energy
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy',
            'SLB': 'Energy', 'EOG': 'Energy',

            # Communication Services
            'VZ': 'Communication Services', 'T': 'Communication Services',
            'CMCSA': 'Communication Services', 'CHTR': 'Communication Services',
            'DIS': 'Communication Services',

            # Utilities
            'NEE': 'Utilities', 'DUK': 'Utilities', 'SO': 'Utilities',
            'D': 'Utilities', 'AEP': 'Utilities',

            # Industrials
            'HON': 'Industrials', 'UNP': 'Industrials', 'UPS': 'Industrials',
            'BA': 'Industrials', 'CAT': 'Industrials', 'GE': 'Industrials',

            # Materials
            'LIN': 'Materials', 'APD': 'Materials', 'ECL': 'Materials',
            'DD': 'Materials', 'DOW': 'Materials',

            # Real Estate
            'AMT': 'Real Estate', 'PLD': 'Real Estate', 'CCI': 'Real Estate',
            'EQIX': 'Real Estate', 'PSA': 'Real Estate'
        }

        for symbol in symbols:
            # First check our predefined mapping
            if symbol in SECTOR_MAPPING:
                sector_map[symbol] = SECTOR_MAPPING[symbol]
                continue

            # trying to use  API if not in predefined list
            try:
                params = {
                    'function': 'OVERVIEW',
                    'symbol': symbol,
                    'apikey': self.market_service.api_key
                }

                response = requests.get(self.market_service.base_url, params=params)
                data = response.json()

                if 'Sector' in data:
                    sector_map[symbol] = data['Sector']
                else:
                    sector_map[symbol] = 'Unknown'

                # Adding to Data from Api to my mapping for future reference
                SECTOR_MAPPING[symbol] = sector_map[symbol]
            except Exception as e:
                # print(f"Error getting sector for {symbol}: {e}")
                sector_map[symbol] = 'Unknown'

        # # Debugging output
        # # print(f"Sector mapping for symbols {symbols}:")
        # for symbol, sector in sector_map.items():
        #     print(f"  {symbol}: {sector}")

        return sector_map




