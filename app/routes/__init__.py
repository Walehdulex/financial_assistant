import time
from functools import wraps
from flask import Blueprint, g, request
from app.monitoring.metrics import measure_response_time

bp = Blueprint('main', __name__)

def track_request_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.start_time = time.time()
        response = f(*args, **kwargs)
        measure_response_time(request.endpoint, g.start_time)
        return response
    return decorated_function