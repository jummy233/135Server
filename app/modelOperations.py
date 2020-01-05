"""
Collection of db operations.
Each add function return the data created.
to record the change
"""

from  typing import Dict, Optional, Callable, Union, ByteString
from .exceptions import ValueExistedError
from sqlalchemy.exc import IntegrityError
from datetime import timedelta, datetime
from .models import User, Location, Project, ProjectDetail
from .models import  ClimateArea, Company, Permission,
from .models import OutdoorSpot, OutdoorRecord
from .models import Spot, SpotRecord, Device
from datetime import datetime as dt
from . import db

def interface(f):
    return f


@interface
def commit():
    try:  # commit after all transaction are successed.
        db.session.commit()
    except IndexError:
        db.commit.rollback()
    except Exception:
        raise


@interface
def add_project(post_data) -> None:
    """
    add project via project generic view

    - if the operation is successed, it will a create a new project in db.

    - if the given location, company, outdoor spot are not in db, the function

    will create them.
    - the operation will not create climate area that are not existed.

    - the operation is atomic, it will only commit transaction after all
    operations are successful.

    Note: add_location, add_company, and add_outdoor_spot will return sqlalchemy
    object directly if they exists in the db.

    Note: foreign key values like location and company can be either
    in from of json or sqlalchemy object. If it is the later case, directly
    use the object.

    """
    if Project.query.filter_by(project_name=post_data.get('project_name')).all():
        raise ValueExistedError

    # add foregien key records.
    outdoor_spot: Union[OutdoorSpot, str] = post_data["outdoor_spot"]
    if not isinstance(post_data["outdoor_spot"], OutdoorSpot):
        outdoor_spot = add_outdoor_spot(outdoor_spot)

    location: Union[Location, str] = post_data["location"]
    if not isinstance(post_data["location"], Location):
        location = add_location(location)

    # add companies
    company_lists = ["tech_support_company", "project_company", "construction_company"]
    is_company = lambda data: isinstance(data, Company)

    if all(map(is_company, (map(post_data.get, company_lists)))):
        tech_support_company = post_data["tech_support_company"]
        project_company = post_data["project_company"]
        construction_company = post_data["construction_company"]

    else:  # else assume all are post jsons. Error will be catched in add company.
        tech_support_company = add_company(post_data["tech_support_company"])
        project_company = add_company(post_data["project_company"])
        construction_company = add_company(post_data["construction_company"])

    def fromisoformat(dtstr: str) -> Optional[dt]:
        """ handle None case """
        if not dtstr:
            return None
        return datetime.fromisoformat(dtstr)

    try:
        new_proj = Project(
            outdoor_spot=outdoor_spot,
            location=location,

            tech_support_company=tech_support_company,
            project_company=project_company,
            construction_company=construction_company,

            project_name=post_data["project_name"],
            district=post_data["district"],
            floor=post_data["floor"],
            longitude=post_data["longitude"],
            latitude=post_data["latitude"],
            area=post_data["area"],
            demo_area=post_data["demo_area"],
            building_type=post_data["building_type"],
            building_height=post_data["building_height"],
            started_time=fromisoformat(post_data["started_time"]),
            finished_time=fromisoformat(post_data["finished_time"]),
            record_started_from=fromisoformat(
                post_data["record_started_from"]),
            description=post_data["description"])
        print(new_proj)

        db.session.add(new_proj)
    except IndexError as e:
        print("Error! add_project failed", e)
        raise
    except ValueError as e:
        print("Error! add_project with unmatched value", e)
        raise
    except IntegrityError as e:
        print("Error! add_project : ", e)
        raise


@interface
def add_spot(post_data: dict) -> Optional[Spot]:
    # TODO 2020-01-04
    if not isinstance(post_data, Dict):
        return None

    new_spot = None

    project: Union[Project, str] = post_data.get('project')
    if not isinstance(post_project, Project):
        post_project = Project.query.filter_by(project_id=post_project)

    spot_name: str = post_data.get('spot_name')
    spot_type: str = post_data.get('spot_type')
    image: Optional[ByteString] = post_data.get('image')

    if Spot.query.filter_by(spot_name=spot_name).all():
        raise ValueExistedError

    try:
        new_spot = Spot(project=project,
                        spot_name=spot_name,
                        spot_type=spot_type,
                        image=image)
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
    return new_spot


@interface
def add_spot_record(post_data) -> None:
    if SpotRecord.query.filter_by(spot_record_time=post_data.get('spot_record_time')):
        raise ValueExistedError
    # TODO 2020-01-03


@interface
def delete_project(pid) -> None:
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
def delete_spot(sid: int) -> None:
    spot = Spot.query.filter_by(spot_id=sid).first()

    try:
        db.session.delete(spot)
    except IntegrityError as e:
        print("Error! add_generic_view: ", e)
        raise
    except Exception as e:
        print('Error delete by spot_generic_view', e)
        raise


@interface
def add_company(company_data: Dict) -> Optional[Company]:
    """
    if the given company is already existed, return it without change anything.
    if no such location fond, create a new location
    """
    if not isinstance(company_data, Dict):
        return None

    new_company = None
    company = (Company.query
               .filter_by(company_name=company_data["company_name"]).first())

    if (company):
        return company

    try:
        new_company = Company(company_name=company_data["company_name"])

    except IndexError as e:
        print("Error! add_company failed", e)
        raise
    except ValueError as e:
        print("Error! add_company with unmatched value", e)
        raise
    except IntegrityError as e:
        print("Error! add_company failed: ", e)
        raise

    return new_company


@interface
def add_outdoor_spot(od_spot_data: Dict) -> Optional[OutdoorSpot]:
    """
    if the given spot is already existed, return it without change anything.
    if no such spot fond, create a new location
    """
    if not isinstance(od_spot_data, Dict):
        return None
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


@interface
def add_location(location_data: Dict) -> Optional[Location]:
    """ if no such location fond, create a new location """
    if not isinstance(location_data, Dict):
        return None

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

    except Exception:
        raise

    return new_loc


@interface
def add_device(device_data: Dict) -> Optional[Device]:
    """ if no such location fond, create a new location """
    # TODO 2020-01-04
    if not isinstance(device_data, Dict):
        return None

    new_device = None

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

    except Exception:
        raise

    return new_loc


#####################################
#  run operation and handle error   #
#####################################


def _commit_db(op: Callable[[Dict], None], post_data: Dict) -> None:
    op(post_data)
    commit()


def commit_db_operation(response_object: Dict,
                        op: Callable[[Dict], None],
                        post_data: Dict,
                        name: str) -> Dict:
    """
    run given db operation and return the response object
    """
    try:
        _commit_db(op, post_data)

    except ValueExistedError as e:
        response_object["status"] = "failed"
        response_object["message"] = f"{name} already existed: {e}"

    except IndexError as e:
        response_object["status"] = "failed"
        response_object["message"] = f"Failed to add {name} : {e}"

    except ValueError as e:
        response_object["status"] = "failed"
        response_object["message"] = f"Unmatched value type: {e}"

    except IntegrityError as e:
        response_object["status"] = "failed"
        response_object["message"] = f"IntegrityError: {e}"

    except Exception as e:
        response_object["status"] = "failed"
        response_object["message"] = f"Error: {e}"

    finally:
        return response_object

    return response_object
