import os

class ProductionConfig:
    # Support both Render-style DATABASE_URL and app-specific SQLALCHEMY_DATABASE_URI.
    _db_url = os.environ.get('SQLALCHEMY_DATABASE_URI') or os.environ.get('DATABASE_URL')
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_DATABASE_URI = _db_url or 'mysql+mysqlconnector://root:812288@localhost/mechanicshop'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    CACHE_TYPE = "SimpleCache"
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ALGORITHM = 'HS256'
    TOKEN_MAX_AGE_SECONDS = 3600

class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:812288@localhost/mechanicshop'
    DEBUG = True
    SECRET_KEY = 'a91519618da3ce2bb09642123963597fde6e7fda9651ec2b171123a94e773337'
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ALGORITHM = 'HS256'
    TOKEN_MAX_AGE_SECONDS = 3600


class TestingConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    SECRET_KEY = 'a91519618da3ce2bb09642123963597fde6e7fda9651ec2b171123a94e773337'
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ALGORITHM = 'HS256'
    TOKEN_MAX_AGE_SECONDS = 3600