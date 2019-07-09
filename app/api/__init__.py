from flask import Blueprint

api = Blueprint('api', __name__)

from . import errors, outdoor_spot_record, projects, spot_records, users, db_views

