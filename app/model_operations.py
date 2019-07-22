from  typing import Dict, Optional
from .exceptions import ValueExistedError
from sqlalchemy.exc import IntegrityError
from datetime import timedelta, datetime
from .models import User, Location, Project, ProjectDetail
from .models import  ClimateArea, Company, Permission
from .models import OutdoorSpot, OutdoorRecord
from .models import Spot, SpotRecord
from . import db


def interface(f):
    return f


@interface
def commit():
    try:  # commit after all transaction are successed.
        db.session.commit()
    except IndexError:
        db.commit.rollback()
    except:
        raise


@interface
def add_by_project_generic_view(post_data) -> None:
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

    outdoor_spot = add_outdoor_spot(post_data["outdoor_spot"])
    location = add_location(post_data["location"])
    company = add_company(post_data["company"])

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

        db.session.add(new_proj)
    except IndexError as e:
        print("Error! add_generic_view failed", e)
        raise
    except ValueError as e:
        print("Error! add_generic_view with unmatched value", e)
        raise
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise


@interface
def add_by_spot_record_view(post_data) -> None:
    post_project_id = post_data.get('project_id')
    post_spot_name = post_data.get('post_name')
    if Spot.query.filter_by(spot_name=post_spot_name).all():
        raise ValueExistedError

    try:
        new_spot = Spot(project_id=post_project_id,
                        spot_name=post_data['spot_name'])
        db.session.add(new_spot)
    except IndexError as e:
        print("Error! add_generic_view failed", e)
        raise
    except ValueError as e:
        print("Error! add_generic_view with unmatched value", e)
        raise
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise


@interface
def delete_by_project_generic_view(pid) -> None:
    project = Project.query.filter_by(project_id=pid).first()
    company = project.company
    project_details = (ProjectDetail
                       .query
                       .filter_by(project_id=pid)
                       .all())

    try:
        if (project_details):
            for pd in project_details:
                db.session.delete(pd)
        if (company and len(company.project.all()) == 1):
            db.session.delete(company)
        db.session.delete(project)
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise
    except Exception as e:
        print('Error when delete by project_generic_view', e)
        raise


@interface
def delete_by_spot_record_view(sid) -> None:
    spot = Project.query.filter_by(project_id=sid)

    try:
        db.session.delete(spot)
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise
    except Exception as e:
        print('Error delete by spot_generic_view', e)
        raise


def add_company(company_data: Dict) -> Optional[Company]:
    """ if no such location fond, create a new location """
    new_company = None
    company = (Company
               .query
               .filter_by(
                   construction_company=company_data["construction_company"])
               .filter_by(
                   tech_support_company=company_data["tech_support_company"])
               .filter_by(
                   project_company=company_data["project_company"]).
               first())

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
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise

    return new_company


def add_outdoor_spot(od_spot_data: Dict) -> Optional[OutdoorSpot]:
    """
    if no such location fond, create a new location
    """

    new_od_spot = None
    # only need outdoor_spot_id to check if the weather station is
    # already existed.

    od_spot = (OutdoorSpot
               .query
               .filter_by(outdoor_spot_id=od_spot_data["outdoor_spot_id"])
               .first())

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
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise

    return new_od_spot


def add_location(location_data: Dict) -> Optional[Location]:
    """ if no such location fond, create a new location """
    new_loc = None
    loc = (Location.query
           .filter_by(province=location_data["province"])
           .filter_by(city=location_data["city"])
           .first())

    if (loc):
        return loc

    try:
        # location must have a climate area.
        climate_area = (ClimateArea
                        .query
                        .filter_by(area_name=location_data["climate_area_name"])
                        .first())

        if not climate_area:
            raise ValueError('unknown climate area')

        new_loc = Location(climate_area=climate_area,
                           province=location_data["province"],
                           city=location_data["city"])
    except IndexError as e:
        print("Error! add_location failed", e)
        raise
    except ValueError as e:
        print("Error! add_location with unmatched value", e)
        raise
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise

    except:
        raise

    return new_loc



