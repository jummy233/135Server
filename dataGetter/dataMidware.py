from threading import Timer
from multiprocessing import Process
from queue import Queue
import time
from typing import (
    NewType, Dict, Optional, Tuple, List, Generator,
    TypedDict, Iterator, Callable, cast, Union)
from abc import ABC, abstractmethod
from collections import namedtuple
from sys import maxsize
from datetime import datetime as dt
from datetime import timedelta
from operator import itemgetter
import logging
from functools import partial
from itertools import tee

from dataGetter import xiaomiGetter as xGetter
from dataGetter import jianyanyuanGetter as jGetter
from dataGetter.jianyanyuanGetter import (
    DataPointParam as JdatapointParam,
    DataPointResult as JdatapointResult,
    DeviceParam as JdevParam,
    DeviceResult as JdevResult)
from dataGetter import authConfig
from dataGetter.utils import str_to_datetime, datetime_to_str
from dataGetter.dateSequence import DateSequence, date_sequence
from app.models import Project


######################################
#  These are intermidiate data       #
#   structrues!!                     #
#  Datatype returned by midware.     #
#  These data will be further piped  #
#  into DBRecorder module to finally #
#  into db.                          #
######################################

class Location(TypedDict):
    province: Optional[str]
    city: Optional[str]
    address: Optional[str]
    extra: Optional[str]    # extra useful informatino to determine spot


class Spot(TypedDict):
    """ Spot is generate from location """
    project_name: Optional[str]
    spot_name: Optional[str]
    spot_type: Optional[str]


class SpotRecord(TypedDict):
    device_name: Optional[str]
    spot_record_time: Optional[dt]
    temperature: Optional[float]
    humidity: Optional[float]
    pm25: Optional[float]
    co2: Optional[float]
    window_opened: Optional[bool]
    ac_power: Optional[float]


class Device(TypedDict):
    location_info: Optional[Location]  # Location info help to deduce the spot.
    device_name: Optional[str]
    device_type: Optional[str]
    online: Union[int, bool, None]
    create_time: Optional[dt]
    modify_time: Optional[dt]


class SpotData(ABC):
    """
    A Factory
    Common interface for spot data from different sources.
    """
    token_fetch_error_msg: str = 'Token fetch Error: Token Error'
    datetime_time_eror_msg: str = 'Datetime error: Incorrect datetime'

    @abstractmethod
    def spot(self) -> Optional[Generator]:
        """
        Get spot location information.
        It returns a generator of the list of spot location information
        value returned are used to fill `spot` table in database schema.
        """

    @abstractmethod
    def spot_record(self) -> Iterator[Optional[Generator]]:
        """
        Get spot record data include temperature, humidity pm2.5 etc.
        value returned are used to fill `spot_record` table in database schema.
        """

    @abstractmethod
    def device(self) -> Optional[Generator]:
        """
        Get device information
        value returned will be used to fill `device` table in database schema.
        """


class RealTimeSpotData(ABC):
    """ RealTime mixin """
    token_fetch_error_msg: str = 'Token fetch Error: Xiaomi Token Error, didn\'t refresh token'
    datetime_time_eror_msg: str = 'Datetime error: Incorrect datetime'

    @abstractmethod
    def rt_spot_record(self) -> Optional[Generator[Optional[SpotRecord], dt, str]]:
        """
        Get spot record data include temperature, humidity pm2.5 etc in real time.
        value returned are used to fill `spot_record` table in database schema.
        """


class XiaoMiData(SpotData, RealTimeSpotData):
    """
    Xiaomi data getter implementation
    """
    source: str = '<xiaomi>'

    def __init__(self):
        # get authcode and token
        self.auth: xGetter.AuthData = authConfig.xauth
        self.token: Optional[xGetter.TokenResult] = xGetter._get_token(self.auth)
        self.refresh: Optional[str] = None
        if not self.token:
            logging.critical('%s %s', self.source, Spot.token_fetch_error_msg)
            raise ConnectionError(self.source, Spot.token_fetch_error_msg)

        def _refresh_token():  # token will expire. So need to be refreshed periodcially.
            self.refresh = self.token['refresh_token']

            token_worker = Process(  # refresh token in another process and pause the current one.
                target=lambda o: (
                    setattr(o,
                            'token',
                            xGetter._get_token(self.auth, self.refresh))), args=(self))
            token_worker.start()
            token_worker.join()

            if not self.token:
                logging.critical('%s %s', self.source, Spot.token_fetch_error_msg)
                raise ConnectionError(self.source, Spot.token_fetch_error_msg)

            # reset timer.
            self.timer = Timer(self.token['expires_in'] - 200, _refresh_token)
            self.timer.start()
        self.timer = Timer(self.token['expires_in'] - 200, _refresh_token)  # spin timer.
        self.timer.start()

    def spot_location(self) -> Optional[Generator]:
        pass

    def spot_record(self, spot_id: Optional[int] = None) -> Iterator[Optional[Generator]]:
        pass

    def device(self) -> Optional[Generator]:
        pass

    def spot(self) -> Optional[Generator]:
        pass

    def rt_spot_record(self) -> Optional[Generator]:
        pass


