# given keyword, fuzzy search in the database.
from operator import itemgetter
from typing import NewType, Optional, TypedDict

from flask import jsonify, request

from app.api_types import ApiRequest
from app.api_types import ApiResponse
from app.api_types import ReturnCode
from app.api_types import is_ApiRequest
from app.modelOperations import ModelOperations
from app.modelOperations import commit
from app.modelOperations import commit_db_operation
from app.models import ClimateArea
from app.models import Company
from app.models import Data
from app.models import Device
from app.models import Location
from app.models import OutdoorRecord
from app.models import OutdoorSpot
from app.models import Permission
from app.models import Project
from app.models import ProjectDetail
from app.models import Spot
from app.models import SpotRecord
from app.models import User
from timeutils.time import str_to_datetime

from . import api

Json = NewType('Json', str)


class FilterParams(TypedDict):
    startTime: str
    endTime: str
    keyword: str


@api.route('/project/filter', methods=["POST"])
def project_filtered() -> Json:
    pass


@api.route('/device/filter', methods=["POST"])
def device_filtered() -> Json:
    post_data = request.get_json()

    if is_ApiRequest(post_data):
        filter_request = post_data['request']
        start, end = map(
            str_to_datetime,
            itemgetter("startTime",
                       "endTime",
                       "keyword",)
            (filter_request))

        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.OK.value,
                message="filted device"))

        filtered_res = (
            SpotRecord
            .query
            .filter(Device.create_time >= start)
            .filter(Device.modify_time <= end)
            .filter(Device.device_name == "keyword"))

        response_object['data'] = {
            'data': [item.to_json() for item in filtered_res if item],
            'totalElementCount': filtered_res.count(),
        }

    else:
        response_object = (
            ApiResponse(
                status=ReturnCode.BAD_REQUEST.value,
                message="bad request format"))
    return jsonify(response_object)


@api.route('/spot/filter', methods=["POST"])
def spot_filtered() -> Json:
    pass


@api.route('/spotRecord/filter/<int:did>', methods=["POST"])
def sport_record_filtered(did: Optional[int]) -> Json:
    post_data = request.get_json()

    if is_ApiRequest(post_data) and did is not None:
        filter_request = post_data['request']
        start, end = map(
            str_to_datetime,
            itemgetter("startTime",
                       "endTime")
            (filter_request))

        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.OK.value,
                message=f"filted sport record {did}"))

        filtered_res = (
            SpotRecord
            .query
            .filter(SpotRecord.device_id == did)
            .filter(SpotRecord.spot_record_time >= start)
            .filter(SpotRecord.spot_record_time <= end))

        response_object['data'] = {
            'data': [item.to_json() for item in filtered_res if item],
            'totalElementCount': filtered_res.count(),
        }

    else:
        response_object = (
            ApiResponse(
                status=ReturnCode.BAD_REQUEST.value,
                message="bad request format"))
    return jsonify(response_object)
