"""
Collection of db operations.
Each add function return the data created.
to record the change
"""

from typing import Dict, Optional, Callable, Union, ByteString
from .exceptions import ValueExistedError
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from datetime import timedelta, datetime
from .models import User, Location, Project, ProjectDetail
from .models import ClimateArea, Company, Permission
from .models import OutdoorSpot, OutdoorRecord
from .models import Spot, SpotRecord, Device
from app.api.api_types import ApiRequest, ApiResponse, ReturnCode
from datetime import datetime as dt
from dataGetter.utils import str_to_datetime
from app.utils import normalize_time
from . import db
import logging

PostData = Dict


def interface(f):
    return f


def fromisoformat(dtstr: str) -> Optional[dt]:
    """ handle None case """
    if not dtstr:
        return None
    return datetime.fromisoformat(dtstr)


def convert(val: str, typ) -> Union[None, int, float]:
    """ convert from string to expected type """
    if not val or val == '':
        return None
    return typ(val)


def json_convert(jsondata, key, typ) -> None:
    jsondata[key] = convert(jsondata[key], typ)


def json_to_bool(val: Union[bool, int, str, None]) -> Optional[bool]:
    """ convert various possible json format for bool to boolean value """
    if isinstance(val, bool):
        return val

    if isinstance(val, int):
        if val == 1:
            return True
        elif val == 0:
            return False
        else:
            return None

    if isinstance(val, str):
        if val in ("True", "true", "1"):
            return True
        elif val in ("False", "false", "0"):
            return False
        else:
            return None
    return None


@interface
def add_project(project_data: PostData) -> Optional[Project]:
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
    project = Project.query.filter_by(project_name=project_data.get('project_name')).first()
    if project:
        return project

    new_proj = None

    # add foregien key records.
    # if the record is not a model object, then it is a project_data form dictionary.
    # convert it into
    outdoor_spot: Union[OutdoorSpot, str] = project_data["outdoor_spot"]
    if not isinstance(project_data["outdoor_spot"], OutdoorSpot):
        outdoor_spot = add_outdoor_spot(outdoor_spot)

    location: Union[Location, str] = project_data["location"]
    if not isinstance(project_data["location"], Location):
        location = add_location(location)

    # add companies
    company_lists = ["tech_support_company", "project_company", "construction_company"]
    is_company = lambda data: isinstance(data, Company)

    if all(map(is_company, (map(project_data.get, company_lists)))):
        tech_support_company = project_data["tech_support_company"]
        project_company = project_data["project_company"]
        construction_company = project_data["construction_company"]

    else:  # else assume all are project_data jsons. Error will be catched in add company.
        def check_company(company_dict: PostData) -> PostData:  # set '' company to None
            if company_dict.get('company_name') == '':
                company_dict['company_name'] = None
            return company_dict

        tech_support_company = add_company(check_company(project_data["tech_support_company"]))
        project_company = add_company(check_company(project_data["project_company"]))
        construction_company = add_company(check_company(project_data["construction_company"]))

    # type conversion from string.
    json_convert(project_data, 'floor', int)
    json_convert(project_data, 'longitude', float)
    json_convert(project_data, 'latitude', float)
    json_convert(project_data, 'area', float)
    json_convert(project_data, 'demo_area', float)
    json_convert(project_data, 'building_height', float)

    if not isinstance(project_data['started_time'], dt):
        json_convert(project_data, 'started_time', lambda s: fromisoformat(s.split('T')[0]))

    if not isinstance(project_data['finished_time'], dt):
        json_convert(project_data, 'finished_time', lambda s: fromisoformat(s.split('T')[0]))

    if not isinstance(project_data['record_started_from'], dt):
        json_convert(project_data, 'record_started_from', lambda s: fromisoformat(s.split('T')[0]))

    try:
        new_proj = Project(
            outdoor_spot=outdoor_spot,
            location=location,

            tech_support_company=tech_support_company,
            project_company=project_company,
            construction_company=construction_company,

            project_name=project_data["project_name"],
            district=project_data["district"],
            floor=project_data["floor"],
            longitude=project_data["longitude"],
            latitude=project_data["latitude"],
            area=project_data["area"],
            demo_area=project_data["demo_area"],
            building_type=project_data["building_type"],
            building_height=project_data["building_height"],
            started_time=project_data["started_time"],
            finished_time=project_data["finished_time"],
            record_started_from=project_data["record_started_from"],
            description=project_data["description"])

        db.session.add(new_proj)
    except IndexError as e:
        logging.error("Error! add_project failed {}".format(e))
        raise
    except ValueError as e:
        logging.error("Error! add_project with unmatched value {}".format(e))
        raise
    except IntegrityError as e:
        logging.error("Error! add_project :  {}".format(e))
        raise

    return new_proj


