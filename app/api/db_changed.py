"""
All apis here will modify the state of database.
"""

from typing import Dict, Optional, List, Tuple, NewType, Callable, Any
from flask import jsonify, request
from flask import json as FlaskJson
from . import api
from ..api_types import ApiResponse, ReturnCode, ApiRequest
from ..api_types import is_ApiRequest
from ..modelOperations import ModelOperations
from ..modelOperations import commit_db_operation
from ..modelOperations import commit
from ..models import User, Location, Project, ProjectDetail
from ..models import ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord, Device
from ..models import Data


Json = NewType('Json', str)
AddOperation = Callable[[Dict], Optional[Data]]
UpdateOperation = Callable[[Dict], Optional[Data]]
DeleteOperation = Callable[[int], Optional[Data]]


def add_update_delete_template(
        some_id: int,
        model_operations: Tuple[AddOperation,
                                UpdateOperation,
                                DeleteOperation]) -> Json:
    add, update, delete = model_operations

    response_object: ApiResponse = (
        ApiResponse(status=ReturnCode.OK.value))

    def handle_post(response_object: ApiResponse) -> None:
        post_data = request.get_json()
        if is_ApiRequest(post_data):
            post_data = post_data['request']

        response_object = commit_db_operation(
            response_object=response_object,
            op=add,
            post_data=post_data,
            name='project')

    def handle_put(response_object: ApiResponse) -> None:
        post_data = request.get_json()
        if is_ApiRequest(post_data):
            post_data = post_data['request']

        updated = update(post_data)
        if updated:
            response_object['message'] = "project update succeeded!"
        else:
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object['message'] = "project update failed"

    def handle_delete(response_object: ApiResponse) -> None:
        response_object["message"] = "project is removed!"
        try:
            delete(some_id)
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


@api.route('/project/<pid>', methods=["POST", "PUT", "DELETE"])
def project_add_update_delete(pid: int):
    return add_update_delete_template(
        pid, (ModelOperations.Add.add_project,
              ModelOperations.Update.update_project,
              ModelOperations.Delete.delete_project))


@api.route('/spots/<sid>', methods=["POST", "PUT", "DELETE"])
def spot_add_update_delete(sid: int):
    return add_update_delete_template(
        sid, (ModelOperations.Add.add_spot,
              ModelOperations.Update.update_spot,
              ModelOperations.Delete.delete_spot))


@api.route('/device/<did>', methods=["POST", "PUT", "DELETE"])
def device_add_update_delete(did: int):
    return add_update_delete_template(
        did, (ModelOperations.Add.add_device,
              ModelOperations.Update.update_device,
              ModelOperations.Delete.delete_device))


@api.route('/spotRecord/<rid>', methods=["POST", "PUT", "DELETE"])
def spot_record_add_update_delete(rid: int):
    return add_update_delete_template(
        rid, (ModelOperations.Add.add_spot_record,
              ModelOperations.Update.update_spot_record,
              ModelOperations.Delete.delete_spot_record))


@api.route('/outdoorSpot/oid', methods=["POST", "PUT", "DELETE"])
def outdoor_spot_add_update_delete(oid: int):
    return add_update_delete_template(
        oid, (ModelOperations.Add.add_outdoor_spot,
              ModelOperations.Update.update_outdoor_spot,
              ModelOperations.Delete.delete_outdoor_spot))