class JianYanYuanData(SpotData, RealTimeSpotData):
    """
    Jianyanyuan data getter implementation
    """
    source: str = '<jianyanyuan>'
    expires_in: int = 20  # token is valid in 20 seconds.
    indoor_data_collector_pid: str = '001'
    monitor_pid: str = '003'

    size: int = 300
    device_params: JdevParam = {  # prepare device parameter.
        'companyId': 'HKZ',
        'start': 1,
        'size': size,
        'pageNo': 1,
        'pageSize': size  # @2020-01-06 could be str.
    }

    def __init__(self, datetime_range: Optional[Tuple[dt, dt]] = None):
        self.auth = authConfig.jauth
        self.token = jGetter._get_token(self.auth)

        if datetime_range is not None:  # data within this date will be collected.

            self.startAt, self.endWith = datetime_range

        if not self.token:

            logging.critical('%s %s', self.source, SpotData.token_fetch_error_msg)
            raise ConnectionError(self.source, SpotData.token_fetch_error_msg)

        def _refresh_token():  # token will expire. So need to be refreshed periodcially.

            q: Queue = Queue()
            token_worker = Process(  # refresh token in another process and pause the current one.
                target=lambda q: (
                    setattr(q.get(),
                            'token',
                            jGetter._get_token(self.auth))), args=(q,))
            token_worker.start()
            token_worker.join()
            token_worker.close()

            if not self.token:
                logging.critical('%s %s', self.source, Spot.token_fetch_error_msg)
                raise ConnectionError(self.source, Spot.token_fetch_error_msg)

            # reset timer.
            self.timer = Timer(JianYanYuanData.expires_in - 5, _refresh_token)
            self.timer.start()
            self.timer.join()

        self.timer = Timer(JianYanYuanData.expires_in - 5, _refresh_token)
        self.timer.start()

        # common states
        self.device_list = jGetter._get_device_list(
            self.auth, self.token, cast(Dict, JianYanYuanData.device_params))

    def close(self):
        """ tear down """
        if self.timer.is_alive():
            self.timer.cancel()
        del self

    def spot(self) -> Optional[Generator]:
        """ return spot generator """
        if not self.device_list:
            return None

        return (self.make_spot(self.make_location(d)) for d in self.device_list)

    def spot_record(self) -> Iterator[Optional[Generator]]:
        """
        Return  Generator of SpotRecord of a specific Spot
        """
        if not self.device_list:
            return iter([])

        datapoint_params: Iterator[Optional[JdatapointParam]] = (
            map(JianYanYuanData._make_datapoint_param,
                self.device_list))
        datapoint_params1, datapoint_params2 = tee(datapoint_params)

        datapoints: Iterator[
            Optional[List[
                JdatapointResult]]] = (
            map(self._datapoint, datapoint_params1))

        spot_records = (
            map(lambda dp: (None if dp[0] is None else
                            (JianYanYuanData.make_spot_record(sr, dp[1]) for sr in dp[0])),
                zip(datapoints, datapoint_params2)))

        if not any(spot_records):
            return iter([])

        return spot_records

    def device(self) -> Optional[Generator]:
        if not self.device_list:
            return None
        return (self.make_device(d) for d in self.device_list)

    ####################################
    #  spot_location helper functions  #
    ####################################

    @staticmethod
    def _filter_location_attrs(device_result: JdevResult,
                               location_attrs: Dict) -> Dict:
        """
        filter location attributes from device results
        """
        return {k: v for k, v
                in device_result.items()
                if k in location_attrs}

    ##################################
    #  spot_record helper functions  #
    ##################################

    def _datapoint_param_iter(self) -> Optional[Iterator]:
        """
        datapoint paramter generator. Each paramter for each device.
        """
        if self.device_list is None:
            return None

        datapoint_param_iter: Iterator = (
            JianYanYuanData._make_datapoint_param(p)
            for p
            in self.device_list)

        if not any(datapoint_param_iter):

            logging.warning(JianYanYuanData.source + 'No datapoint parameter.')
            return None

        return datapoint_param_iter

    def _datapoint(self,
                   datapoint_param: Optional[JdatapointParam]
                   ) -> Optional[List[JdatapointResult]]:
        if not datapoint_param:
            return None
        return jGetter._get_data_points(self.auth, self.token, datapoint_param)

    def datapoint_iter(self,
                       datapoint_param_iter: Optional[Iterator]
                       ) -> Optional[Iterator
                                     [Optional
                                      [List[JdatapointResult]]]]:
        """ datapoint data generator. Is a iterator of list.  """

        if datapoint_param_iter is None:
            logging.error('empty datapoint_param_iter')
            return None

        datapoint_iter = (
            self._datapoint(param)
            for param
            in datapoint_param_iter)

        if not any(datapoint_iter):
            logging.warning(JianYanYuanData.source + 'No datapoint list.')
            return None

        return datapoint_iter

    @staticmethod
    def _make_datapoint_param(device_result: JdevResult,
                              time_range: Optional[Tuple[dt, dt]] = None
                              ) -> Optional[JdatapointParam]:
        """
        make query parameter datapoint query.
        DataPoint query parameter format:
            gid: str
            did: str
            aid: int
            startTime: str, yyyy-MM-ddTHH:mm:ss
            endTime: str, yyyy-MM-ddTHH:mm:ss

        modelName, prodcutId for devices: 'ESIC-SN\\d{2,2}',     '001', indoor data
                                          'ESIC-DTU-RB-RF06-2G', '003', AC power
        """
        if not device_result:
            logging.error('no device result')
            return None

        gid = device_result.get('gid')
        did = device_result.get('deviceId')
        createTime = str_to_datetime(device_result.get('createTime'))
        modifyTime = str_to_datetime(device_result.get('modifyTime'))

        def get_aid() -> str:
            return '1,2,3,4,32,155'

        if not time_range:
            startTime: Optional[dt] = createTime
            endTime: Optional[dt] = (modifyTime if modifyTime
                                     else dt.utcnow() - timedelta(hours=1))  # 1 hour gap avoid bug.
        # check if datetimes are valid

        else:
            startTime, endTime = time_range

            # handle impossible date.
            if createTime and startTime < createTime:
                startTime = createTime

            if endTime > dt.utcnow():
                endTime = (modifyTime if modifyTime
                           else dt.utcnow() - timedelta(hours=1))

        datapoint_params: JdatapointParam = (
            JdatapointParam(
                gid=gid,
                did=did,
                aid=get_aid(),
                startTime=datetime_to_str(startTime),
                endTime=datetime_to_str(endTime)))

        return datapoint_params

    ######################
    #  Real time         #
    ######################

    def rt_spot_record(self):
        pass

    ########################################
    # Convert json result into TypedDict   #
    ########################################

    @staticmethod
    def make_location(device_result: JdevResult) -> Location:
        """
        return location in standard format
        location will be used to make Spot and device info.
        """

        # define utils.
        location_attrs: Tuple[str, ...] = (
            'cityIdLogin', 'provinceIdLogin', 'nickname', 'address',
            'provinceLoginName', 'cityLoginName', 'location')

        # filter location attributes from device result lists.
        make_attrs: Callable = partial(
            JianYanYuanData._filter_location_attrs,
            location_attrs=location_attrs)

        # attrses: Iterator = map(make_attrs, self.device_list)

        # make_spot = JianYanYuanData.make_spot
        # return (make_spot(attrs) for attrs in attrses)
        location = make_attrs(device_result)
        return Location(province=location.get('provinceLoginName'),
                        city=location.get('cityLoginName'),
                        address=location.get('address'),
                        extra=location.get('nickname'))

    @staticmethod
    def make_spot_record(datapoint: Optional[JdatapointResult],
                         datapoint_param: Optional[JdatapointParam]
                         ) -> Optional[SpotRecord]:
        """ construct `SpotRecord` from given datapoint_params """

        if datapoint is None:
            logging.error('datapoint is empty')
            return None

        aS: Optional[Dict] = datapoint.get('as')

        if aS is None:
            logging.error('datapoint `as` record is empty')
            return None

        key: Optional[str] = datapoint.get('key')
        if key is None:
            logging.error('datapoint `key` record is empty')
            return None

        spot_record_time = str_to_datetime(key)

        pm25: Optional[float] = aS.get(jGetter.attrs['pm25'])
        co2: Optional[float] = aS.get(jGetter.attrs['co2'])
        temperature: Optional[float] = aS.get(jGetter.attrs['temperature'])
        humidity: Optional[float] = aS.get(jGetter.attrs['humidity'])

        ac_power: Optional[float] = aS.get(jGetter.attrs['ac_power1'])
        if ac_power is None:
            ac_power = aS.get(jGetter.attrs['ac_power2'])

        # device_name is did of JianYanYuanData
        # each device will be granted with a new id, so did becomes the name.
        device_name: Optional[str] = None
        if datapoint_param:
            device_name = datapoint_param.get('did')

        return SpotRecord(spot_record_time=spot_record_time,
                          device_name=device_name,
                          temperature=temperature,
                          humidity=humidity,
                          pm25=pm25,
                          co2=co2,
                          window_opened=None,
                          ac_power=ac_power)

    @staticmethod
    def make_spot(loc_attrs: Location) -> Optional[Spot]:
        """
        Spot for jianyanyuan is based on project.
        there are no room information.

        This method return the location dict, and
        will be used to deduce the project a given device is in.

        then db will create a unique separate spot corresponding
        to the unique project.
        """
        # TODO: pick the most suitable infor from locatino attrs 2019-12-23 @1
        # Location need to match with project.
        # So this function need to be implemented with project information.

        return Spot(project_name=loc_attrs.get('address'),
                    spot_name=None,
                    spot_type=None)

    @staticmethod
    def make_device(device_result: JdevResult) -> Device:
        return Device(location_info=JianYanYuanData.make_location(device_result),
                      device_name=device_result.get('deviceId'),
                      online=device_result.get('online'),
                      device_type=device_result.get('productName'),
                      create_time=device_result.get('createTime'),
                      modify_time=device_result.get('modifyTime'))


# TODO Outdoor data
class OutdoorData:
    pass