@interface
def add_spot(spot_data: PostData) -> Optional[Spot]:
    # TODO 2020-01-04
    if not isinstance(spot_data, PostData):
        return None

    spot = Spot.query.filter_by(spot_name=spot_data["spot_name"]).first()
    if spot:
        return spot

    new_spot = None

    # project id
    project: Union[Project, str, int, None] = spot_data.get('project')
    if not project:
        pass
    elif not isinstance(project, Project):
        project = Project.query.filter_by(project_id=int(project)).first()

    image: Optional[ByteString] = spot_data.get('image')

    try:
        new_spot = Spot(project=project,
                        spot_name=spot_data.get('spot_name'),
                        spot_type=spot_data.get('spot_type'),
                        image=image)
        db.session.add(new_spot)
    except IndexError as e:
        logging.error("Error! add_generic_view failed: {}".format(e))
        raise
    except ValueError as e:
        logging.error("Error! add_generic_view with unmatched value: {}".format(e))
        raise
    except IntegrityError as e:
        logging.error("Error! add_generic_view: : {}".format(e))
        raise
    return new_spot


@interface
def add_spot_record(spot_record_data: PostData) -> Optional[SpotRecord]:
    if not isinstance(spot_record_data, PostData):
        return None

    # time can either be dt or string.
    spot_record_time: Union[dt, str, None] = normalize_time(5)(
        spot_record_data['spot_record_time'])
    if not isinstance(spot_record_time, dt):
        spot_record_time = normalize_time(5)(
            str_to_datetime(spot_record_data['spot_record_time']))

    # query with device id or device name
    device: Union[Device, str, None] = spot_record_data.get('device')
    if not isinstance(device, Device):
        device = Device.query.filter_by(device_id=spot_record_data.get("device")).first()

    # change in 2020-01-08
    # same device and same spot record time means the same record.
    # if device is None, skip the record because it doesn't form a valid
    spot_record = (SpotRecord
                   .query
                   .filter_by(spot_record_time=spot_record_time)
                   .filter(and_(
                       SpotRecord.spot_record_time == spot_record_time,

                       SpotRecord.device == device))
                   .first())
    if spot_record:
        return spot_record

    new_spot_record = None

    try:
        json_convert(spot_record_data, 'window_opened', json_to_bool)
        json_convert(spot_record_data, 'temperature', float)
        json_convert(spot_record_data, 'humidity', float)
        json_convert(spot_record_data, 'ac_power', float)
        json_convert(spot_record_data, 'pm25', float)
        json_convert(spot_record_data, 'co2', float)

        new_spot_record = SpotRecord(
            spot_record_time=spot_record_time,
            device=device,
            window_opened=spot_record_data.get("window_opened"),
            temperature=spot_record_data.get("temperature"),
            humidity=spot_record_data.get("humidity"),
            ac_power=spot_record_data.get("ac_power"),
            pm25=spot_record_data.get("pm25"),
            co2=spot_record_data.get("co2"))
        db.session.add(new_spot_record)
    except IndexError as e:
        logging.error("Error! add_company failed: {}".format(e))
        raise
    except ValueError as e:
        logging.error("Error! add_company with unmatched value: {}".format(e))
        raise
    except IntegrityError as e:
        logging.error("Error! add_company failed: : {}".format(e))
        raise

    return new_spot_record


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
        logging.error("Error! add_generic_view: : {}".format(e))
        raise
    except Exception as e:
        logging.error('Error when delete by project_generic_view: {}'.format(e))
        raise


@interface
def delete_spot(sid: int) -> None:
    spot = Spot.query.filter_by(spot_id=sid).first()

    try:
        db.session.delete(spot)
    except IntegrityError as e:
        logging.error("Error! add_generic_view: : {}".format(e))
        raise
    except Exception as e:
        logging.error('Error delete by spot_generic_view: {}'.format(e))
        raise


@interface
def add_company(company_data: PostData) -> Optional[Company]:
    """
    if the given company is already existed, return it without change anything.
    if no such location fond, create a new location
    """
    if not isinstance(company_data, PostData):
        return None

    company = (Company.query
               .filter_by(
                   company_name=company_data["company_name"]).first())
    if (company):
        return company

    new_company = None

    try:
        new_company = Company(company_name=company_data["company_name"])

        db.session.add(new_company)
    except IndexError as e:
        logging.error("Error! add_company failed: {}".format(e))
        raise
    except ValueError as e:
        logging.error("Error! add_company with unmatched value: {}".format(e))
        raise
    except IntegrityError as e:
        logging.error("Error! add_company failed: : {}".format(e))
        raise

    return new_company


