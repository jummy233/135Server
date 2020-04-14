from flask import jsonify
from . import api
from ..models import User

from flask import json as FlaskJson
from flask import jsonify, request
from ..api_types import ApiRequest, ApiResponse, ReturnCode, is_ApiRequest

import json
from typing import NewType, Optional, TypedDict

Json = NewType('Json', str)


@api.route('/login', methods=["POST"])
def login() -> Json:
    """
    request:
        name: str,
        pwhash: str
    """
    post_data = request.get_json()
    response: ApiResponse = {}

    print(post_data)
    if is_ApiRequest(post_data):
        stored = {}
        login_req = post_data.get('request')
        name: str = login_req.get("name")
        pwhash: str = login_req.get("pwhash")

        with open('dataGetter/static/pw.json', 'r') as f:
            stored = json.loads(f.read())

            print("---")
            print(stored)

        if name == stored['name'] and pwhash == stored['pwhash']:
            response = ApiResponse(
                status=ReturnCode.OK.value,
                message="logined")
            return jsonify(response)

        response = ApiResponse(
            status=ReturnCode.BAD_REQUEST.value,
            message="login failed. invalid name or password.")
        return jsonify(response)

    response = ApiResponse(
        status=ReturnCode.BAD_REQUEST.value,
        message="bad request format")
    return jsonify(response)
