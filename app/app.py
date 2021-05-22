import logging as log
from concurrent.futures import ThreadPoolExecutor

from flask import Flask

from app.controllers.binance import bp_binance_detect_mooning_management
from app.jobs.binance_detect_mooning import run as run_binance_detect_mooning
from app.utils.environment import Environment
from config import app_config

executor = ThreadPoolExecutor(2)


def create_app(env: Environment):
    log.basicConfig(level=log.INFO)
    app = Flask(__name__)
    app.config.from_object(app_config[env])

    app.url_map.strict_slashes = False
    active_endpoints = (
        ("/", bp_binance_detect_mooning_management),
    )

    for url, blueprint in active_endpoints:
        app.register_blueprint(blueprint, url_prefix=url)

    if env == Environment.PRODUCTION:
        #run_jobs()
        pass

    return app


def run_jobs():
    executor.submit(run_binance_detect_mooning)
    return 'Task executor job was launched in background!'


app = create_app(Environment.PRODUCTION)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
