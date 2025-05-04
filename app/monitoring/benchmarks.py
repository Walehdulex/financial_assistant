import time
from datetime import datetime
from app import db
from app.models.portfolio import Portfolio, Holding
from app.models.user import User
from app.services.market_service import MarketService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService
from app.services.performance_service import PerformanceService
from app.services.enhanced_recommendation_service import EnhancedRecommendationService
from app.monitoring.metrics import FeatureMetric

from app.routes.portfolio_routes import ml_service

# Initialize services
market_service = MarketService()
portfolio_service = PortfolioService()
risk_service = RiskService(market_service)
performance_service = PerformanceService(market_service)
recommendation_service = EnhancedRecommendationService(market_service, risk_service, ml_service)


def benchmark_portfolio_valuation(portfolio_id):
    """Benchmark portfolio valuation performance."""
    start_time = time.time()
    portfolio_service.get_portfolio_value(portfolio_id)
    duration = time.time() - start_time

    metric = FeatureMetric(
        feature='portfolio_valuation',
        portfolio_size=Holding.query.filter_by(portfolio_id=portfolio_id).count(),
        execution_time=duration,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()
    return duration


def benchmark_risk_analysis(portfolio_id):
    """Benchmark risk analysis performance."""
    start_time = time.time()
    risk_service.calculate_portfolio_risk(Portfolio.query.get(portfolio_id))
    duration = time.time() - start_time

    metric = FeatureMetric(
        feature='risk_analysis',
        portfolio_size=Holding.query.filter_by(portfolio_id=portfolio_id).count(),
        execution_time=duration,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()
    return duration


def benchmark_recommendation_generation(portfolio_id, user_id):
    """Benchmark recommendation generation performance."""
    start_time = time.time()
    recommendation_service.generate_enhanced_recommendations(
        Portfolio.query.get(portfolio_id),
        User.query.get(user_id)
    )
    duration = time.time() - start_time

    metric = FeatureMetric(
        feature='recommendation_generation',
        portfolio_size=Holding.query.filter_by(portfolio_id=portfolio_id).count(),
        execution_time=duration,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()
    return duration


def benchmark_historical_performance(portfolio_id, timeframe='1m'):
    """Benchmark historical performance calculation."""
    start_time = time.time()
    performance_service.calculate_historical_performance(
        Portfolio.query.get(portfolio_id),
        timeframe
    )
    duration = time.time() - start_time

    metric = FeatureMetric(
        feature='historical_performance',
        portfolio_size=Holding.query.filter_by(portfolio_id=portfolio_id).count(),
        execution_time=duration,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()
    return duration