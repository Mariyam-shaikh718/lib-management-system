import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///instance/lms.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    BOOKS_PER_PAGE = 12
    MAX_BORROW_DAYS = 14
    MAX_BOOKS_PER_USER = 5
    FINE_PER_DAY = 5.00  # PKR or your currency