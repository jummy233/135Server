"""
Dependency:

There are two major data source: Xiaomi and Jianyanyuan server,
each one has its own APIs.

Low level modules provides the basic abtractions for raw resources. Including
the basic request handling, ORM mapping and operation on top of orm.
There is also a LRU cache module to speed up update.

Mid level maintain the periocial update operation. The main entrance is
Scheduler which is a daemon thread schedule all the update operations.
There will be a overall update for the entire database everyday. and
for online device there will be a update every 5 minutes.
Update operations are done by separate actors and are all non blocking.
- Note that DataGen module maintain the connection to server and provides
  iterators of database compatible data, which can be threaded by Actors.
- There is also a force update option which cause a instance overall update.

Restful level provides resftul apis for frontend. It talks directly with
Low level modules. Apis provides paged get, update, delete, filtering, and
login functionalites. How to handle this apis is up to the frontend.

>= Resources =================================================================
>               Server                 Sqlite3
>                 .                      .
>= Low level =====+======================+====================================
>                 .                      .
>                 .              App ----.-------------------+
>                 .               |      .                   |
>                 .     +---------+      .                   |
>                 .     |         |      .                   |
> (http request) api    |       Models---+                   |
>                 |     |        (orm)                       |
>                 |     |         |                          |
>                 |     |     ModelOperations------------ | Cache |
>                 |     |   (higher level orm operations)
>                 |     |         |
>= Mid level =====+=====+=========+============================================
>                 |     |         |
>                 |     |         +--<------- db_init (threaded init)
>                 |     |         |
>                 |     |     +---+--<------+
>                 |     |     |             |
>              DataGen--|     |             |
>           (connection)      |             |
>                 |           |             |
>                 |           |             |
>               Actor         |             |
>                 |           |             |
>             FetchActor      |             |
>                 |           |             |
>            UpdateActor--- Scheduler       |
>     (Realtime, Allupdate, all threaded)   |
>                                           |
>= RESTFUL =================================+==================================
>                                           |
>                                     app.apis (restful)
>                                 +---------+----------+
>                                 |         |          |
>                                view     modify     filter
>                                 |         |          |
>                                 +---------+----------+
>                                           .
>                                           .
>                                       Fronent  (frontend has its own api.)
"""

from flask import Flask
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from .caching import CacheInstance
from .dataGetter import UpdateScheduler
from logger import make_logger
from logging import DEBUG
logger = make_logger('app', 'app_log', DEBUG)

logger.warning('initializing app')

global_cache = CacheInstance()  # create cache instance here.
moment = Moment()
db = SQLAlchemy()
scheduler = UpdateScheduler()


login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name: str, with_scheduler: bool = True) -> Flask:
    """ application factory function."""
    app = Flask(__name__)

    # load config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    if with_scheduler:
        scheduler.init_app(app)
        scheduler.start()

    if app.config['SHISANWU_CACHE_ON']:
        global_cache.init_app(app)  # cache database.

    # register blue_prints
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    logger.info('created new flask app')

    return app


logger.info('app module loaded')
