from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
# from app.utils.decorators import admin_required
from app.models.user import User
from app.models.portfolio import Portfolio
from app import db
from functools import wraps
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from app.models.portfolio import Holding
from app.routes.portfolio_routes import market_service
from app.models.recommendation import RecommendationFeedback

from app.monitoring.metrics import (
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


bp = Blueprint('admin', __name__)

#Admin access Code
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.')
            return redirect(url_for('auth.login'))

        print(f"User {current_user.username} (ID: {current_user.id}) admin status: {current_user.is_admin}")

        if not current_user.is_admin:
            flash('You do not have permission to access this page.')
            return redirect(url_for('main.home'))

        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    user_count = User.query.count()
    portfolio_count = Portfolio.query.count()
    registration_data = get_registration_data()
    total_feedback = RecommendationFeedback.query.count()
    positive_feedback = RecommendationFeedback.query.filter(RecommendationFeedback.rating >= 4).count()
    recommendation_rate = round((positive_feedback / total_feedback * 100) if total_feedback else 0)
    one_day_ago = datetime.now() - timedelta(days=1)

    # Breakdown
    recent_portfolios = Portfolio.query.filter(Portfolio.created_at >= one_day_ago).count()
    recent_holdings = Holding.query.filter(Holding.purchase_date >= one_day_ago).count()
    recent_feedback = RecommendationFeedback.query.filter(RecommendationFeedback.created_at >= one_day_ago).count()

    recent_activity_count = recent_portfolios + recent_holdings + recent_feedback

    return render_template('admin/dashboard.html',
                           user_count=user_count,
                           portfolio_count=portfolio_count,
                           registration_data=registration_data,
                           recommendation_rate=recommendation_rate,
                           recent_activity_count=recent_activity_count,
                           recent_portfolios=recent_portfolios,
                           recent_holdings=recent_holdings,
                           recent_feedback=recent_feedback
                           )

def get_registration_data():
    # Getting Monthly user registration data for the last 6 months.
    six_months_ago = datetime.now() - timedelta(days=180)

    #Counting Users Grouped by month
    results = db.session.query(
        func.date_format(User.created_at, '%Y-%m-%d').label('day'),
        func.count(User.id).label('count')
    ).filter(
        User.created_at >= six_months_ago
    ).group_by(
        func.date_format(User.created_at, '%Y-%m-%d')
    ).order_by(
        func.date_format(User.created_at, '%Y-%m-%d')
    ).all()

    #Formatting my data for Chart.js
    days = []
    counts = []

    for day, count in results:
        #Converting the month data format like this (2023-01 to Jan 2023)
        day_date = datetime.strptime(day, '%Y-%m-%d')
        formatted_month = day_date.strftime('%b %d, %Y')
        days.append(formatted_month)
        counts.append(count)

    return {
        'months': days,
        'counts': counts
    }

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@bp.route('/make-admin/<int:user_id>')
@login_required
def make_admin(user_id):
    if current_user.id != 1:  # Safeguard to prevent unauthorized access
        return redirect(url_for('main.home'))

    user = User.query.get(user_id)
    if user:
        user.is_admin = True
        db.session.commit()
        flash(f'User {user.username} is now an admin')
    return redirect(url_for('main.home'))


@bp.route('/fix-dates')
@login_required
@admin_required
def fix_dates():
    from datetime import datetime

    # Find users with NULL created_at
    users_to_fix = User.query.filter(User.created_at == None).all()
    count = len(users_to_fix)

    # Set default date
    for user in users_to_fix:
        user.created_at = datetime.utcnow()

    db.session.commit()

    return f"Fixed {count} users with missing dates"

@bp.route('/admin-status')
@login_required
def admin_status():
    return f"""
    <h1>Admin Status Check</h1>
    <p>Username: {current_user.username}</p>
    <p>User ID: {current_user.id}</p>
    <p>Is Admin: {current_user.is_admin}</p>
    <p>User Dict: {vars(current_user)}</p>
    """

@bp.route('/analytics')
@login_required
@admin_required
def analytics():
    # Getting system-wide analytics
    return render_template('admin/analytics.html')

@bp.route('/recommendation-stats')
@login_required
@admin_required
def recommendation_stats():
    # Getting recommendation effectiveness statistics
    recommendation_types = ['Buy', 'Sell', 'Diversification', 'Sector', 'Risk', 'Tax']
    avg_ratings = [db.session.query(func.avg(RecommendationFeedback.rating)).filter(
        RecommendationFeedback.recommendation_type == rec_type).scalar() for rec_type in recommendation_types]

    # Fetching follow-through rate (followed vs not followed)
    followed_count = db.session.query(func.count(RecommendationFeedback.id)).filter(
        RecommendationFeedback.was_followed == True).scalar()
    total_count = db.session.query(func.count(RecommendationFeedback.id)).scalar()
    follow_through_rate = (followed_count / total_count * 100) if total_count else 0

    # Fetching Top recommendations and grouping it
    top_recommendations = db.session.query(
        RecommendationFeedback.recommendation_type,
        RecommendationFeedback.recommendation_action,
        func.avg(RecommendationFeedback.rating).label('avg_rating'),
        func.count(RecommendationFeedback.id).label('times_shown'),
        (func.sum(RecommendationFeedback.was_followed) / func.count(RecommendationFeedback.id) * 100).label('follow_rate')
    ). group_by(
        RecommendationFeedback.recommendation_type,
        RecommendationFeedback.recommendation_action,
    ).order_by(func.avg(RecommendationFeedback.rating).desc()).all()

    return render_template('admin/recommendation_stats.html',
                           recommendation_types=recommendation_types,
                           avg_ratings=avg_ratings,
                           follow_through_rate=follow_through_rate,
                           top_recommendations=top_recommendations)


# User management routes for edit, delete and creating new user
@bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        is_admin = 'is_admin' in request.form

        # Validating  data
        if not username or not email:
            flash('Username and email are required', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))

        # Checking if username or email already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email),
            User.id != user_id
        ).first()

        if existing_user:
            flash('Username or email already exists', 'danger')
            return redirect(url_for('admin.edit_user', user_id=user_id))

        # Updating the  user
        user.username = username
        user.email = email
        user.is_admin = is_admin

        # Checking if password is being updated
        password = request.form.get('password')
        if password and password.strip():
            user.password_hash = generate_password_hash(password)

        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', user=user)


