"""
Provide joined table search.
Basic db query will be aggregated here and dispatched to frontend components.
"""
from  typing import Dict, Optional, List
from datetime import timedelta, datetime
from flask import jsonify, request
from . import api
from ..exceptions import ValueExistedError
from ..model_operations import add_by_project_generic_view
from ..model_operations import add_by_spot_record_view
from ..models import User, Location, Project, ProjectDetail
from ..models import  ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord
from .. import db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_


@api.route('/view/project/generic', methods=['GET', 'POST'])
def poject_generic_view():
    """combine project and climate area"""
    response_object = {
        'status': 'success',
        'message': 'project added successfully',
    }
    if request.method == 'POST':  # add new project.
        post_data = request.get_json()

        # send failure responses accroding to the exception captures.
        try:
            add_by_project_generic_view(post_data)
        except ValueExistedError as e:
            response_object["status"] = "failed"
            response_object["message"] = f"project already existed: {e}"
            return jsonify(response_object)
        except IndexError as e:
            response_object["status"] = "failed"
            response_object["message"] = f"Failed to add project: {e}"
            return jsonify(response_object)
        except ValueError as e:
            response_object["status"] = "failed"
            response_object["message"] = f"Unmatched value type: {e}"
            return jsonify(response_object)
        except Exception as e:
            response_object["status"] = "failed"
            response_object["message"] = f"Error: {e}"
            return jsonify(response_object)

        try:  # commit after all transaction are successed.
            db.session.commit()
        except IndexError:
            db.commit.rollback()
        except:
            raise

    else:  # post successful or get. resent the updated reponse.
        projects = [p.to_json() for p in Project.query.all()]
        for proj in projects:
            climate_area = (Location.query
                            .filter_by(location_id=proj["location"]
                                                       ["location_id"])
                            .first()
                            .climate_area.to_json())
            proj.update({"climate_area": climate_area})
        response_object["project_generic_views"] = projects
    return jsonify(response_object)


@api.route('/view/project/generic/<pid>', methods=["PUT", "DELETE"])
def project_generic_view_update_delete(pid):
    pass


@api.route('/view/<pid>/spots', methods=["GET", "POST"])
def spot_generic_view(pid: int):
    """combine Spot, Location, Project, OutdoorSpot"""
    spots: List[Dict] = []
    response_object = {
        'status': 'success',
        'message': 'spot added successfully',
    }
    if request.method == 'POST':  # add new project.
        post_data = request.get_json()

        # send failure responses accroding to the exception captures.
        try:
            add_by_spot_record_view(post_data)
        except ValueExistedError as e:
            response_object["status"] = "failed"
            response_object["message"] = f"spot already existed: {e}"
            return jsonify(response_object)
        except IndexError as e:
            response_object["status"] = "failed"
            response_object["message"] = f"Failed to add spot: {e}"
            return jsonify(response_object)
        except ValueError as e:
            response_object["status"] = "failed"
            response_object["message"] = f"Unmatched value type: {e}"
            return jsonify(response_object)
        except Exception as e:
            response_object["status"] = "failed"
            response_object["message"] = f"Error: {e}"
            return jsonify(response_object)

        try:  # commit after all transaction are successed.
            db.session.commit()
        except IndexError:
            db.commit.rollback()
        except:
            raise
    else:
        for s in Spot.query.filter_by(project_id=pid).all():
            spot = s.to_json()
            proj = Project.query.filter_by(project_id=s.project_id).first()
            od_spot = (OutdoorSpot
                       .query
                       .filter(OutdoorSpot.project.contains(proj))
                       .first()
                       .to_json())

            spot.update({"outdoor_spot": od_spot})
            spots.append(spot)
        response_object["spot_generic_views"] = spots
    return jsonify(response_object)


@api.route('/view/<pid>/spots', methods=["PUT", "DELETE"])
def spot_generic_view_update_delete(pid: int):
    pass


@api.route('/view/spot/<sid>/records')
def spot_record_view(sid: int):
    """combine Spot, Location, Project, Climate area, Outdoor Record"""
    records = []

    for spot_rec in SpotRecord.query.filter_by(spot_id=sid):

        # fetch relevent objects.
        spot = Spot.query.filter_by(spot_id=spot_rec.spot_id).first()
        proj = Project.query.filter_by(project_id=spot.project_id).first()
        od_spot = (OutdoorSpot
                   .query
                   .filter(OutdoorSpot
                           .project
                           .contains(proj))
                   .first())

        # @ TODO: select the outdoor record within the same hour.
        spot_rec_date = spot_rec.spot_record_time
        spot_rec_hour = spot_rec_date.replace(minute=0, second=0, microsecond=0)
        dhour = timedelta(hours=1)

        od_rec = (OutdoorRecord
                  .query
                  .filter(and_(
                      OutdoorRecord
                      .outdoor_record_time >= spot_rec_hour,
                      OutdoorRecord
                      .outdoor_record_time < spot_rec_hour + dhour))
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

    return jsonify(records)


@api.route('/view/project/pic/<pid>', methods=['GET'])
def project_pic_view(pid):
    """send project picture for given project"""
    response_object = {'success': 'success'}

    project_images = ProjectDetail.query.filter_by(project_id=pid).all()
    project_images_json = [p.to_json() for p in project_images]
    response_object['image'] = project_images_json

    return jsonify(response_object)


