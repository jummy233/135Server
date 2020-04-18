"""
All apis here will modify the state of database.
"""

from typing import Dict, Optional, List, Tuple, NewType, Callable, Any, cast
from flask import jsonify, request
from flask import json as FlaskJson
from sqlalchemy.exc import IntegrityError
from . import api
from app.api.api_types import ApiResponse, ReturnCode, ApiRequest
from app.api.api_types import is_ApiRequest
from app.modelOperations import ModelOperations
from app.modelOperations import commit_db_operation
from app.modelOperations import commit
from app.models import User, Location, Project, ProjectDetail
from app.models import ClimateArea, Company
from app.models import OutdoorSpot, OutdoorRecord
from app.models import Spot, SpotRecord, Device
from app.models import Data

Json = NewType('Json', str)
AddOperation = Callable[[Dict], Optional[Data]]
UpdateOperation = Callable[[Dict], Optional[Data]]
DeleteOperation = Callable[[int], Optional[Data]]


def add_update_delete_template(
        some_id: Optional[int],
        model_operations: Tuple[AddOperation,
                                UpdateOperation,
                                DeleteOperation]) -> Json:
    add, update, delete = model_operations

    def handle_post(post_data: Optional[ApiRequest]) -> ApiResponse:

        response_object: ApiResponse = (
            ApiResponse(status=ReturnCode.OK.value))

        if post_data is None or not is_ApiRequest(cast(Optional[Dict], post_data)):
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object['message'] = "post failed "
            return response_object

        try:
            posted = add(cast(Dict, post_data["request"]))
            if posted:
                commit()
                response_object["message"] = "post succeeded!"
                response_object["data"] = posted.to_json()
            else:
                response_object['status'] = ReturnCode.NO_DATA.value
                response_object['message'] = "post failed"

        except IntegrityError:
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object["message"] = (
                "post failed!, integrity error. might be missing a field")
        except Exception as e:
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object["message"] = f"post failed! {e}"

        finally:
            return response_object

    def handle_put(post_data: Optional[ApiRequest]) -> ApiResponse:

        response_object: ApiResponse = (
            ApiResponse(status=ReturnCode.OK.value))

        if post_data is None or not is_ApiRequest(cast(Optional[Dict], post_data)):
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object['message'] = "post failed "
            return response_object

        try:
            updated = update(cast(Dict, post_data["request"]))
            if updated:
                commit()
                response_object['message'] = "update succeeded!"
                response_object["data"] = updated.to_json()
            else:
                response_object['status'] = ReturnCode.NO_DATA.value
                response_object['message'] = "update failed"

        except IntegrityError:
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object["message"] = (
                "update failed!, integrity error. might be missing a field")

        except Exception as e:
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object['message'] = f"update failed {e}"

        finally:
            return response_object

    def handle_delete() -> ApiResponse:
        response_object: ApiResponse = (
            ApiResponse(status=ReturnCode.OK.value))

        try:
            if some_id is None:
                raise Exception("Error when deleting, id is None")
            delete(some_id)
            commit()
            response_object["message"] = "remvoe succeeded"
        except Exception as e:
            response_object["status"] = ReturnCode.BAD_REQUEST.value
            response_object["message"] = f"failed to remove: {e}"
        finally:
            return response_object

    response_object: ApiResponse = ApiResponse()
    if request.method == 'POST':  # add new project.
        response_object = handle_post(post_data=request.get_json())

    if request.method == 'PUT':
        response_object = handle_put(post_data=request.get_json())

    if request.method == 'DELETE':
        response_object = handle_delete()

    return jsonify(response_object)


@api.route('/project/', methods=["POST"])
@api.route('/project/<pid>', methods=["PUT", "DELETE"])
def project_add_update_delete(pid: Optional[int] = None):
    return add_update_delete_template(
        pid, (ModelOperations.Add.add_project,
              ModelOperations.Update.update_project,
              ModelOperations.Delete.delete_project))


@api.route('/spot/', methods=["POST"])
@api.route('/spot/<sid>', methods=["PUT", "DELETE"])
def spot_add_update_delete(sid: Optional[int] = None):
    return add_update_delete_template(
        sid, (ModelOperations.Add.add_spot,
              ModelOperations.Update.update_spot,
              ModelOperations.Delete.delete_spot))


@api.route('/device/', methods=["POST"])
@api.route('/device/<did>', methods=["PUT", "DELETE"])
def device_add_update_delete(did: Optional[int] = None):
    return add_update_delete_template(
        did, (ModelOperations.Add.add_device,
              ModelOperations.Update.update_device,
              ModelOperations.Delete.delete_device))


@api.route('/spotRecord/', methods=["POST"])
@api.route('/spotRecord/<rid>', methods=["PUT", "DELETE"])
def spot_record_add_update_delete(rid: Optional[int] = None):
    return add_update_delete_template(
        rid, (ModelOperations.Add.add_spot_record,
              ModelOperations.Update.update_spot_record,
              ModelOperations.Delete.delete_spot_record))


@api.route('/outdoorSpot/', methods=["POST"])
@api.route('/outdoorSpot/<oid>', methods=["PUT", "DELETE"])
def outdoor_spot_add_update_delete(oid: Optional[int] = None):
    return add_update_delete_template(
        oid, (ModelOperations.Add.add_outdoor_spot,
              ModelOperations.Update.update_outdoor_spot,
              ModelOperations.Delete.delete_outdoor_spot))



