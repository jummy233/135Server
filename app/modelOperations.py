
"""
Collection of db operations.
Each add function return the data created.
to record the change
"""

import importlib
from abc import ABC, abstractmethod
from copy import copy
from datetime import datetime as dt
from logging import DEBUG
from typing import (ByteString, Callable, Dict, List, NewType, Optional, Tuple,
                    TypedDict, Union)

from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from app.api_types import ApiRequest, ApiResponse, ReturnCode
from app.utils import normalize_time
from dataGetter.utils import str_to_datetime
from logger import make_logger

from . import db
from .caching.caching import Cache, get_cache
from .caching.global_cache import GlobalCache, GlobalCacheKey, ModelDataEnum
from .models import (ClimateArea, Company, Data, Device, Location,
                     OutdoorRecord, OutdoorSpot, Permission, Project,
                     ProjectDetail, Spot, SpotRecord, User)

logger = make_logger('modelOperation', 'modelOperation_log', DEBUG)
logger.propagate = False



# from app import global_cache

app = importlib.import_module('app')
global_cache = app.global_cache


# TODO lazy load global_cache.global_cacheall so it is fully initialized.
PostData = Dict

# load global_cache.global_cacheall lazily.
# lazy_caching = lazyload('caching.cache_instance')


@global_cache.global_cacheall
def cacher_test(cache):
    print(cache)


def interface(f):
    return f


def fromisoformat(dtstr: str) -> Optional[dt]:
    """ handle None case """
    if not dtstr:
        return None
    return dt.fromisoformat(dtstr)


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


###############################
#  Abstract class definition  #
###############################


class ModelInterfaces(ABC):
    """ Used as a namespace here """

    class BatchAdd(ABC):
        """ add stuffs in batch with core sql operation """
        @staticmethod
        @abstractmethod
        def add_spot_record_batch(project_data: PostData) -> bool:
            """
            add spot_record in batch
            return True if stuff get inserted.
            """

    class Add(ABC):
        """ add data """
        @staticmethod
        @abstractmethod
        def add_project(project_data: PostData) -> Optional[Project]:
            """ add project """

        @staticmethod
        @abstractmethod
        def add_device(device_data: PostData) -> Optional[Device]:
            """ add device"""

        @staticmethod
        @abstractmethod
        def add_spot(spot_data: PostData) -> Optional[Spot]:
            """ add spot """

        @staticmethod
        @abstractmethod
        def add_spot_record(spot_record_data: PostData) -> Optional[SpotRecord]:
            """ add spot_record """

        @staticmethod
        @abstractmethod
        def add_outdoor_spot(outdoor_spot_data: PostData) -> Optional[OutdoorSpot]:
            """ add outdoor_spot """

    class Update(ABC):
        """ update data """
        @staticmethod
        @abstractmethod
        def update_project(project_data: PostData) -> Optional[Project]:
            """ update project """
        @staticmethod
        @abstractmethod
        def update_device(device_data: PostData) -> Optional[Device]:
            """ update device"""
        @staticmethod
        @abstractmethod
        def update_spot(spot_data: PostData) -> Optional[Spot]:
            """ update spot """
        @staticmethod
        @abstractmethod
        def update_spot_record(spot_record_data: PostData) -> Optional[SpotRecord]:
            """ update spot_record """
        @staticmethod
        @abstractmethod
        def update_outdoor_spot(outdoor_spot_data: PostData) -> Optional[OutdoorSpot]:
            """ update outdoor_spot """

    class Delete(ABC):
        @staticmethod
        @abstractmethod
        def delete_project(pid: int) -> None:
            """ delete project """
        @staticmethod
        @abstractmethod
        def delete_device(did: int) -> None:
            """ delete device"""
        @staticmethod
        @abstractmethod
        def delete_spot(sid: int) -> None:
            """ delete spot """
        @staticmethod
        @abstractmethod
        def delete_spot_record(rid: int) -> None:
            """ delete spot_record """
        @staticmethod
        @abstractmethod
        def delete_outdoor_spot(oid: int) -> None:
            """ delete outdoor_spot """


