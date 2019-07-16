"""
Provide joined table search.
Basic db query will be aggregated here and dispatched to frontend components.
"""
from flask import jsonify, request
from . import api
from ..models import User, Location, Project, ProjectDetail
from ..models import  ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from .. import db
from datetime import timedelta


@api.route('/view/project/generic', methods=['GET'])
def poject_generic_view():
    """combine project and climate area"""
    projects = [p.to_json() for p in Project.query.all()]

    for proj in projects:
        climate_area = Location.query.                                         \
            filter_by(location_id=proj["location"]["location_id"]).            \
            first().climate_area.to_json()
        proj.update({"climate_area": climate_area})
    return jsonify(projects)


@api.route('/view/project/detailed/<pid>', methods=['GET'])
def poject_detailed_view(pid):
    """send project picture for given project"""
    response_object = {'success': 'success'}

    project_images = ProjectDetail.query.filter_by(project_id=pid).all()
    project_images_json = [p.to_json() for p in project_images]
    response_object['image'] = project_images_json

    return jsonify(response_object)


@api.route('/view/<pid>/spots')
def spot_generic_view(pid: int):
    """combine Spot, Location, Project, OutdoorSpot"""
    spots = []

    for s in Spot.query.filter_by(project_id=pid).all():
        spot = s.to_json()
        proj = Project.query.filter_by(project_id=s.project_id).first()
        od_spot = OutdoorSpot.query                                            \
            .filter(OutdoorSpot.project.contains(proj)).first().to_json()

        spot.update({"outdoor_spot": od_spot})
        spots.append(spot)

    return jsonify(spots)


@api.route('/view/spot/<sid>/records')
def spot_detailed_view(sid: int):
    """combine Spot, Location, Project, Climate area, Outdoor Record"""
    records = []

    for spot_rec in SpotRecord.query.filter_by(spot_id=sid):

        # fetch relevent objects.
        spot = Spot.query.filter_by(spot_id=spot_rec.spot_id).first()
        proj = Project.query.filter_by(project_id=spot.project_id).first()
        od_spot = OutdoorSpot.query.filter(OutdoorSpot.project
                                           .contains(proj)).first()

        # @ TODO: select the outdoor record within the same hour.
        spot_rec_date = spot_rec.spot_record_time
        spot_rec_hour = spot_rec_date.replace(minute=0, second=0, microsecond=0)
        dhour = timedelta(hours=1)

        od_rec = OutdoorRecord.query.filter(
            and_(OutdoorRecord.outdoor_record_time >= spot_rec_hour,
                 OutdoorRecord.outdoor_record_time < spot_rec_hour + dhour)).first()

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




