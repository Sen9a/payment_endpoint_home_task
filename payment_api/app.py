import logging

from flask import Flask
from flask.logging import default_handler

from payment_api import models  # noqa: F401  register models on Base.metadata
from payment_api.api import base as base_api
from payment_api.api import payments as payments_api
from payment_api.database.db import init_db
from payment_api.error_handlers import register_errorhandlers

LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"


def create_app(config_object: str = 'payment_api.settings',
               extra_config: dict = None) -> Flask:
    flask_app = Flask(__name__)
    flask_app.config.from_object(config_object)
    if extra_config:
        flask_app.config.update(extra_config)

    default_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    flask_app.logger.setLevel(flask_app.config['LOG_LEVEL'])
    # the app logger is a child of the package logger; without this each
    # record would be printed by both its own handler and the package handler
    flask_app.logger.propagate = False
    package_logger = logging.getLogger('payment_api')
    package_logger.setLevel(flask_app.config['LOG_LEVEL'])
    if not package_logger.handlers:
        package_logger.addHandler(default_handler)

    init_db(flask_app)
    register_errorhandlers(flask_app)

    flask_app.register_blueprint(base_api.bp)
    flask_app.register_blueprint(payments_api.bp)

    return flask_app
