from flask import Blueprint

bp = Blueprint('main', __name__)

from app.routes import auth_routes, portfolio_routes, market_routes, main_routes, settings_routes