from flask import jsonify

from app.api_types import ApiResponse, ReturnCode
from . import api


@api.route('/logout', methods=["GET"])
def logout():
    response = ApiResponse(
        status=ReturnCode.OK.value,
        message="logout")
    return jsonify(response)
