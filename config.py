import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql+pymysql://root:mKhZKiEoojnoLbYRnjfJiudjFoatnrAS@mysql.railway.internal:3306/railway")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALPHA_VANTAGE_API_KEY = 'F3FVLPKT5JEIRH70'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    if os.getenv("FLASK_ENV") == "production":
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    else:
         SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "mysql+pymysql://root:mKhZKiEoojnoLbYRnjfJiudjFoatnrAS@mysql.railway.internal:3306/railway")
        # SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:yourpassword@localhost/financial_assistant'
      