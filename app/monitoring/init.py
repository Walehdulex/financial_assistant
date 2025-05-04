from app.monitoring.metrics import (
    measure_response_time,
    track_api_call,
    track_cache_access,
    track_response_with_cache_status,
    get_average_response_time,
    get_percentile_response_time,
    get_api_success_rate,
    get_cache_hit_rate,
    get_average_response_by_cache_status
)

from app.monitoring.benchmarks import (
    benchmark_portfolio_valuation,
    benchmark_risk_analysis,
    benchmark_recommendation_generation,
    benchmark_historical_performance
)