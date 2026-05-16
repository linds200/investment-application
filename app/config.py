import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')
    CONFIG_REGION = os.environ.get('COGNITO_REGION')
    CONFIG_POOL_ID = os.environ.get('COGNITO_POOL_ID')
    CONFIG_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
    CONFIG_DOMAIN = os.environ.get('COGNITO_DOMAIN')

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite+pysqlite:///:memory:'
    SQLALCHEMY_ECHO = False
    ALPHAVANTAGE_API_KEY = os.environ.get('ALPHAVANTAGE_API_KEY')


class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'mysql+pymysql://{os.environ.get("DB_USER", "")}:'
        f'{os.environ.get("DB_PASSWORD", "")}@'
        f'{os.environ.get("DB_HOST", "")}:'
        f'{os.environ.get("DB_PORT", "3306")}/'
        f'{os.environ.get("DB_NAME", "")}'
    )
    DEBUG = True
    SQLALCHEMY_ECHO = True
    CONFIG_REGION = os.environ.get('COGNITO_REGION')
    CONFIG_USER_POOL_ID = os.environ.get('COGNITO_POOL_ID')
    CONFIG_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
    CONFIG_DOMAIN = os.environ.get('COGNITO_DOMAIN')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f'mysql+pymysql://{os.environ.get("DB_USER", "")}:'
        f'{os.environ.get("DB_PASSWORD", "")}@'
        f'{os.environ.get("DB_HOST", "")}:'
        f'{os.environ.get("DB_PORT", "3306")}/'
        f'{os.environ.get("DB_NAME", "")}'
    )
    DEBUG = False
    SQLALCHEMY_ECHO = False
    CONFIG_REGION = os.environ.get('COGNITO_REGION')
    CONFIG_USER_POOL_ID = os.environ.get('COGNITO_POOL_ID')
    CONFIG_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
    CONFIG_DOMAIN = os.environ.get('COGNITO_DOMAIN')


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
}


def get_config(env: str):
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)
