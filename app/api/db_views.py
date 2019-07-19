"""
Provide joined table search.
Basic db query will be aggregated here and dispatched to frontend components.
"""
from  typing import Dict, Optional
from datetime import timedelta, datetime
from flask import jsonify, request
from . import api
from .exceptions import ValueExistedError
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
            add_by_project_generic_view(post_data, response_object)
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
            climate_area = Location.query                                      \
                .filter_by(location_id=proj["location"]["location_id"])        \
                .first().climate_area.to_json()
            proj.update({"climate_area": climate_area})
        response_object["project_generic_views"] = projects
    return jsonify(response_object)


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


def add_location(location_data: Dict) -> Optional[Location]:
    """ if no such location fond, create a new location """
    new_loc = None
    loc = Location.query                                                       \
        .filter_by(province=location_data["province"])                         \
        .filter_by(city=location_data["city"]).first()

    if (loc):
        return loc

    try:
        # location must have a climate area.
        climate_area = ClimateArea.query                                       \
            .filter_by(area_name=location_data["climate_area_name"]).first()

        if not climate_area:
            raise ValueError('unknown climate area');

        new_loc = Location(climate_area=climate_area,
                           province=location_data["province"],
                           city=location_data["city"])
    except IndexError as e:
        print("Error! add_location failed", e)
        raise
    except ValueError as e:
        print("Error! add_location with unmatched value", e)
        raise
    except:
        raise

    return new_loc


def add_company(company_data: Dict) -> Optional[Company]:
    """ if no such location fond, create a new location """
    new_company = None
    company = Company.query                                                    \
        .filter_by(construction_company=company_data["construction_company"])  \
        .filter_by(tech_support_company=company_data["tech_support_company"])  \
        .filter_by(project_company=company_data["project_company"]).first()

    if (company):
        return company

    try:
        new_company = Company(
            construction_company=company_data["construction_company"],
            tech_support_company=company_data["tech_support_company"],
            project_company=company_data["project_company"])

    except IndexError as e:
        print("Error! add_company failed", e)
        raise
    except ValueError as e:
        print("Error! add_company with unmatched value", e)
        raise

    return new_company


def add_outdoor_spot(od_spot_data: Dict) -> Optional[OutdoorSpot]:
    """
    if no such location fond, create a new location
    """

    new_od_spot = None
    # only need outdoor_spot_id to check if the weather station is
    # already existed.

    od_spot = OutdoorSpot.query                                                \
        .filter_by(outdoor_spot_id=od_spot_data["outdoor_spot_id"])            \
        .first()

    if (od_spot):
        return od_spot

    try:  # need id and name to create a new weather spot when it doesn't exsit
        new_od_spot = OutdoorSpot(
            outdoor_spot_id=od_spot_data["outdoor_spot_id"],
            outdoor_spot_name=od_spot_data["outdoor_spot_name"])

    except IndexError as e:
        print("Error! add_outdoor_spot failed", e)
        raise
    except ValueError as e:
        print("Error! add_outdoor_spot with unmatched value", e)
        raise

    return new_od_spot


def add_by_project_generic_view(post_data, response_object) -> None:
    """
    add project via project generic view
    - if the operation is successed, it will a create a new project in db.
    - if the given location, company, outdoor spot are not in db, the function
    will create them.
    - the operation will not create climate area that are not existed.
    - the operation is atomic, it will only commit transaction after all
    operations are successful.
    """
    post_project_name = post_data.get('project_name')
    if Project.query.filter_by(project_name=post_project_name).all():
        raise ValueExistedError

    print('before::')
    outdoor_spot = add_outdoor_spot(post_data["outdoor_spot"])
    print(outdoor_spot)
    print('od::')
    location = add_location(post_data["location"])
    print(location)
    print('loc::')
    company = add_company(post_data["company"])
    print(company)
    print('com::')

    try:

        new_proj = Project(outdoor_spot=outdoor_spot,
                           location=location,
                           company=company,
                           project_name=post_data["project_name"],
                           district=post_data["district"],
                           floor=post_data["floor"],
                           longitude=post_data["longitude"],
                           latitude=post_data["latitude"],
                           area=post_data["area"],
                           demo_area=post_data["demo_area"],
                           building_type=post_data["building_type"],
                           building_height=post_data["building_height"],
                           finished_time=datetime.fromisoformat(
                               post_data["finished_time"]),
                           record_started_from=datetime.fromisoformat(
                               post_data["record_started_from"]),
                           record_ended_by=datetime.fromisoformat(
                               post_data["record_ended_by"]),
                           description=post_data["description"])

        print('after::')
        db.session.add(new_proj)
    except IndexError as e:
        print("Error! add_generic_view failed", e)
        raise
    except ValueError as e:
        print("Error! add_generic_view with unmatched value", e)
        raise


