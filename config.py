import os
from dotenv import load_dotenv

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")
    
    # Default to development environment (local database) unless in production
    if os.getenv("FLASK_ENV") == "production":
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")  # For production
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql+pymysql://root:Dulex231@localhost/financial_assistant")  # For local or development

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALPHA_VANTAGE_API_KEY =os.getenv("ALPHA_VANTAGE_API_KEY")
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    REPORT_DIR = os.path.join(basedir, 'instance', 'reports')
    os.makedirs(REPORT_DIR, exist_ok=True)

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False  # Disable CSRF protection for testing
    ALPHA_VANTAGE_API_KEY = 'test_key'  # Mock API key for testing
    SCHEDULER_API_ENABLED = False
    SCHEDULER_ENABLED = False
