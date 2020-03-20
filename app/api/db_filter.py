# given keyword, fuzzy search in the database.
from operator import itemgetter
from typing import NewType, Optional, TypedDict

from flask import json as FlaskJson
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

from timeutils.time import str_to_datetime

from ..api_types import ApiRequest, ApiResponse, ReturnCode, is_ApiRequest
from ..modelOperations import ModelOperations, commit, commit_db_operation
from ..models import (ClimateArea, Company, Data, Device, Location,
                      OutdoorRecord, OutdoorSpot, Permission, Project,
                      ProjectDetail, Spot, SpotRecord, User)
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
    pass


@api.route('/spot/filter', methods=["POST"])
def spot_filtered() -> Json:
    pass

@api.route('/spotRecord/filter/<sid>', methods=["POST"])
def sport_record_filtered(sid: Optional[int]) -> Json:
    post_data = request.get_json()

    if is_ApiRequest(post_data) and sid is not None:
        filter_request = post_data['request']
        start, end = map(str_to_datetime,
                         itemgetter("startTime",
                                    "endTime")
                         (filter_request))

        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.OK.value,
                message=f"filted sport record {sid}"))

        filtered_res = (
            SpotRecord
            .query
            .filter(SpotRecord.device_id == sid)
            .filter(SpotRecord.spot_record_time >= start)
            .filter(SpotRecord.spot_record_time <= end)
        )

        response_object['data'] = {
            'data': [item.to_json() for item in filtered_res if item],
            'totalElementCount': filtered_res.total
        }

    else:
        response_object = (
            ApiResponse(
                status=ReturnCode.BAD_REQUEST.value,
                message="bad request format"))

    return jsonify(response_object)
