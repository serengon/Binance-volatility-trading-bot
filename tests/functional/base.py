from app import app
from app.utils.environment import Environment


class BaseTestCase:
    def setup_method(self):
        test_app = app.create_app(Environment.TESTING)
        test_app.testing = True
        self.app = test_app.test_client()
