from flask import Flask, redirect, url_for, render_template
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
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
    app.config.from_object(config_class)

    mail.init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    #Initializing Scheduler
    scheduler.init_app(app)
    scheduler.start()

    #User Loader
    from app.models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    with app.app_context():

        #Importing Models
        from app.models import User, Portfolio, Holding


        #Registering my Blueprints
        from app.routes import auth_routes, portfolio_routes, market_routes
        from app.routes.auth_routes import bp as auth_bp
        from app.routes.portfolio_routes import bp as portfolio_bp
        from app.routes.market_routes import bp as market_bp
        from app.tasks import record_portfolio_values
        from app.models import User,Portfolio, Holding
        from app.routes.settings_routes import bp as settings_bp
        from app.routes.main_routes import bp as main_bp




        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
        app.register_blueprint(market_bp, url_prefix='/market')
        app.register_blueprint(settings_bp, url_prefix='/settings')
        app.register_blueprint(main_bp, url_prefix='/')

        #Scheduling Daily portfolio value recording
        scheduler.add_job(id='record_portfolio_values', func=record_portfolio_values, trigger='cron', hour=0, minute=0)



        @app.route('/')
        def home():
            return render_template('home.html')
        
        @app.context_processor
        def inject_now():
            return {'now': datetime.utcnow()}

        #Database tables
        db.create_all()

    return app