@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # Preventing deleting account of current logged-in user
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'You cannot delete your own account'}), 400

    # Deleting the user
    db.session.delete(user)
    db.session.commit()

    return jsonify({'success': True})


@bp.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    data = request.get_json()

    username = data.get('username', '').strip()
    email = data.get('email').strip()
    password = data.get('password')
    is_admin = data.get('is_admin', False)

    # Validating data
    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'Username, email, and password are required'}), 400

    # Checking if username or email already exists
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        if existing_user.username == username:
            return jsonify({'success': False, 'message': f'Username "{username}" already exists'}), 400
        else:
            return jsonify({'success': False, 'message': f'Email "{email}" already exists'}), 400

    # Creating the new user
    try:
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=is_admin,
            created_at=datetime.utcnow()
        )

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error adding user: {e}")
        return jsonify({'success': False, }), 500


@bp.route('/portfolios/all', methods=['GET'])
@login_required
@admin_required
def get_all_portfolios():
    try:
        portfolios = Portfolio.query.all()

        portfolio_list = []

        for portfolio in portfolios:
            # Calculate total value correctly
            total_value = 0
            for holding in portfolio.holdings:
                stock_data = market_service.get_stock_data(holding.symbol)
                if stock_data:
                    current_price = stock_data['current_price']
                    total_value += current_price * holding.quantity

            portfolio_data = {
                'id': portfolio.id,
                'name': portfolio.name,
                'value': total_value,
                'holdings_count': Holding.query.filter_by(portfolio_id=portfolio.id).count(),
                'created_at': portfolio.created_at.isoformat() if portfolio.created_at else datetime.now().isoformat()
            }

            portfolio_list.append(portfolio_data)

        return jsonify(portfolio_list)

    except Exception as e:
        print(f"Error fetching portfolios: {str(e)}")
        return jsonify({'error': 'Failed to fetch portfolios'}), 500


@bp.route('/performance-metrics')
@login_required
@admin_required
def performance_metrics():
    metrics = {
        'average_response_times': {
            'portfolio_value': get_average_response_time('portfolio.get_holdings'),
            'risk_analysis': get_average_response_time('portfolio.get_risk_analysis'),
            'recommendations': get_average_response_time('portfolio.get_enhanced_recommendations'),
            'historical_performance': get_average_response_time('portfolio.get_historical_performance')
        },
        'percentile_response_times': {
            'portfolio_value': get_percentile_response_time('portfolio.get_holdings'),
            'risk_analysis': get_percentile_response_time('portfolio.get_risk_analysis'),
            'recommendations': get_percentile_response_time('portfolio.get_enhanced_recommendations'),
            'historical_performance': get_percentile_response_time('portfolio.get_historical_performance')
        },
        'system_efficiency': {
            'api_success_rate': get_api_success_rate('alpha_vantage'),
            'cache_hit_rate': get_cache_hit_rate(),
            'cached_response_time': get_average_response_by_cache_status('get_stock_data', True),
            'fresh_response_time': get_average_response_by_cache_status('get_stock_data', False)
        }
    }

    return render_template('admin/performance_metrics.html', metrics=metrics)


@bp.route('/run-benchmarks/<int:portfolio_id>/<int:user_id>')
@login_required
@admin_required
def run_benchmarks(portfolio_id, user_id):
    results = {
        'portfolio_valuation': benchmark_portfolio_valuation(portfolio_id),
        'risk_analysis': benchmark_risk_analysis(portfolio_id),
        'recommendation_generation': benchmark_recommendation_generation(portfolio_id, user_id),
        'historical_performance': benchmark_historical_performance(portfolio_id)
    }

    return render_template('admin/benchmark_results.html', results=results)