@interface
def add_outdoor_spot(od_spot_data: PostData) -> Optional[OutdoorSpot]:
    """
    if the given spot is already existed, return it without change anything.
    if no such spot fond, create a new location
    """
    if not isinstance(od_spot_data, PostData):
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

        db.session.add(new_od_spot)
    except IndexError as e:
        logging.error("Error! add_outdoor_spot failed: {}".format(e))
        raise
    except ValueError as e:
        logging.error("Error! add_outdoor_spot with unmatched value: {}".format(e))
        raise
    except IntegrityError as e:
        logging.error("Error! add_generic_view: : {}".format(e))
        raise

    return new_od_spot


@interface
def add_location(location_data: PostData) -> Optional[Location]:
    """ if no such location fond, create a new location """
    if not isinstance(location_data, PostData):
        return None

    loc = (Location.query
           .filter_by(province=location_data["province"])
           .filter_by(city=location_data["city"])
           .first())

    new_loc = None
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
        db.session.add(new_loc)
    except IndexError as e:
        logging.error("Error! add_location failed: {}".format(e))
        raise
    except ValueError as e:
        logging.error("Error! add_location with unmatched value: {}".format(e))
        raise
    except IntegrityError as e:
        logging.error("Error! add_generic_view: : {}".format(e))
        raise

    except Exception:
        raise

    return new_loc


@interface
def add_device(device_data: PostData) -> Optional[Device]:
    """ if no such location fond, create a new location """
    # TODO 2020-01-04
    if not isinstance(device_data, PostData):
        return None

    device = (Device
              .query
              .filter_by(device_name=device_data.get("device_name"))
              .first())
    if device:
        return device

    spot: Union[Spot, int, str, None] = device_data.get('spot')
    if spot and isinstance(spot, Spot) or not spot:  # None or be a Spot.
        pass
    elif isinstance(spot, int) or isinstance(spot, str):  # Convert from id to Spot.
        spot = Spot.query.filter_by(spot_id=int(spot)).first()
    else:
        logging.error('add_device error, spot type is incorrect.')
        return None

    new_device = None

    try:
        # location must have a climate area.
        if not isinstance(device_data['create_time'], dt):
            json_convert(device_data, 'create_time', lambda s: fromisoformat(s.split('T')[0]))

        if not isinstance(device_data['modify_time'], dt):
            json_convert(device_data, 'modify_time', lambda s: fromisoformat(s.split('T')[0]))

        if not isinstance(device_data['online'], bool):
            json_convert(device_data, 'online', json_to_bool)

        new_device = Device(device_name=device_data.get("device_name"),
                            device_type=device_data.get("device_type"),
                            online=device_data.get("online"),
                            spot=spot,
                            create_time=device_data["create_time"],
                            modify_time=device_data["modify_time"])

        db.session.add(new_device)
    except IndexError as e:
        logging.error("Error! add_location failed: {}".format(e))
        raise
    except ValueError as e:
        logging.error("Error! add_location with unmatched value: {}".format(e))
        raise
    except IntegrityError as e:
        logging.error("Error! add_generic_view: {}".format(e))
        raise

    except Exception:
        raise

    return new_device


#####################################
#  run operation and handle error   #
#####################################

@interface
def commit():
    try:  # commit after all transaction are successed.
        db.session.commit()
    except IndexError:
        db.commit.rollback()
    except Exception:
        raise

@interface
def commit_db_operation(response_object: ApiResponse,
                        op: Callable[[Dict], None],
                        post_data: Dict,
                        name: str) -> ApiResponse:
    """
    run given db operation and return the response object
    if commit failed, handle exceptions.
    """
    try:
        res = op(post_data)
        commit()

        if isinstance(res, db.Model) and hasattr(res, 'to_json'):
            response_object['data'] = res.to_json()

    except ValueExistedError as e:
        response_object["status"] = ReturnCode.BAD_REQUEST.value
        response_object["message"] = f"{name} already existed: {e}"

    except IndexError as e:
        response_object["status"] = ReturnCode.BAD_REQUEST.value
        response_object["message"] = f"Failed to add {name} : {e}"

    except ValueError as e:
        response_object["status"] = ReturnCode.BAD_REQUEST.value
        response_object["message"] = f"Unmatched value type: {e}"

    except IntegrityError as e:
        response_object["status"] = ReturnCode.NO_DATA.value
        response_object["message"] = f"IntegrityError: {e}"

    except Exception as e:
        response_object["status"] = ReturnCode.BAD_REQUEST.value
        response_object["message"] = f"Error: {e}"

    finally:
        return response_object

    return response_object
