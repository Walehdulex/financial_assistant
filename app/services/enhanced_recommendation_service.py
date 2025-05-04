import traceback
from datetime import datetime

import requests
from app.models.user import UserSettings

from app.models.recommendation import RecommendationFeedback



class EnhancedRecommendationService:
    def __init__(self, market_service, risk_service, ml_service):
        self.market_service = market_service
        self.risk_service = risk_service
        self.ml_service = ml_service

    def generate_enhanced_recommendations(self, portfolio, user):
        try:
            # Getting user settings
            user_settings = UserSettings.query.filter_by(user_id=user.id).first()
            if not user_settings:
                user_settings = UserSettings(user_id=user.id)

            # Handling missing attributes with defaults
            if not hasattr(user_settings, 'investment_goal'):
                user_settings.investment_goal = 'Growth'  # Default value
            if not hasattr(user_settings, 'time_horizon'):
                user_settings.time_horizon = 'Long-term'  # Default value
            if not hasattr(user_settings, 'preferred_sectors'):
                user_settings.preferred_sectors = ''
            if not hasattr(user_settings, 'tax_consideration'):
                user_settings.tax_consideration = False

            # print("Generating recommendations for portfolio:")
            # print(f"  User: {user.username} (ID: {user.id})")
            # print(f"  Holdings: {[h.symbol for h in portfolio.holdings]}")
            # print(f"  Risk tolerance: {user_settings.risk_tolerance}")

            # Getting user feedback history to learn from past recommendations
            feedback_history = []
            try:
                feedback_history = RecommendationFeedback.query.filter_by(user_id=user.id).all()
            except Exception as e:
                print(f"Error fetching feedback history (this is normal if the table doesn't exist yet): {e}")

            # Analyzing feedback to adjust recommendation priorities
            feedback_adjustments = self._analyze_feedback(feedback_history)

            # Getting portfolio risk data
            risk_data = self.risk_service.calculate_portfolio_risk(portfolio)

            # Getting ML prediction
            symbols = [holding.symbol for holding in portfolio.holdings]
            predictions = self.ml_service.predict_stock_movement(symbols)

            recommendations = []

            # Generating goal-based recommendations
            goal_recs = self._generate_goal_based_recommendations(
                portfolio,
                user_settings.investment_goal,
                user_settings.time_horizon
            )
            if goal_recs:
                recommendations.extend(goal_recs)

            # Generating trade recommendations
            trade_recs = self._generate_trade_recommendations(
                portfolio,
                predictions,
                user_settings.risk_tolerance)
            if trade_recs:
                # Mark which symbols are already in the portfolio
                for rec in trade_recs:
                    if 'symbol' in rec:
                        rec['in_portfolio'] = rec['symbol'] in symbols
                recommendations.extend(trade_recs)

            # Generating diversification recommendations
            div_recs = self._generate_diversification_recommendations(
                portfolio,
                risk_data,
                user_settings.risk_tolerance)
            if div_recs:
                recommendations.extend(div_recs)

            # Generating sector recommendation
            sector_recs = self._generate_sector_recommendations(
                portfolio,
                user_settings.risk_tolerance)
            if sector_recs:
                recommendations.extend(sector_recs)

            # generating goal-based recommendations if investment_goal is available
            try:
                goal_recs = self._generate_goal_based_recommendations(
                    portfolio,
                    user_settings.investment_goal,
                    user_settings.time_horizon
                )
                if goal_recs:
                    recommendations.extend(goal_recs)
            except Exception as e:
                print(f"Error generating goal-based recommendations (likely missing attributes): {e}")

            # generating tax recommendations if tax_consideration is available
            try:
                if user_settings.tax_consideration:
                    tax_recs = self._generate_tax_recommendations(portfolio)
                    if tax_recs:
                        recommendations.extend(tax_recs)
            except Exception as e:
                print(f"Error generating tax recommendations (likely missing attributes): {e}")

            # resolving conflicts between recommendations first
            recommendations = self._resolve_recommendation_conflicts(recommendations)

            # Applying feedback adjustments to recommendations after resolving conflicts
            adjusted_recommendations = []
            for rec in recommendations:
                # Check if we should adjust this recommendation type based on feedback
                if rec['type'] in feedback_adjustments:
                    adjustment = feedback_adjustments[rec['type']]

                    # Skip recommendation types with very low ratings
                    if adjustment['average_rating'] < 2.0 and adjustment['count'] >= 3:
                        continue

                    # Adjust priority based on feedback
                    if adjustment['average_rating'] > 4.0:
                        # Increase priority for highly rated recommendations
                        if rec['priority'] == 'medium':
                            rec['priority'] = 'high'
                    elif adjustment['average_rating'] < 3.0:
                        # Decrease priority for poorly rated recommendations
                        if rec['priority'] == 'high':
                            rec['priority'] = 'medium'
                        elif rec['priority'] == 'medium':
                            rec['priority'] = 'low'

                adjusted_recommendations.append(rec)

            # Sorting by priority
            adjusted_recommendations.sort(key=lambda x: self._get_priority_value(x['priority']), reverse=True)

            return adjusted_recommendations

        except Exception as e:
            print(f"Error generating enhanced recommendations: {e}")
            traceback.print_exc()
            return [{
                'type': 'error',
                'action': 'Unable to generate recommendations',
                'reasoning': 'There was an error analyzing your portfolio',
                'priority': 'medium'
            }]

    def _analyze_feedback(self, feedback_history):
        """Analyzing feedback history to adjust recommendation generation"""
        feedback_adjustments = {}

        # Handling cases where feedback table doesn't exist yet
        if not feedback_history:
            return feedback_adjustments

        # Grouping feedback by recommendation type
        for feedback in feedback_history:
            rec_type = feedback.recommendation_type

            if rec_type not in feedback_adjustments:
                feedback_adjustments[rec_type] = {
                    'total_rating': 0,
                    'count': 0,
                    'follow_rate': 0,
                    'followed_count': 0
                }

            feedback_adjustments[rec_type]['total_rating'] += feedback.rating
            feedback_adjustments[rec_type]['count'] += 1

            if feedback.was_followed:
                feedback_adjustments[rec_type]['followed_count'] += 1

        # Calculating averages
        for rec_type, data in feedback_adjustments.items():
            if data['count'] > 0:
                data['average_rating'] = data['total_rating'] / data['count']
                data['follow_rate'] = int(data['followed_count']) / int(data['count'])
            else:
                data['average_rating'] = 0
                data['follow_rate'] = 0

        return feedback_adjustments

    def _generate_goal_based_recommendations(self, portfolio, investment_goal, time_horizon):
        """Generating recommendations based on investment goals and time horizon"""
        recommendations = []

        # Current portfolio characteristics
        holdings = list(portfolio.holdings)
        symbols = [holding.symbol for holding in holdings]

        # For Income-focused investors
        if investment_goal == 'Income':
            # Check if portfolio has enough dividend stocks
            dividend_count = 0
            for symbol in symbols:
                company_info = self._get_company_info(symbol)
                if company_info and float(company_info.get('DividendYield', 0)) > 0.02:  # 2% yield threshold
                    dividend_count += 1

            # Recommendations If less than 50% of stocks pay meaningful dividends
            if dividend_count < len(symbols) * 0.5:
                recommendations.append({
                    'type': 'goal',
                    'action': 'Consider adding dividend-paying stocks',
                    'reasoning': 'Your portfolio currently has fewer dividend-paying stocks than recommended for an income-focused strategy',
                    'priority': 'high'
                })
        # Recommendation For Preservation-focused investors
        elif investment_goal == 'Preservation':
            # Check volatility
            risk_data = self.risk_service.calculate_portfolio_risk(portfolio)
            if risk_data['volatility'] > 0.15:  # 15% volatility threshold
                recommendations.append({
                    'type': 'goal',
                    'action': 'Consider reducing portfolio volatility',
                    'reasoning': 'Your current volatility exceeds recommended levels for capital preservation',
                    'priority': 'high'
                })
        # Recommendation For Growth investors with short time horizon
        elif investment_goal == 'Growth' and time_horizon == 'Short-term':
            recommendations.append({
                'type': 'goal',
                'action': 'Consider adjusting your time horizon or investment goal',
                'reasoning': 'Growth strategies typically perform better with longer time horizons',
                'priority': 'medium'
            })

        return recommendations

    def _generate_tax_recommendations(self, portfolio):
        """Generating tax optimization recommendations"""
        recommendations = []

        # Current date
        current_date = datetime.now().date()

        # Looking for tax loss harvesting opportunities
        for holding in portfolio.holdings:
            stock_data = self.market_service.get_stock_data(holding.symbol)
            if stock_data:
                current_price = stock_data['current_price']
                purchase_price = holding.purchase_price

                # If the stock is down at least 10%
                if current_price < purchase_price * 0.9:
                    # Check if it's been held for more than 30 days but less than 1 year
                    days_held = (current_date - holding.purchase_date.date()).days
                    if 30 < days_held < 365:
                        recommendations.append({
                            'type': 'tax',
                            'symbol': holding.symbol,
                            'action': f'Consider tax-loss harvesting for {holding.symbol}',
                            'reasoning': f'This position is down {((current_price / purchase_price) - 1) * 100:.1f}% and could offset capital gains',
                            'priority': 'medium'
                        })

        return recommendations

    def _generate_trade_recommendations(self, portfolio, predictions, risk_tolerance, investment_goal=None):
        recommendations = []

        # Thresholds based on risk tolerance
        thresholds = {
            'Conservative': {'buy': 0.08, 'sell': -0.05},
            'Moderate': {'buy': 0.05, 'sell': -0.03},
            'Aggressive': {'buy': 0.03, 'sell': -0.02}
        }

        threshold = thresholds.get(risk_tolerance, thresholds['Moderate'])

        try:
            for symbol, prediction in predictions.items():
                expected_return = prediction['expected_return']

                if expected_return > threshold['buy']:
                    # Buy recommendation
                    recommendations.append({
                        'type': 'buy',
                        'symbol': symbol,
                        'action': f"Increase Position in {symbol}",
                        'reasoning': f"Expected return of {expected_return * 100:.1f}% (target price: ${prediction['target_price']:.2f})",
                        'confidence': prediction['confidence'],
                        'priority': 'high' if expected_return > threshold['buy'] * 1.5 else 'medium'
                    })
                elif expected_return < threshold['sell']:
                    # Sell recommendation
                    recommendations.append({
                        'type': 'sell',
                        'symbol': symbol,
                        'action': f"Reduce Position in {symbol}",
                        'reasoning': f"Potential downside of {-expected_return * 100:.1f}% (target price: ${prediction['target_price']:.2f})",
                        'confidence': prediction['confidence'],
                        'priority': 'high' if expected_return < threshold['sell'] * 1.5 else 'medium'
                    })
        except Exception as e:
            print(f"Error generating trade recommendations: {str(e)}")

        return recommendations

    def _generate_diversification_recommendations(self, portfolio, risk_data, risk_tolerance):
        recommendations = []

        # Checking overall Diversification
        if risk_data['diversification_score'] < 0.6:
            recommendations.append({
                'type': 'diversification',
                'action': 'Increase Portfolio Diversification',
                'reasoning': f"Current diversification score is {risk_data['diversification_score']:.2f}, suggesting high concentration risk",
                'priority': 'high'
            })

        # Checking Individual stock risk
        holdings = list(portfolio.holdings)
        total_value = sum(holding.quantity * self.market_service.get_stock_data(holding.symbol)['current_price']
                          for holding in holdings if self.market_service.get_stock_data(holding.symbol))

        high_concentration = []
        for holding in holdings:
            stock_data = self.market_service.get_stock_data(holding.symbol)
            if stock_data:
                value = holding.quantity * stock_data['current_price']
                weight = value / total_value if total_value > 0 else 0

                # Checking for Over-Concentration (>20% in single stock)
                if weight > 0.2:
                    high_concentration.append({
                        'symbol': holding.symbol,
                        'weight': weight,
                    })

        if high_concentration:
            symbols = ", ".join([item['symbol'] for item in high_concentration])
            recommendations.append({
                'type': 'concentration',
                'action': f"Reduce concentration in {symbols}",
                'reasoning': "Portfolio is heavily concentrated in these positions, increasing risk",
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

        # # Debugging output
        # print("Current sector allocation:")
        # for sector, allocation in sector_allocation.items():
        #     print(f"  {sector}: {allocation:.2%}")

        # Identifying underrepresented sectors (less than 5%)
        underrepresented = []
        major_sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer Defensive',
                         'Energy', 'Communication Services', 'Utilities', 'Industrials']

        for sector in major_sectors:
            allocation = sector_allocation.get(sector, 0)
            if allocation < 0.05:
                underrepresented.append(sector)

        # Skipping recommendation for  sectors that are already well-represented
        for sector in list(sector_allocation.keys()):
            if sector in underrepresented and sector_allocation[sector] >= 0.05:
                underrepresented.remove(sector)

        # Generating recommendations for underrepresented sectors
        for sector in underrepresented:
            # Skipping it if it is a preferred sector that user doesn't want
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

    def _get_priority_value(self, priority):
        priority_values = {
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return priority_values.get(priority, 0)

    # Resolving conflicts between competing recommendations so as not to recommend both buy and sell on the same stock
    def _resolve_recommendation_conflicts(self, recommendations):
        if not recommendations:
            return []

        # Grouping recommendations by symbol
        symbol_groups = {}
        other_recs = []

        for rec in recommendations:
            if 'symbol' in rec and rec['symbol']:
                symbol = rec['symbol']
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append(rec)
            else:
                other_recs.append(rec)

        # Resolving conflicts within each symbol group
        resolved_recommendations = []

        for symbol, recs in symbol_groups.items():
            if len(recs) <= 1:
                # No conflict if only one recommendation per symbol
                resolved_recommendations.extend(recs)
                continue

            # Checking for buy/sell conflicts
            buy_recs = [r for r in recs if r['type'] == 'buy']
            sell_recs = [r for r in recs if r['type'] == 'sell']

            if buy_recs and sell_recs:
                # Resolving based on priority, confidence, and expected return

                # Finding the highest confidence buy and sell recommendations
                best_buy = max(buy_recs, key=lambda x: x.get('confidence', 0) * self._get_priority_value(x['priority']))
                best_sell = max(sell_recs,
                                key=lambda x: x.get('confidence', 0) * self._get_priority_value(x['priority']))

                # Comparing them to decide which to keep
                buy_score = best_buy.get('confidence', 0.5) * self._get_priority_value(best_buy['priority'])
                sell_score = best_sell.get('confidence', 0.5) * self._get_priority_value(best_sell['priority'])

                # If the symbol exists in the portfolio, we slightly favor sell recommendations and vice versa
                portfolio_bias = 1.1 if best_sell.get('in_portfolio', True) else 0.9

                if sell_score * portfolio_bias > buy_score:
                    # Keep the sell recommendation
                    resolved_recommendations.append(best_sell)
                    # Adding a note about the conflict
                    best_sell[
                        'reasoning'] += " (Note: A buy recommendation was also generated but with lower confidence.)"
                else:
                    # We Keep the buy recommendation
                    resolved_recommendations.append(best_buy)
                    # Adding a note about the conflict
                    best_buy[
                        'reasoning'] += " (Note: A sell recommendation was also generated but with lower confidence.)"
            else:
                #If No buy/sell conflict, but might have duplicate recommendations we Keep the one with the highest priority/confidence
                best_rec = max(recs, key=lambda x: x.get('confidence', 0.5) * self._get_priority_value(x['priority']))
                resolved_recommendations.append(best_rec)

        # Resolving conflicts between diversification and concentration recommendations
        div_recs = [r for r in other_recs if r['type'] == 'diversification']
        conc_recs = [r for r in other_recs if r['type'] == 'concentration']

        if div_recs and conc_recs:
            # Conflict between diversification and concentration
            best_div = max(div_recs, key=lambda x: self._get_priority_value(x['priority']))
            best_conc = max(conc_recs, key=lambda x: self._get_priority_value(x['priority']))

            if self._get_priority_value(best_div['priority']) >= self._get_priority_value(best_conc['priority']):
                resolved_recommendations.append(best_div)
                # Filtering out concentration recs that contradict the diversification recommendation
                other_recs = [r for r in other_recs if r not in conc_recs]
            else:
                resolved_recommendations.append(best_conc)
                # Filtering out diversification recs that contradict the concentration recommendation
                other_recs = [r for r in other_recs if r not in div_recs]

        # Add the remaining non-conflicting recommendations
        non_conflict_other_recs = [r for r in other_recs if r not in div_recs and r not in conc_recs]
        resolved_recommendations.extend(non_conflict_other_recs)

        return resolved_recommendations

    def _get_company_info(self, symbol):
        """Getting company information for a stock symbol"""
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.market_service.api_key
            }

            response = requests.get(self.market_service.base_url, params=params)
            data = response.json()

            if not data or 'Symbol' not in data:
                print(f"No company info found for {symbol}")
                return {}

            return data
        except Exception as e:
            print(f"Error getting company info for {symbol}: {e}")
            return {}


    def _get_stock_sectors(self, symbols):
        """Get sectors for a list of stock symbols"""
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

            # try API if not in predefined list
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

                # Add to Data from Api to my mapping for future reference
                SECTOR_MAPPING[symbol] = sector_map[symbol]
            except Exception as e:
                print(f"Error getting sector for {symbol}: {e}")
                sector_map[symbol] = 'Unknown'

        # Debugging output
        # # print(f"Sector mapping for symbols {symbols}:")
        # for symbol, sector in sector_map.items():
        #     print(f"  {symbol}: {sector}")

        return sector_map
