from flask import Blueprint

api = Blueprint('api', __name__)

from . import db_views, db_paged, db_changed, errors, login, spot_records, users

