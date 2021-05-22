import os

from app.utils.environment import Environment


class Config:
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    # DB_HOST = 'localhost'
    # DB_NAME = 'test'
    # DB_USER = 'root'
    # DB_PASS = 'root'
    # BACKUP_PATH = '/var/backup/ehome/'
    # UPLOAD_PATH = '/srv/http/ehome/app/frontend/planos'
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SECRET_KEY = ""


class ProductionConfig(Config):
    LOG_LEVEL = 'INFO'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DB_MYSQL_MALEALERTS00_MALECONF_MALECONF_ENDPOINT')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    CACHE_TYPE = 'simple'


class TestingConfig(DevelopmentConfig):
    TESTING = True
    JSONIFY_PRETTYPRINT_REGULAR = False


app_config = {
    Environment.PRODUCTION: ProductionConfig,
    Environment.DEVELOPMENT: DevelopmentConfig,
    Environment.TESTING: TestingConfig
}
