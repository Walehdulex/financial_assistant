from flask import Flask, redirect, url_for, render_template
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from config import Config
from flask_migrate import Migrate
from flask_apscheduler import APScheduler
from datetime import datetime


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
scheduler = APScheduler()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')

    if config_class == 'testing':
        app.config.from_object('config.TestConfig')
    else:
        app.config.from_object(config_class)


    #Initializing Extensions
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    #Initializing Scheduler
    scheduler.init_app(app)
    if config_class != 'testing':
        scheduler.start()

    #User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():

        #Importing Models
        from app.models import User, Portfolio, Holding
        from app.models.notification import Notification


        #Registering my Blueprints
        from app.routes import auth_routes, portfolio_routes, market_routes
        from app.routes.auth_routes import bp as auth_bp
        from app.routes.portfolio_routes import bp as portfolio_bp
        from app.routes.market_routes import bp as market_bp
        from app.tasks import record_portfolio_values
        from app.models import User,Portfolio, Holding
        from app.routes.settings_routes import bp as settings_bp
        from app.routes.main_routes import bp as main_bp
        from app.routes.education_routes import bp as education_bp
        from app.routes.admin_routes import bp as admin_bp
        from app.routes import notification_routes
        # from app.routes.report_routes import bp
        from app.routes.report_routes import bp as report_bp




        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
        app.register_blueprint(market_bp, url_prefix='/market')
        app.register_blueprint(settings_bp, url_prefix='/settings')
        app.register_blueprint(main_bp)
        app.register_blueprint(education_bp, url_prefix='/education')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(notification_routes.bp, url_prefix='/notifications')
        # app.register_blueprint(bp)
        app.register_blueprint(report_bp, url_prefix='/reports')

        # Only scheduling jobs in production, not in testing
        if config_class != 'testing':
            from app.tasks import record_portfolio_values
            scheduler.add_job(id='record_portfolio_values', func=record_portfolio_values,
                              trigger='cron', hour=0, minute=0)

        # #Scheduling Daily portfolio value recording
        # scheduler.add_job(id='record_portfolio_values', func=record_portfolio_values, trigger='cron', hour=0, minute=0)



        @app.route('/')
        def home():
            return render_template('home.html')

        @app.context_processor
        def inject_now():
            return {'now': datetime.utcnow()}

        @app.context_processor
        def notification_processor():
            if current_user.is_authenticated:
                notification_count = Notification.query.filter_by(
                    user_id=current_user.id, is_read=False).count()
                recent_notifications = Notification.query.filter_by(
                    user_id=current_user.id).order_by(
                    Notification.created_at.desc()).limit(5).all()
                return {
                    'notification_count': notification_count,
                    'recent_notifications': recent_notifications
                }
            return {'notification_count': 0, 'recent_notifications': []}

        @app.template_filter('time_ago')
        def time_ago_filter(timestamp):
            """
            Convert a timestamp to a human-readable "time ago" string
            like "2 minutes ago" or "3 days ago"
            """
            now = datetime.utcnow()
            diff = now - timestamp

            seconds = diff.total_seconds()

            if seconds < 60:
                return "just now"
            elif seconds < 3600:
                minutes = int(seconds / 60)
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds / 3600)
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif seconds < 604800:
                days = int(seconds / 86400)
                return f"{days} day{'s' if days > 1 else ''} ago"
            elif seconds < 2592000:
                weeks = int(seconds / 604800)
                return f"{weeks} week{'s' if weeks > 1 else ''} ago"
            else:
                return timestamp.strftime("%Y-%m-%d")

        #Database tables
        db.create_all()

    return app