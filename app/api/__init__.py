from flask import Blueprint

api = Blueprint('api', __name__)

from . import db_views, db_paged, db_changed, db_filter
from . import logout, db_realtime
from . import errors, login, spot_records, users
