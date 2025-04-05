from app.models.user import UserSettings

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

            # Getting portfolio risk data
            risk_data = self.risk_service.calculate_portfolio_risk(portfolio)

            # Getting ML prediction
            symbols = [holding.symbol for holding in portfolio.holdings]
            predictions = self.ml_service.predict_stock_movement(symbols)

            recommendations = []

            #Generating Trade Ideas
            trade_recs = self._generate_trade_recommendations(portfolio, predictions, user_settings.risk_tolerance)
            if trade_recs:
                recommendations.extend(trade_recs)


            #Generating diversification recommendations
            div_recs = self._generate_diversification_recommendations(portfolio, risk_data, user_settings.risk_tolerance)
            if div_recs:
                recommendations.extend(div_recs)

            #Generating sector recommendation
            sector_recs = self._generate_sector_recommendatiomns(portfolio,user_settings.risk_tolerance)
            if sector_recs:
                recommendations.extend(sector_recs)

            #Sorting by priority
            recommendations.sort(key=lambda x: self._get_priority_value(x['priority']), reverse=True)

            return recommendations

        except Exception as e:
            print(f"Error generating enhanced recommendations: {e}")
            import traceback
            traceback.print_exc()
            return [{
                'type': 'error',
                'action': 'Unable to generate recommendations',
                'reasoning': 'There was an error analyzing your portfolio',
                'priority': 'medium'
            }]

    def _generate_trade_recommendations(self, portfolio, predictions, risk_tolerance):
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

        #Checking overall Diversification
        if risk_data['diversification_score'] < 0.6:
            recommendations.append({
                'type': 'diversification',
                'action': 'Increase Portfolio Diversification',
                'reasoning': f"Current diversification score is {risk_data['diversification_score']:.2f}, suggesting high concentration risk",
                'priority': 'high'
            })

        #Checking Individual stock risk
        holdings = list(portfolio.holdings)
        total_value = sum(holding.quantity * self.market_service.get_stock_data(holding.symbol)['current_price']
                          for holding in holdings if self.market_service.get_stock_data(holding.symbol))


        high_concentration = []
        for holding in holdings:
            stock_data = self.market_service.get_stock_data(holding.symbol)
            if stock_data:
                value = holding.quantity * stock_data['current_price']
                weight = value / total_value if total_value > 0 else 0

                #Checking for Over-Concentration (>20% in single stock)
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

    def _generate_sector_recommendatiomns(self, portfolio,risk_tolerance):
        # This is a placeholder - in a full implementation you would:
        # 1. Get sector data for each holding
        # 2. Calculate sector weights
        # 3. Compare to target sector allocation
        # 4. Generate recommendations for underweight/overweight sectors

        return [{
            'type': 'sector',
            'action': 'Consider adding technology exposure',
            'reasoning': 'Technology sector is underrepresented in your portfolio',
            'priority': 'low'
        }]

    def _get_priority_value(self, priority):
        priority_values = {
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return priority_values.get(priority, 0)


