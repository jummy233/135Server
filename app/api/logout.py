from flask import jsonify
from . import api
from ..models import User


@api.route('/logout')
def logout():
    return "logout"
