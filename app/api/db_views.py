"""
Provide joined table search.
Basic db query will be aggregated here and dispatched to frontend components.
"""
from typing import Dict, Optional, List, Tuple, Callable
from datetime import timedelta, datetime
from flask import jsonify, request
from . import api
from .api_types import ApiRequest, ApiResponse, ReturnCode
from ..exceptions import ValueExistedError
from ..modelOperations import commit_db_operation
from ..modelOperations import add_project
from ..modelOperations import add_spot
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

#############
#  Generic  #
#############

# Query all data from the databse. Bad performance.
@api.route('/api/v1/project/all', methods=['GET', 'POST'])
def project_view():
    """ project, companies, and climate_area """

    response_object = (
        ApiResponse(status=ReturnCode.OK.value,
                    message='project added successfully'))

    if request.method == 'POST':  # add new project.
        post_data: ApiRequest = request.get_json()
        post_data = post_data['request']

        response_object = commit_db_operation(
            response_object=response_object,
            op=add_project,
            post_data=post_data,
            name='project')
        return jsonify(response_object)

    else:  # post successful or get. resend the updated reponse.
        projects = [p.to_json() for p in Project.query.all()]
        response_object["data"] = projects
    return jsonify(response_object)


@api.route('/api/v1/project/<pid>/spots', methods=["GET", "POST"])
def spot_view(pid: int):
    """Spot, Location, Project, OutdoorSpot"""

    response_object: ApiResponse = {
        'status': ReturnCode.OK.value,
        'message': 'spot added successfully',
    }
    if request.method == 'POST':  # add new project.
        post_data: ApiRequest = request.get_json()

        # send failure responses accroding to the exception captures.
        response_object = commit_db_operation(
            response_object=response_object,
            op=add_spot,
            post_data=post_data,
            name='spot')
        return jsonify(response_object)

    else:
        spots: List[Dict] = [
            s.to_json for s in
            (Spot
             .query
             .filter_by(project_id=pid)
             .all())]

        response_object["data"] = spots
    return jsonify(response_object)


@api.route('/api/v1/spot/<sid>/device/<did>/records', methods=['GET'])
def spot_record_view(sid: int, did: int):
    """ combine spot record and outdoor records """
    response_object: ApiResponse = (
        ApiResponse(
            status=ReturnCode.OK.value,
            message="successfully get spot records",
            data=[]))

    records = []

    for spot_rec in SpotRecord.query.filter_by(spot_id=sid):

        # fetch relevent objects.
        if spot_rec is not None:
            device = Device.query.filter_by(device_id=spot_rec.device_id).first()

        if device is not None:
            spot = Spot.query.filter_by(spot_id=device.spot_id).first()

        # use project to fetch outdoor spot.
        if spot is not None:
            proj = Project.query.filter_by(project_id=spot.project_id).first()

        od_spot = (OutdoorSpot
                   .query
                   .filter(OutdoorSpot
                           .project
                           .contains(proj))
                   .first())

        # @ TODO: select the outdoor record within the same hour.
        spot_rec_hour = (
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
        od_spot_json = od_spot.to_json()

        try:
            od_rec_json = od_rec.to_json()
        except AttributeError:
            od_rec_json = {}

        spot_rec_json.update({
            "spot_id": spot.spot_id,
            "outdoor_spot": od_spot_json,
            "outdoor_record": od_rec_json,
        })

        records.append(spot_rec_json)

        response_object['data'] = records
    return jsonify(response_object)


@api.route('/api/view/project_pic/<pid>', methods=['GET'])
def project_pic_view(pid):
    """send project picture for given project"""
    response_object = {'success': 'success'}

    project_images = ProjectDetail.query.filter_by(project_id=pid).all()
    project_images_json = [p.to_json() for p in project_images]
    response_object['image'] = project_images_json

    return jsonify(response_object)


@api.route('/api/v1/project/<pid>', methods=["PUT", "DELETE"])
def project_view_update_delete(pid: int):
    response_object = {'status': 'success'}
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        response_object["message"] = "project removed!"
        try:
            delete_project(pid)
            commit()
        except Exception as e:
            response_object["status"] = "failed"
            response_object["message"] = f"project remove failed: {e}"

    return jsonify(response_object)


@api.route('/api/view/<pid>/spots/<sid>', methods=["PUT", "DELETE"])
def spot_generic_view_update_delete(pid: int, sid: int):
    response_object = {'status': 'success'}
    if request.method == 'PUT':
        pass
    if request.method == 'DELETE':
        response_object["message"] = "spot removed!"
        try:
            delete_spot(sid)
            commit()
        except Exception as e:
            response_object["status"] = "failed"
            response_object["message"] = f"spot remove failed: {e}"

    return jsonify(response_object)


#######################
#      Paged          #
#######################

@api.route('/api/v1/project', methods=['POST'])
def project_paged(sid: int, pagelen: int):
    """ Return a specific page of data"""

    # return desired range of record ids
    def paging_idx(sid: int, pagelen: int) -> Tuple[int, int]:
        pass


# TODO 2019-12-12 add paging request instead of sending all data at once.
@api.route('/api/v1/spot', methods=['POST'])
def spot_paged(sid: int, pagelen: int):
    """ Return a specific page of data"""

    # return desired range of record ids
    def paging_idx(sid: int, pagelen: int) -> Tuple[int, int]:
        pass

# TODO 2019-12-12 add paging request instead of sending all data at once.
@api.route('/api/v1/spot_record', methods=['POST'])
def spot_record_paged(sid: int, pagelen: int):
    """ Return a specific page of data"""

    # return desired range of record ids
    def paging_idx(sid: int, pagelen: int) -> Tuple[int, int]:
        pass


