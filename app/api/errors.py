from flask import jsonify
from . import api


@api.errorhandler(404)
def page_not_found(e):
    return 'page not foud', 404


@api.errorhandler(500)
def internal_server_error(e):
    return 'internal server error'

