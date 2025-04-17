import os
from datetime import timedelta


class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://postgres:mirka2003@localhost/crm'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Login settings
    REMEMBER_COOKIE_DURATION = timedelta(days=7)

    # Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # Logging
    LOG_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:mirka2003@localhost/crm_test'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}