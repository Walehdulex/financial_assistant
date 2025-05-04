from app.services.history_service import HistoryService


class PerformanceService:
    def __init__(self, market_service):
        self.market_service = market_service
        self.history_service = HistoryService(market_service)

    def calculate_portfolio_performance(self, portfolio):
        try:
            total_value = 0
            total_cost = 0
            performance_data = []

            for holding in portfolio.holdings:
                current_data = self.market_service.get_stock_data(holding.symbol)
                if current_data:
                    current_price = current_data['current_price']
                    current_value = current_price * holding.quantity
                    cost_basis = holding.purchase_price * holding.quantity

                    gain_loss = current_value - cost_basis
                    gain_loss_percentage = (gain_loss / cost_basis * 100) if cost_basis > 0 else 0


                    performance_data.append({
                        'symbol': holding.symbol,
                        'quantity': holding.quantity,
                        'purchase_price': holding.purchase_price,
                        'current_price': current_price,
                        'current_value': current_value,
                        'gain_loss': gain_loss,
                        'gain_loss_percentage': gain_loss_percentage,
                        'purchase_date': holding.purchase_date.strftime('%Y-%m-%d') if holding.purchase_date else None
                    })

                    total_value += current_value
                    total_cost += cost_basis


            #Getting Historical data from the history Service
            historical_data = self.get_historical_data(portfolio)

            return {
                'holdings': performance_data,
                'total_value': total_value,
                'total_cost': total_cost,
                'total_return': total_value - total_cost,
                'total_return_percentage': ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
                'historical_data': historical_data
            }
        except Exception as e:
            print(f"Error calculating portfolio performance: {e}")
            return {
                'holdings': [],
                'total_value': 0,
                'total_cost': 0,
                'total_return': 0,
                'total_return_percentage': 0,
                'historical_data': []
            }


    def get_historical_data(self, portfolio):
        try:
            history_entries = self.history_service.get_portfolio_history(portfolio, days=30)

            historical_data = []

            # Checking if we have any history entries
            if not history_entries:
                return []

            # Calculating cost basis at each point
            total_cost = 0
            for holding in portfolio.holdings:
                total_cost += holding.purchase_price * holding.quantity

            for entry in history_entries:
                # Calculating return percentage based on the total cost
                return_percentage = ((entry.total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

                historical_data.append({
                    'date': entry.date.strftime('%Y-%m-%d'),
                    'value': entry.total_value,
                    'return_percentage': return_percentage
                })

            # Sorting by date (oldest first)
            historical_data.sort(key=lambda x: x['date'])

            return historical_data

        except Exception as e:
            print(f"Error getting historical data: {e}")
            return []



