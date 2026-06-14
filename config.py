
class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:812288@localhost/mechanicshop'
    DEBUG = True
    SECRET_KEY = 'a91519618da3ce2bb09642123963597fde6e7fda9651ec2b171123a94e773337'
    TOKEN_MAX_AGE_SECONDS = 3600