class ModelOperations(ModelInterfaces):

    ################
    #  Add module  #
    ################

    class BatchAdd():
        @staticmethod
        def add_spot_record_batch(spot_record_data_list: List[PostData]):

            @global_cache.global_cacheall
            def _add_spot_record_batch(cache: Optional[GlobalCache] = None) -> bool:
                return True
            return _add_spot_record_batch(spot_record_data_list)

    class Add(ModelInterfaces.Add):

        @staticmethod
        def add_project(project_data: PostData):

            @global_cache.global_cacheall
            def _add_project(cache: Optional[GlobalCache] = None) -> Optional[Project]:
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
                if not isinstance(project_data, PostData):
                    return None

                project = Project.query.filter_by(project_name=project_data.get('project_name')).first()
                if project:
                    logger.debug('project exists')
                    return project

                try:
                    new_project: Optional[Project] = ModelOperations._make_project(project_data)
                    db.session.add(new_project)

                    if cache is not None and new_project is not None:
                        cache[ModelDataEnum._Project][new_project.project_name] = new_project
                        cache[ModelDataEnum._Project][new_project.project_id] = new_project

                except IndexError as e:
                    logger.error("Error! add_project failed {}".format(e))
                    raise
                except ValueError as e:
                    logger.error("Error! add_project with unmatched value {}".format(e))
                    raise
                except IntegrityError as e:
                    logger.error("Error! add_project :  {}".format(e))
                    raise

                return new_project
            return _add_project()

        @staticmethod
        def add_spot(spot_data: PostData, core_db_operatoin: bool = False):

            @global_cache.global_cacheall
            def _add_spot(cache: Optional[GlobalCache] = None) -> Optional[Spot]:

                if not isinstance(spot_data, PostData):
                    return None

                if cache is not None:
                    spot = get_cache(cache, ModelDataEnum._Spot, spot_data.get("spot_name"))
                else:
                    spot = Spot.query.filter_by(spot_name=spot_data["spot_name"]).first()

                if spot:
                    logger.debug('spot exists')
                    return spot

                new_spot = None

                try:
                    new_spot = ModelOperations._make_spot(spot_data)
                    db.session.add(new_spot)

                    if cache is not None and new_spot is not None:
                        cache[ModelDataEnum._Spot][new_spot.spot_name] = new_spot

                except IndexError as e:
                    logger.error("Error! add_generic_view failed: {}".format(e))
                    raise
                except ValueError as e:
                    logger.error(
                        "Error! add_generic_view with unmatched value: {}".format(e))
                    raise
                except IntegrityError as e:
                    logger.error("Error! add_generic_view: : {}".format(e))
                    raise
                return new_spot
            return _add_spot()

        @staticmethod
        def add_device(device_data: PostData):

            @global_cache.global_cacheall
            def _add_device(cache: Optional[GlobalCache] = None) -> Optional[Device]:
                """ if no such location fond, create a new location """

                # TODO 2020-01-04
                if not isinstance(device_data, PostData):
                    return None

                if cache is not None:
                    logger.debug('add device')

                    device = get_cache(cache,
                                       ModelDataEnum._Device,
                                       device_data.get("device_name"))

                    logger.debug('device from cache {}'.format('device'))
                else:

                    device = (Device
                              .query
                              .filter_by(device_name=device_data.get("device_name"))
                              .first())

                if device:
                    logger.debug('device exists')
                    return device

                new_device = None

                try:
                    new_device = ModelOperations._make_device(device_data)
                    db.session.add(new_device)

                    # add device into cache if it is not there.
                    if cache is not None and new_device is not None:
                        cache[ModelDataEnum._Device][new_device.device_name] = new_device
                        cache[ModelDataEnum._Device][new_device.device_id] = new_device

                except IndexError as e:
                    logger.error("Error! add_location failed: {}".format(e))
                    raise
                except ValueError as e:
                    logger.error(
                        "Error! add_location with unmatched value: {}".format(e))
                    raise
                except IntegrityError as e:
                    logger.error("Error! add_generic_view: {}".format(e))
                    raise

                except Exception:
                    raise

                return new_device

            return _add_device()

        @staticmethod
        def add_spot_record(spot_record_data: PostData):

            @global_cache.global_cacheall
            def _add_spot_record(cache: Optional[GlobalCache] = None) -> Optional[SpotRecord]:
                if not isinstance(spot_record_data, PostData):
                    return None

                logger.debug(spot_record_data)
                # time can either be dt or string.
                spot_record_time: Union[dt, str, None] = normalize_time(5)(
                    spot_record_data['spot_record_time'])

                if not isinstance(spot_record_time, dt):
                    spot_record_time = normalize_time(5)(
                        str_to_datetime(spot_record_data['spot_record_time']))

                # query with device id or device name
                device: Union[Device, str, None] = spot_record_data.get('device')

                if not isinstance(device, Device):

                    if cache is not None:
                        device = get_cache(
                            cache,
                            ModelDataEnum._Device,
                            spot_record_data.get('device'))
                    else:
                        logger.debug('using database')
                        device = Device.query.filter_by(
                            device_id=spot_record_data.get("device")).first()

                # change in 2020-01-08
                # same device and same spot record time means the same record.
                # if device is None, skip the record because it doesn't form a valid

                # change in 2020-01-21
                # generate cache key for records in _LRUDictionary.
                if isinstance(spot_record_time, dt) and isinstance(device, Device):
                    cache_key: Optional[GlobalCacheKey] = (spot_record_time, device)
                else:
                    cache_key = None

                if cache is not None and cache_key is not None:
                    spot_record = (
                        get_cache(cache,
                                  ModelDataEnum._SpotRecord,
                                  cache_key))

                else:  # expensive.
                    spot_record = (SpotRecord
                                   .query
                                   .filter_by(spot_record_time=spot_record_time)
                                   .filter(and_(

                                       SpotRecord.spot_record_time == spot_record_time,

                                       SpotRecord.device == device))
                                   .first())
                if spot_record:
                    logger.debug('record already exists.')
                    return spot_record

                new_spot_record = None

                try:
                    new_spot_record = ModelOperations._make_spot_reocrd(
                        spot_record_data)
                    db.session.add(new_spot_record)

                    # add new record into cache.
                    if (cache_key is not None and
                            new_spot_record is not None and
                            cache is not None):

                        cache[ModelDataEnum._SpotRecord][cache_key] = new_spot_record

                except IndexError as e:
                    logger.error("Error! add_spot_record failed: {}".format(e))
                    raise
                except ValueError as e:
                    logger.error(
                        "Error! add_spot_record with unmatched value: {}".format(e))
                    raise
                except IntegrityError as e:
                    logger.error("Error! add_spot_record failed: : {}".format(e))
                    raise

                return new_spot_record
            return _add_spot_record()

        @staticmethod
        def add_outdoor_spot(od_spot_data: PostData):

            @global_cache.global_cacheall
            def _add_outdoor_spot(cache: Optional[GlobalCache] = None) -> Optional[OutdoorSpot]:
                """
                if the given spot is already existed, return it without change anything.
                if no such spot fond, create a new location
                """
                if not isinstance(od_spot_data, PostData):
                    return None
                # only need outdoor_spot_id to check if the weather station is
                # already existed.

                od_spot = (OutdoorSpot
                           .query
                           .filter_by(outdoor_spot_id=od_spot_data["outdoor_spot_id"])
                           .first())

                if (od_spot):
                    return od_spot

                new_od_spot = None
                try:  # need id and name to create a new weather spot when it doesn't exsit
                    new_od_spot = ModelOperations._make_outdoor_spot(od_spot_data)
                    db.session.add(new_od_spot)

                    if cache is not None and new_od_spot is not None:
                        # deal with it later.
                        NotImplementedError

                except IndexError as e:
                    logger.error("Error! add_outdoor_spot failed: {}".format(e))
                    raise
                except ValueError as e:
                    logger.error(
                        "Error! add_outdoor_spot with unmatched value: {}".format(e))
                    raise
                except IntegrityError as e:
                    logger.error("Error! add_generic_view: : {}".format(e))
                    raise

                return new_od_spot
            return _add_outdoor_spot()

        @staticmethod
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
                new_loc = ModelOperations._make_location(location_data)
                db.session.add(new_loc)
            except IndexError as e:
                logger.error("Error! add_location failed: {}".format(e))
                raise
            except ValueError as e:
                logger.error(
                    "Error! add_location with unmatched value: {}".format(e))
                raise
            except IntegrityError as e:
                logger.error("Error! add_generic_view: : {}".format(e))
                raise

            except Exception:
                raise

            return new_loc

        @staticmethod
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
                new_company = Company(
                    company_name=company_data["company_name"])

                db.session.add(new_company)
            except IndexError as e:
                logger.error("Error! add_company failed: {}".format(e))
                raise
            except ValueError as e:
                logger.error(
                    "Error! add_company with unmatched value: {}".format(e))
                raise
            except IntegrityError as e:
                logger.error("Error! add_company failed: : {}".format(e))
                raise

            return new_company
        # END Add

    ###################
    #  Update module  #
    ###################

    class Update(ModelInterfaces.Update):
        @staticmethod
        def update_device(device_data: PostData) -> Optional[Device]:

            @global_cache.global_cacheall
            def _update_device(cache: Optional[GlobalCache] = None):
                if not isinstance(device_data, PostData):
                    return None
                new_device = ModelOperations._make_device(device_data)
                device = (Device
                          .query
                          .filter_by(device_name=device_data.get("device_name"))
                          .first())

                if device:
                    db.session.delete(device)

                db.session.add(new_device)
                return new_device
            return _update_device()

        @staticmethod
        def update_spot_record(spot_record_data: PostData) -> Optional[SpotRecord]:

            @global_cache.global_cacheall
            def _update_spot_record(cache: Optional[GlobalCache] = None):
                if not isinstance(spot_record_data, PostData):
                    return None

                spot_record_time: Union[dt, str, None] = normalize_time(5)(
                    spot_record_data['spot_record_time'])
                if not isinstance(spot_record_time, dt):
                    spot_record_time = normalize_time(5)(
                        str_to_datetime(spot_record_data['spot_record_time']))

                # query with device id or device name
                device: Union[Device, str, None] = spot_record_data.get('device')
                if not isinstance(device, Device):
                    device = Device.query.filter_by(
                        device_id=spot_record_data.get("device")).first()

                new_spot_record = ModelOperations._make_spot_reocrd(
                    spot_record_data)
                spot_record = (SpotRecord
                               .query
                               .filter_by(spot_record_time=spot_record_time)
                               .filter(and_(
                                   SpotRecord.spot_record_time == spot_record_time,

                                   SpotRecord.device == device))
                               .first())
                if spot_record:
                    db.session.delete(spot_record)
                db.session.add(new_spot_record)
                return new_spot_record
            return _update_spot_record()

        @staticmethod
        def update_spot(spot_data: PostData) -> Optional[Spot]:

            @global_cache.global_cacheall
            def _update_spot(cache: Optional[GlobalCache] = None):
                if not isinstance(spot_data, PostData):
                    return None

                new_spot = ModelOperations._make_spot(spot_data)
                spot = Spot.query.filter_by(
                    spot_name=spot_data["spot_name"]).first()
                if spot:
                    db.session.delete(spot)

                db.session.add(new_spot)
                return new_spot
            return _update_spot()

        @staticmethod
        def update_project(project_data: PostData) -> Optional[Project]:

            @global_cache.global_cacheall
            def _update_project(cache: Optional[GlobalCache] = None):
                if not isinstance(project_data, PostData):
                    return None

                new_project = ModelOperations._make_project(project_data)
                project = Project.query.filter_by(
                    project_name=project_data.get('project_name')).first()
                if project:
                    db.session.delete(project)

                db.session.add(new_project)
                return new_project
            return _update_project()

        @staticmethod
        def update_outdoor_spot(outdoor_spot_data: PostData) -> Optional[OutdoorSpot]:

            @global_cache.global_cacheall
            def _update_outdoor_spot(cache: Optional[GlobalCache] = None):
                if not isinstance(outdoor_spot_data, OutdoorSpot):
                    return None

                new_outdoor_spot = ModelOperations._make_outdoor_spot(
                    outdoor_spot_data)
                outdoor_spot = (
                    OutdoorSpot
                    .query
                    .filter_by(outdoor_spot_name=outdoor_spot_data.get('project_name'))
                    .first())
                if outdoor_spot:
                    db.session.delete(outdoor_spot)

                db.session.add(new_outdoor_spot)
                return new_outdoor_spot
            return _update_outdoor_spot()

    ###################
    #  Delete module  #
    ###################

    class Delete(ModelInterfaces.Delete):
        @staticmethod
        def delete_project(pid: int) -> None:
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

                if project:
                    db.session.delete(project)
                else:
                    return

            except IntegrityError as e:
                logger.error("Error! add_generic_view: : {}".format(e))
                raise
            except Exception as e:
                logger.error('Error when delete by project_generic_view: {}'.format(e))
                raise

        @staticmethod
        def delete_spot(sid: int) -> None:
            spot = Spot.query.filter_by(spot_id=sid).first()

            try:
                if spot:
                    db.session.delete(spot)
                else:
                    return
            except IntegrityError as e:
                logger.error("Error! add_generic_view: : {}".format(e))
                raise
            except Exception as e:
                logger.error('Error delete by spot_generic_view: {}'.format(e))
                raise
        # END Delete

        @staticmethod
        def delete_spot_record(rid: int) -> None:
            spot_record = SpotRecord.query.filter_by(spot_record_id=rid).first()

            try:
                if spot_record:
                    db.session.delete(spot_record)
                else:
                    return
            except IntegrityError as e:
                logger.error("Error! add_generic_view: : {}".format(e))
                raise
            except Exception as e:
                logger.error('Error delete by spot_generic_view: {}'.format(e))
                raise

        @staticmethod
        def delete_device(did: int) -> None:
            device = Device.query.filter_by(device_id=did).first()

            try:
                if device:
                    db.session.delete(device)
                else:
                    return
            except IntegrityError as e:
                logger.error("Error! add_generic_view: : {}".format(e))
                raise
            except Exception as e:
                logger.error('Error delete by spot_generic_view: {}'.format(e))
                raise

        @staticmethod
        def delete_outdoor_spot(oid: int) -> None:
            outdoor_spot = Device.query.filter_by(outdoor_spot_id=oid).first()

            try:
                if outdoor_spot:
                    db.session.delete(outdoor_spot)
                else:
                    return
            except IntegrityError as e:
                logger.error("Error! add_generic_view: : {}".format(e))
                raise
            except Exception as e:
                logger.error('Error delete by spot_generic_view: {}'.format(e))
                raise

        # END Delete

    ######################################
    #  local methods to create db object.#
    ######################################

    @staticmethod
    def _make_project(project_data: PostData) -> Optional[Project]:

        @global_cache.global_cacheall
        def _make(cache: Optional[GlobalCache] = None):
            project = None

            # add foregien key records.
            # if the record is not a model object, then it is a project_data form dictionary.
            # convert it into
            outdoor_spot: Union[OutdoorSpot, PostData,
                                None] = project_data["outdoor_spot"]
            if outdoor_spot is None:
                ...
            elif not isinstance(project_data["outdoor_spot"], OutdoorSpot):
                outdoor_spot = ModelOperations.Add.add_outdoor_spot(outdoor_spot)

            location: Union[Location, Dict, None] = project_data["location"]
            if location is None:
                ...
            elif not isinstance(project_data["location"], Location):
                location = ModelOperations.Add.add_location(location)

            # add companies
            company_lists = ["tech_support_company",
                             "project_company", "construction_company"]

            def is_company(data):
                return isinstance(data, Company)

            if all(map(is_company, (map(project_data.get, company_lists)))):
                tech_support_company = project_data["tech_support_company"]
                project_company = project_data["project_company"]
                construction_company = project_data["construction_company"]

            else:  # else assume all are project_data jsons. Error will be catched in add company.
                def check_company(company_dict: PostData) -> PostData:  # set '' company to None
                    if company_dict.get('company_name') == '':
                        company_dict['company_name'] = None
                    return company_dict

                tech_support_company = ModelOperations.Add.add_company(
                    check_company(project_data["tech_support_company"]))
                project_company = ModelOperations.Add.add_company(
                    check_company(project_data["project_company"]))
                construction_company = ModelOperations.Add.add_company(
                    check_company(project_data["construction_company"]))

            # type conversion from string.
            json_convert(project_data, 'floor', int)
            json_convert(project_data, 'longitude', float)
            json_convert(project_data, 'latitude', float)
            json_convert(project_data, 'area', float)
            json_convert(project_data, 'demo_area', float)
            json_convert(project_data, 'building_height', float)

            if not isinstance(project_data['started_time'], dt):
                json_convert(project_data, 'started_time',
                             lambda s: fromisoformat(s.split('T')[0]))

            if not isinstance(project_data['finished_time'], dt):
                json_convert(project_data, 'finished_time',
                             lambda s: fromisoformat(s.split('T')[0]))

            if not isinstance(project_data['record_started_from'], dt):
                json_convert(project_data, 'record_started_from',
                             lambda s: fromisoformat(s.split('T')[0]))

            project = Project(
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

            return project
        return _make()

    @staticmethod
    def _make_spot(spot_data: PostData) -> Optional[Spot]:

        @global_cache.global_cacheall
        def _make(cache: Optional[GlobalCache] = None):
            if not isinstance(spot_data, PostData):
                return None

            new_spot = None

            # project id
            project: Union[Project, str, int, None] = spot_data.get('project')

            if not project:
                ...

            elif not isinstance(project, Project):

                try:
                    project = Project.query.filter_by(
                        project_id=int(project)).first()
                except Exception:
                    raise

            image: Optional[ByteString] = spot_data.get('image')

            new_spot = Spot(project=project,
                            spot_name=spot_data.get('spot_name'),
                            spot_type=spot_data.get('spot_type'),
                            image=image)

            return new_spot
        return _make()

    @staticmethod
    def _make_device(device_data: PostData) -> Optional[Device]:

        @global_cache.global_cacheall
        def _make(cache: Optional[GlobalCache] = None):

            if not isinstance(device_data, PostData):
                return None

            spot: Union[Spot, int, str, None] = device_data.get('spot')
            if spot and isinstance(spot, Spot) or not spot:  # None or be a Spot.
                ...

            # Convert from id to Spot.
            elif isinstance(spot, int) or isinstance(spot, str):
                spot = Spot.query.filter_by(spot_id=int(spot)).first()
            else:
                logger.error('add_device error, spot type is incorrect.')
                return None

            device = None

            # location must have a climate area.
            if not isinstance(device_data['create_time'], dt):
                json_convert(device_data, 'create_time',
                             lambda s: fromisoformat(s.split('T')[0]))

            if not isinstance(device_data['modify_time'], dt):
                json_convert(device_data, 'modify_time',
                             lambda s: fromisoformat(s.split('T')[0]))

            if not isinstance(device_data['online'], bool):
                json_convert(device_data, 'online', json_to_bool)

            device = Device(device_name=device_data.get("device_name"),
                            device_type=device_data.get("device_type"),
                            online=device_data.get("online"),
                            spot=spot,
                            create_time=device_data["create_time"],
                            modify_time=device_data["modify_time"])
            return device
        return _make()

    @staticmethod
    def _make_spot_reocrd(spot_record_data: PostData) -> Optional[SpotRecord]:

        @global_cache.global_cacheall
        def _make(cache: Optional[GlobalCache] = None):
            if not isinstance(spot_record_data, PostData):
                return None

            # time can either be dt or string.
            spot_record_time: Union[dt, str, None] = normalize_time(5)(
                spot_record_data['spot_record_time'])
            if not isinstance(spot_record_time, dt):
                spot_record_time = normalize_time(5)(
                    str_to_datetime(spot_record_data['spot_record_time']))

            # query with device id or device name
            try:
                device: Union[Device, str, None] = spot_record_data.get('device')
                if not isinstance(device, Device):
                    device = Device.query.filter_by(
                        device_id=spot_record_data.get("device")).first()
            except Exception:
                raise

            spot_record = None

            json_convert(spot_record_data, 'window_opened', json_to_bool)
            json_convert(spot_record_data, 'temperature', float)
            json_convert(spot_record_data, 'humidity', float)
            json_convert(spot_record_data, 'ac_power', float)
            json_convert(spot_record_data, 'pm25', float)
            json_convert(spot_record_data, 'co2', float)

            spot_record = SpotRecord(
                spot_record_time=spot_record_time,
                device=device,
                window_opened=spot_record_data.get("window_opened"),
                temperature=spot_record_data.get("temperature"),
                humidity=spot_record_data.get("humidity"),
                ac_power=spot_record_data.get("ac_power"),
                pm25=spot_record_data.get("pm25"),
                co2=spot_record_data.get("co2"))

            return spot_record
        return _make()

    @staticmethod
    def _make_location(location_data: PostData) -> Optional[Location]:
        # location must have a climate area.
        try:
            climate_area = (ClimateArea
                            .query
                            .filter_by(area_name=location_data["climate_area_name"])
                            .first())
        except Exception:
            raise

        location = Location(
            climate_area=climate_area,
            province=location_data["province"],
            city=location_data["city"])

        return location

    @staticmethod
    def _make_company(company_data: PostData) -> Optional[Company]:
        if not isinstance(company_data, PostData):
            return None
        return Company(company_name=company_data["company_name"])

    @staticmethod
    def _make_outdoor_spot(outdoor_spot_data: PostData) -> Optional[OutdoorSpot]:
        if not isinstance(outdoor_spot_data, PostData):
            return None

        return OutdoorSpot(
            outdoor_spot_id=outdoor_spot_data["outdoor_spot_id"],
            outdoor_spot_name=outdoor_spot_data["outdoor_spot_name"])


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
