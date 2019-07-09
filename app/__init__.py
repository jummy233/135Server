from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

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

    # register blue_prints
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    return app

