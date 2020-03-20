"""
Paged apis
Only for query
all operations are idempotent.
"""
from typing import Dict, Optional, List, Tuple, Callable
from datetime import timedelta, datetime
from operator import itemgetter
from flask import jsonify, request
from sqlalchemy import desc
from . import api
from ..api_types import ApiResponse, ReturnCode
from ..api_types import is_ApiRequest
from ..api_types import PagingRequest
from ..models import User, Location, Project, ProjectDetail
from ..models import ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord, Device


@api.route('/project', methods=['POST'])
def project_paged():
    """ Return a specific page of data"""
    post_data = request.get_json()
    if is_ApiRequest(post_data):
        paging_request: PagingRequest = post_data['request']
        size, pageNo = itemgetter('size', 'pageNo')(paging_request)

        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.OK.value,
                message=f"get project page {pageNo}"))

        projects_page = Project.query.paginate(pageNo, size)
        response_object['data'] = {
            'data': [item.to_json() for item in projects_page.items if item],
            'totalElementCount': projects_page.total,
            'currentPage': pageNo,
            'pageSize': size
        }

    else:
        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.BAD_REQUEST.value,
                message="bad request format"))

    return jsonify(response_object)


@api.route('/project/<pid>/spot', methods=['POST'])
@api.route('/spot', methods=['POST'])
def spot_paged(pid: Optional[int] = None):
    """
    Either return paged spot data or paged spot data under
    a given project.
    """
    post_data = request.get_json()
    if is_ApiRequest(post_data):
        paging_request: PagingRequest = post_data['request']
        size, pageNo = itemgetter('size', 'pageNo')(paging_request)

        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.OK.value,
                message=f"get spot page {pageNo}"))

        if pid is None:
            spots_page = Spot.query.paginate(pageNo, size)
        else:
            spots_page = (
                Spot
                .query
                .filter_by(project_id=pid).paginate(pageNo, size))

        response_object['data'] = {
            'data': [item.to_json() for item in spots_page.items if item],
            'totalElementCount': spots_page.total,
            'currentPage': pageNo,
            'pageSize': size
        }

    else:
        response_object = (
            ApiResponse(
                status=ReturnCode.BAD_REQUEST.value,
                message="bad request format"))

    return jsonify(response_object)


@api.route('/spot/<sid>/device', methods=['POST'])
@api.route('/device', methods=['POST'])
def device_paged(sid: Optional[int] = None):
    """ Return a specific page of data"""
    post_data = request.get_json()

    if is_ApiRequest(post_data):
        paging_request: PagingRequest = post_data['request']
        size, pageNo = itemgetter('size', 'pageNo')(paging_request)

        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.OK.value,
                message=f"get device page {pageNo}"))

        if sid is None:
            devices_page = Device.query.paginate(pageNo, size)
        else:
            devices_page = Device.query.filter_by(
                spot_id=sid).paginate(pageNo, size)

        response_object['data'] = {
            'data': [item.to_json() for item in devices_page.items if item],
            'totalElementCount': devices_page.total,
            'currentPage': pageNo,
            'pageSize': size
        }

    else:
        response_object = (
            ApiResponse(
                status=ReturnCode.BAD_REQUEST.value,
                message="bad request format"))
    return jsonify(response_object)


@api.route('/device/<did>/spot_record', methods=['POST'])
def spot_record_paged(did: int):
    """ Return a specific page of data"""
    post_data = request.get_json()
    if is_ApiRequest(post_data):
        paging_request: PagingRequest = post_data['request']
        size, pageNo = itemgetter('size', 'pageNo')(paging_request)

        response_object: ApiResponse = (
            ApiResponse(
                status=ReturnCode.OK.value,
                message=f"get spot_record page {pageNo}"))

        # never send all records
        if pageNo * size > SpotRecord.query.filter_by(device_id=did).count():
            response_object['status'] = ReturnCode.NO_DATA.value
            response_object['message'] = f"query out of range for device {did}"
        else:
            spot_records_page = (
                SpotRecord.query
                .filter_by(
                    device_id=did)
                .order_by(desc(SpotRecord.spot_record_time))
                .paginate(pageNo, size)
            )

            response_object['data'] = {
                'data': [
                    item.to_json()
                    for item in spot_records_page.items if item],
                'totalElementCount': spot_records_page.total,
                'currentPage': pageNo,
                'pageSize': size
            }

    else:
        response_object = (
            ApiResponse(
                status=ReturnCode.BAD_REQUEST.value,
                message="bad request format"))

    return jsonify(response_object)


# might be useful later.
# append outdoor records
# TODO 2020-01-09
# od_spot = Device.query.filter_by(device_id=did).first().spot.project.outdoor_spot

# spot_rec_hour: datetime = (
#     spot_rec
#     .spot_record_time
#     .replace(minute=0, second=0, microsecond=0))

# dhour = timedelta(hours=1)

# od_rec = (OutdoorRecord
#           .query
#           .filter(and_(
#               OutdoorRecord.
#               outdoor_record_time >= spot_rec_hour,

#               OutdoorRecord.
#               outdoor_record_time < spot_rec_hour + dhour))
#           .first())

# spot_rec_json = spot_rec.to_json()
# od_spot_json = od_spot.to_json()
