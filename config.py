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
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # Logging
    LOG_FOLDER = os.path.join(BASE_DIR, 'logs')

    # Pagination
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100


class DevelopmentConfig(Config):
    DEBUG = True
    # For development, we'll use a separate database if specified
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or Config.SQLALCHEMY_DATABASE_URI
    # Enable SQLAlchemy query logging
    SQLALCHEMY_ECHO = True


class ProductionConfig(Config):
    DEBUG = False
    # In production, ensure environment variables are set
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Ensure SSL is used in production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'sslmode': 'require'}
    } if os.environ.get('DATABASE_URL', '').startswith('postgresql') else {}


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'postgresql://postgres:mirka2003@localhost/crm_test'
    WTF_CSRF_ENABLED = False
    # Reduce password hashing rounds for faster tests
    BCRYPT_LOG_ROUNDS = 4
    # Make server responses faster for testing
    SERVER_NAME = 'localhost.localdomain'
    # Disable CSRF in testing
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}