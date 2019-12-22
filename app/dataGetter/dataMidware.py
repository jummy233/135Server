from threading import Timer
from typing import NewType, Dict, Optional, Tuple, List, Generator, NamedTuple
from abc import ABC, abstractmethod
from collections import namedtuple
from sys import maxsize
from datetime import datetime as dt
from operator import itemgetter
import xiaomiGetter as xGetter
import jianyanyuanGetter as jGetter
import authConfig
import pysnooper
from utils import str_to_datetime, datetime_to_str
import logging
from dateSequence import DateSequence, date_sequence


class Spot(NamedTuple):
    project_id: int
    spot_name: str


class SpotRecord(NamedTuple):
    spot_id: int
    spot_record_time: dt
    temperature: float
    humidity: float
    window_opened: bool
    ac_power: float
    pm25: int
    co2: int


class Device(NamedTuple):
    spot_id: int
    device_name: str


class SpotData(ABC):
    """
    Common interface for spot data from different sources.
    """
    token_fetch_error_msg: str = 'Token fetch Error: Token Error'
    datetime_time_eror_msg: str = 'Datetime error: Incorrect datetime'

    @abstractmethod
    def spot_location(self) -> Generator[Spot, None, None]:
        """
        Get spot location information.
        It returns a generator of the list of spot location information
        value returned are used to fill `spot` table in database schema.
        """

    @abstractmethod
    def spot_record(self) -> Generator[SpotRecord, dt, str]:
        """
        Get spot record data include temperature, humidity pm2.5 etc.
        value returned are used to fill `spot_record` table in database schema.
        """

    @abstractmethod
    def device(self) -> Generator[Device, None, None]:
        """
        Get device information
        value returned will be used to fill `device` table in database schema.
        """


class RealTimeSpotData(ABC):
    token_fetch_error_msg: str = 'Token fetch Error: Xiaomi Token Error, didn\'t refresh token'
    datetime_time_eror_msg: str = 'Datetime error: Incorrect datetime'

    @abstractmethod
    def rt_spot_record(self) -> Generator[SpotRecord, dt, str]:
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
            self.token = xGetter._get_token(self.auth, self.refresh)
            if not self.token:
                logging.critical('%s %s', self.source, Spot.token_fetch_error_msg)
                raise ConnectionError(self.source, Spot.token_fetch_error_msg)

            # reset timer.
            self.timer = Timer(self.token['expires_in'] - 200, _refresh_token)
            self.timer.start()
        self.timer = Timer(self.token['expires_in'] - 200, _refresh_token)  # spin timer.
        self.timer.start()

    def spot_location(self) -> Generator[Spot, None, None]:
        pass

    def spot_record(self) -> Generator[SpotRecord, dt, str]:
        pass

    def device(self) -> Generator[Device, None, None]:
        pass

    def _query_device(self, params: jGetter.DeviceParam):
        pass

    def rt_spot_record(self):
        pass


class JianYanYuanData(SpotData, RealTimeSpotData):
    """
    Jianyanyuan data getter implementation
    """
    source: str = '<jianyanyuan>'
    expire_in: int = 20  # token is valid in 20 seconds.
    indoor_data_collector_pid: str = '001'
    monitor_pid: str = '003'

    def __init__(self, datetime_range: Optional[Tuple[dt, dt]] = None):
        self.auth: jGetter.AuthData = authConfig.jauth
        self.token: Optional[jGetter.AuthToken] = jGetter._get_token(self.auth)

        if datetime_range is not None:  # data within this date will be collected.
            self.startAt, self.endWith = datetime_range

        if not self.token:
            logging.critical('%s %s', self.source, SpotData.token_fetch_error_msg)
            raise ConnectionError(self.source, SpotData.token_fetch_error_msg)

        def _refresh_token():
            self.token = jGetter._get_token(self.auth)
            if not self.token:
                logging.critical('%s %s', self.source, Spot.token_fetch_error_msg)
                raise ConnectionError(self.source, Spot.token_fetch_error_msg)

            self.timer = Timer(JianYanYuanData.expire_in - 5, _refresh_token)
            self.timer.start()

        self.timer = Timer(JianYanYuanData.expire_in - 5, _refresh_token)
        self.timer.start()

    def spot_location(self) -> Generator[Spot, None, None]:
        pass

    def spot_record(self) -> Generator[SpotRecord, dt, str]:
        pass

    def device(self) -> Generator[Device, None, None]:
        pass

    def rt_spot_record(self):
        pass

    def _make_datapoint_param(self,
                              dev_result: jGetter.DeviceResult,
                              time_range: Optional[Tuple[str, str]] = None
                              ) -> Optional[jGetter.DataPointParam]:
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
        if not dev_result:
            return None

        (gid,
         did,
         productId,
         createTime) = itemgetter('gid',
                                  'deviceId',
                                  'productId',
                                  'createTime')(dev_result)

        # Don't need get attrs since we already know what to get,
        # attrs: Optional[List[jGetter.AttrResult]] = (
        #     jGetter._get_device_attrs(self.auth, self.token, gid))

        if not time_range:
            startTime: str = createTime
            endTime: str = datetime_to_str(dt.utcnow())
        # check if datetimes are valid
        else:
            startTime, endTime = time_range
            if str_to_datetime(startTime) < str_to_datetime(createTime):
                raise ValueError(self.source, SpotData.datetime_time_eror_msg, startTime, createTime)
            if str_to_datetime(endTime) > dt.utcnow():
                raise ValueError(self.source, SpotData.datetime_time_eror_msg, endTime)

        # set attr id
        # Here ignored all haier devices.
        def _get_aid() -> str:
            if productId == JianYanYuanData.indoor_data_collector_pid:
                return '{},{},{},{}'.format(jGetter.attrs['pm25'],
                                            jGetter.attrs['co2'],
                                            jGetter.attrs['temperature'],
                                            jGetter.attrs['humidity'])
            if productId == JianYanYuanData.monitor_pid:
                return jGetter.attrs['ac_power']
            return ''
        aid: str = _get_aid()

        datapoint_params: Optional[jGetter.DataPointParam] = (
            jGetter.DataPointParam(gid=gid,
                                   did=did,
                                   aid=aid,
                                   startTime=startTime,
                                   endTime=endTime))
        return datapoint_params


# TODO Outdoor data
class OutdoorData:
    pass


# TODO Project Data got input from json file.
class ProjectData:
    pass
