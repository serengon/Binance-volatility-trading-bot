import enum
import os


class Environment(enum.Enum):
    PRODUCTION = "production"
    TESTING = "testing"
    DEVELOPMENT = "development"

    def __init__(self, env):
        self.env = env

    def __str__(self):
        return self.env


def get_env():
    return Environment(os.getenv('FLASK_ENV'))


def set_env(env: Environment):
    os.environ['FLASK_ENV'] = str(env)
