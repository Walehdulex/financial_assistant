from datetime import datetime, timedelta
from app import db
import time


# Metric Models
class ResponseMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(100))
    response_time = db.Column(db.Float)  # in seconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class FeatureMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    feature = db.Column(db.String(100))
    portfolio_size = db.Column(db.Integer)
    execution_time = db.Column(db.Float)  # in seconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class APIMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(100))
    endpoint = db.Column(db.String(100))
    success = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CacheMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255))
    hit = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CachedResponseMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(100))
    response_time = db.Column(db.Float)
    cached = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Metric Recording Functions
def measure_response_time(route_name, start_time):
    """Record response time for a specific route."""
    duration = time.time() - start_time
    metric = ResponseMetric(
        route=route_name,
        response_time=duration,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()
    return duration


def track_api_call(provider, endpoint, success):
    """Tracking API call success/failure."""
    metric = APIMetric(
        provider=provider,
        endpoint=endpoint,
        success=success,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()


def track_cache_access(cache_key, hit):
    """Tracking cache hit/miss."""
    metric = CacheMetric(
        cache_key=cache_key,
        hit=hit,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()


def track_response_with_cache_status(route_name, duration, cached):
    """Tracking response time with cache status."""
    metric = CachedResponseMetric(
        route=route_name,
        response_time=duration,
        cached=cached,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()


def track_response_with_cache_status(route_name, duration, cached):
    """Tracking response time with cache status."""
    # Adding logging to debug the values
    # print(f"Cache status: {'HIT' if cached else 'MISS'}, Route: {route_name}, Duration: {duration}ms")

    metric = CachedResponseMetric(
        route=route_name,
        response_time=duration,
        cached=cached,
        timestamp=datetime.now()
    )
    db.session.add(metric)
    db.session.commit()


# Metric Reporting Functions
def get_average_response_time(route_name, time_window=24):
    """Get average response time for a route over time window (hours)."""
    cutoff_time = datetime.now() - timedelta(hours=time_window)
    metrics = ResponseMetric.query.filter(
        ResponseMetric.route == route_name,
        ResponseMetric.timestamp >= cutoff_time
    ).all()

    if not metrics:
        return 0

    total_time = sum([m.response_time for m in metrics])
    return total_time / len(metrics)


def get_percentile_response_time(route_name, percentile=95, time_window=24):
    """Get the 95th percentile response time for a route over the last 24 hours."""
    cutoff_time = datetime.now() - timedelta(hours=time_window)
    metrics = ResponseMetric.query.filter(
        ResponseMetric.route == route_name,
        ResponseMetric.timestamp >= cutoff_time
    ).all()

    if not metrics:
        return 0

    response_times = sorted([m.response_time for m in metrics])
    index = int(len(response_times) * (percentile / 100))
    return response_times[min(index, len(response_times) - 1)]


def get_api_success_rate(provider, time_window=24):
    """Get API success rate over time window (hours)."""
    cutoff_time = datetime.now() - timedelta(hours=time_window)
    total_calls = APIMetric.query.filter(
        APIMetric.provider == provider,
        APIMetric.timestamp >= cutoff_time
    ).count()

    successful_calls = APIMetric.query.filter(
        APIMetric.provider == provider,
        APIMetric.success == True,
        APIMetric.timestamp >= cutoff_time
    ).count()

    if total_calls == 0:
        return 100.0

    return (successful_calls / total_calls) * 100


def get_cache_hit_rate(time_window=24):
    """Get cache hit rate over time window (hours)."""
    cutoff_time = datetime.now() - timedelta(hours=time_window)
    total_access = CacheMetric.query.filter(
        CacheMetric.timestamp >= cutoff_time
    ).count()

    hits = CacheMetric.query.filter(
        CacheMetric.hit == True,
        CacheMetric.timestamp >= cutoff_time
    ).count()

    if total_access == 0:
        return 0.0

    return (hits / total_access) * 100


def get_average_response_by_cache_status(route_name, cached=True, time_window=24):
    """Get average response time based on cache status."""
    cutoff_time = datetime.now() - timedelta(hours=time_window)
    metrics = CachedResponseMetric.query.filter(
        CachedResponseMetric.route == route_name,
        CachedResponseMetric.cached == cached,
        CachedResponseMetric.timestamp >= cutoff_time
    ).all()

    if not metrics:
        return 0

    total_time = sum([m.response_time for m in metrics])
    return total_time / len(metrics)