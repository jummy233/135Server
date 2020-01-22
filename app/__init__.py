from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from typing import Optional
from .caching import CacheInstance
import logging

logging.basicConfig(level=logging.DEBUG, filename='./log')

logging.warning('initializing app')

global_cache = CacheInstance()  # create cache instance here.
moment = Moment()
db = SQLAlchemy()


login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name) -> Flask:
    # application factory function.

    app = Flask(__name__)
    app.config.from_object(config[config_name])  # create app with specific configuration.
    config[config_name].init_app(app)

    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    global_cache.init_app(app)  # cache database.

    # register blue_prints
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    logging.info('created new flask app')
    return app


logging.info('app module loaded')

