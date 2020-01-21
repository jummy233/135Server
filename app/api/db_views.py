"""
Provide joined table search.
Basic db query will be aggregated here and dispatched to frontend components.
Idempotent operations.
"""
from typing import Dict, Optional, List, Tuple, Callable
from datetime import timedelta, datetime
from operator import itemgetter
from flask import jsonify, request
from . import api
from ..api_types import ApiRequest, ApiResponse, ReturnCode
from ..api_types import is_ApiRequest
from ..modelOperations import commit_db_operation
from ..modelOperations import commit
from ..models import User, Location, Project, ProjectDetail
from ..models import ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord, Device
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

#############
#  Generic  #
#############


@api.route('/test', methods=['GET'])
def test():
    return jsonify(ApiResponse(status=ReturnCode.OK.value, message="test!"))


# Query all data from the databse. Bad performance.
@api.route('/project/all', methods=['GET'])
def project_view():
    """ project, companies, and climate_area """

    response_object = (
        ApiResponse(status=ReturnCode.OK.value,
                    message='project added successfully'))

    # post successful or get. resend the updated reponse.
    projects = [p.to_json() for p in Project.query.all() if p]
    response_object["data"] = projects

    return jsonify(response_object)


@api.route('/project/<pid>/spots', methods=["GET"])
def spot_view(pid: int):
    """Spot, Location, Project, OutdoorSpot"""

    response_object: ApiResponse = {
        'status': ReturnCode.OK.value,
        'message': 'got spot successfully',
    }

    spots: List[Dict] = [
        s.to_json() for s in
        (Spot
         .query
         .filter_by(project_id=pid)
         .all()) if s]

    response_object["data"] = spots
    return jsonify(response_object)


@api.route('/device/<did>/records', methods=['GET'])
def spot_record_view(did: int):
    """ combine spot record and outdoor records """
    response_object: ApiResponse = (
        ApiResponse(
            status=ReturnCode.OK.value,
            message="successfully get spot records",
            data=[]))

    records = []

    for spot_rec in SpotRecord.query.filter_by(device_id=did):

        # fetch relevent objects.
        od_spot = Device.query.filter_by(device_id=did).first().spot.project.outdoor_spot

        spot_rec_hour: datetime = (
            spot_rec
            .spot_record_time
            .replace(minute=0, second=0, microsecond=0))

        dhour = timedelta(hours=1)

        od_rec = (OutdoorRecord
                  .query
                  .filter(and_(
                      OutdoorRecord.
                      outdoor_record_time >= spot_rec_hour,

                      OutdoorRecord.
                      outdoor_record_time < spot_rec_hour + dhour))
                  .first())

        spot_rec_json = spot_rec.to_json()
        od_spot_json = od_spot.to_json() if od_spot else None

        try:
            od_rec_json = od_rec.to_json()
        except AttributeError:
            od_rec_json = {}

        spot_rec_json.update({
            "outdoor_spot": od_spot_json,
            "outdoor_record": od_rec_json,
        })

        records.append(spot_rec_json)

        response_object['data'] = records
    return jsonify(response_object)


@api.route('/project_pic/<pid>', methods=['GET'])
def project_pic_view(pid):
    """send project picture for given project"""
    response_object: ApiResponse = (
        ApiResponse(status=ReturnCode.OK.value,
                    message="project pictures are sent successfully"))

    project_images = ProjectDetail.query.filter_by(project_id=pid).all()
    project_images_json = [p.to_json() for p in project_images if p]
    response_object['data'] = project_images_json

    return jsonify(response_object)


