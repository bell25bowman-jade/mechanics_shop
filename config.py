import os


def _clean_env(name: str) -> str | None:
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1].strip()
    return value

class ProductionConfig:
    # Support both Render-style DATABASE_URL and app-specific SQLALCHEMY_DATABASE_URI.
    _db_url = _clean_env('SQLALCHEMY_DATABASE_URI') or _clean_env('DATABASE_URL')
    if _db_url and _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    if _db_url and _db_url.startswith('postgresql://') and 'sslmode=' not in _db_url:
        joiner = '&' if '?' in _db_url else '?'
        _db_url = f"{_db_url}{joiner}sslmode=require"

    SQLALCHEMY_DATABASE_URI = _db_url or 'mysql+mysqlconnector://root:812288@localhost/mechanicshop'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    CACHE_TYPE = "SimpleCache"
    SECRET_KEY = _clean_env('SECRET_KEY')
    JWT_SECRET_KEY = _clean_env('JWT_SECRET_KEY') or SECRET_KEY
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