"""
All apis here will modify the state of database.
"""

from typing import Dict, Optional, List, Tuple, Callable
from datetime import timedelta, datetime
from operator import itemgetter
from flask import jsonify, request
from . import api
from ..api_types import ApiResponse, ReturnCode, ApiRequest
from ..api_types import is_ApiRequest
from ..exceptions import ValueExistedError
from ..modelOperations import add_project
from ..modelOperations import add_spot
from ..modelOperations import commit_db_operation
from ..modelOperations import delete_project
from ..modelOperations import delete_spot
from ..modelOperations import commit
from ..models import User, Location, Project, ProjectDetail
from ..models import  ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord, Device
from .. import db
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

# TODO handle put. 2020-01-13
@api.route('/project/<pid>', methods=["POST", "PUT", "DELETE"])
def project_view_add_update_delete(pid: int):
    response_object: ApiResponse = (
        ApiResponse(status=ReturnCode.OK.value))

    def handle_post(response_object: ApiResponse):
        post_data = request.get_json()
        if is_ApiRequest(post_data):
            post_data = post_data['request']

        response_object = commit_db_operation(
            response_object=response_object,
            op=add_project,
            post_data=post_data,
            name='project')
        return jsonify(response_object)

    def handle_put(response_object: ApiResponse):
        pass

    def handle_delete(response_object: ApiResponse) -> None:
        response_object["message"] = "project is removed!"
        try:
            delete_project(pid)
            commit()
        except Exception as e:
            response_object["status"] = ReturnCode.BAD_REQUEST.value
            response_object["message"] = f"failed to remove project: {e}"

    if request.method == 'POST':  # add new project.
        handle_post(response_object)

    if request.method == 'PUT':
        handle_put(response_object)

    if request.method == 'DELETE':
        handle_delete(response_object)

    return jsonify(response_object)


@api.route('/project/<pid>/spots/<sid>', methods=["POST", "PUT", "DELETE"])
def spot_generic_view_add_update_delete(pid: int, sid: int):
    response_object: ApiResponse = (
        ApiResponse(status=ReturnCode.OK.value))

    def handle_post(response_object: ApiResponse):
        post_data: ApiRequest = request.get_json()

        # send failure responses accroding to the exception captures.
        response_object = commit_db_operation(
            response_object=response_object,
            op=add_spot,
            post_data=post_data,
            name='spot')
        return jsonify(response_object)

    def handle_put(response_object: ApiResponse):
        pass

    def handle_delete(response_object: ApiResponse):
        response_object["message"] = "spot is removed!"
        try:
            delete_spot(sid)
            commit()
        except Exception as e:
            response_object["status"] = ReturnCode.BAD_REQUEST.value
            response_object["message"] = f"spot remove failed: {e}"

    if request.method == 'POST':
        handle_post(response_object)

    if request.method == 'PUT':
        pass

    if request.method == 'DELETE':
        handle_delete(response_object)

    return jsonify(response_object)


