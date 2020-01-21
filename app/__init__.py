from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from typing import Optional
import logging

from .caching import Cache, empty_cache

logging.warning('initializing app')

moment = Moment()
db = SQLAlchemy()
app_global_cache: Cache = empty_cache()
app_global_cacher = lambda f: f


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

    with app.app_context():
        from .global_cache import init_global_cache
        global app_global_cache
        global app_global_cacher

        new_cache = init_global_cache()
        if new_cache is not None:
            app_global_cache, app_global_cacher = new_cache

    # register blue_prints
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    return app




