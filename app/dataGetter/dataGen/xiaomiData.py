from flask import Flask
from multiprocessing import Process
from queue import Queue
from datetime import datetime as dt
from threading import RLock, Timer
from functools import partial
from typing import (Any, Callable, Dict, Generator, Iterator, List, NewType,
                    Optional, Tuple, TypedDict, Union, cast)

from logger import make_logger

from .. import authConfig
from ..apis import xiaomiGetter as xGetter
from ..apis.xiaomiGetter import OneResourceParam, DeviceData
from ..dateSequence import DateSequence, date_sequence
from timeutils.time import back7daytuple_generator, datetime_to_str, str_to_datetime, timestamp_setdigits
from .tokenManager import TokenManager
from .dataType import (Device, Location, Spot, SpotData,
                       SpotRecord, LazySpotRecord, WrongDidException,
                       did_check, DataSource)

logger = make_logger('dataMidware', 'dataGetter_log')
logger.propagate = False

logger.addHandler

"""
some of the device models are ignored. Largely because the are
just gateway for gathering data from its child devices.
"""
deviceModels: Dict = {
    'lumi.acpartner.v3': ["on_off_status", "cost_energy"],  # AC
    'lumi.gateway.aq1': [],                                 # ignore
    'lumi.plug.v1': ["plug_status", "cost_energy"],         # AC
    'lumi.sensor_ht.v1': ["humitidy_value", "temperature_value"],
    'lumi.sensor_magnet.v2': ["magnet_status"],
    'lumi.sensor_motion.v2': []                             # ignore
}


class XiaoMiData(SpotData):
    """
    Xiaomi data getter implementation
    Location related interface are not implemented. It only serves to record
    device and spot records.
    """
    source: str = '<xiaomi>'
    expires_in: int = 5000  # token is valid in 20 seconds.

    def __init__(self, app: Flask):
        # get authcode and token
        self.app = app
        self.device_list: List = []
        self.auth: xGetter.AuthData = authConfig.xauth
        self.tokenManager = TokenManager(
            lambda: xGetter.get_token(self.auth),
            XiaoMiData.expires_in)

        self.refresh: Optional[str] = None
        self._init_device_list()

    def _init_device_list(self):
        def query_device_amount() -> int:
            param: xGetter.DeviceParam = {
                'pageNum': 1,
                'pageSize': 1
            }
            response: Optional[xGetter.DeviceResult] = xGetter.get_device(
                self.auth, self.token, param)
            device_amount: int = response['totalCount'] if response else 0
            return device_amount
        device_amount = query_device_amount()
        if device_amount is not None and device_amount > 0:
            param: xGetter.DeviceParam = {
                'pageNum': 1,
                'pageSize': device_amount
            }
            response = xGetter.get_device(self.auth, self.token, param)
            response_result = response.get('data') if response else []
            device_list = response_result
        self.device_amount, self.device_list = device_amount, device_list

    @property
    def token(self):
        return self.tokenManager.token

    def spot_location(self) -> Optional[Generator]:
        raise NotImplementedError

    def spot_record(
            self,
            did: Optional[int] = None) -> Iterator[LazySpotRecord]:
        """ get spot record based on device list """
        if not self.device_list:
            return iter([])
        ...

    def device(self) -> Optional[Generator]:
        if not self.device_list:
            return None
        return (MakeDict.make_device(d) for d in self.device_list)

    def spot(self) -> Optional[Generator]:
        raise NotImplementedError

    class _SpotRecord:
        """
        Handle spotrecord
        """

        def __init__(self, data: 'XiaoMiData'):
            self.data = data

        @property
        def device_list(self):
            return self.data.device_list

        @property
        def token(self):
            return self.data.token

        @property
        def auth(self):
            return self.data.auth

        def one(self, did: int, daterange: Tuple[dt, dt]):
            """ for one device """
            try:
                with self.data.app.app_context():
                    from app.models import Device as MD
                    device = (MD.query.
                              filter(MD.device_id == did).first())
                dn = did_check(device.device_name, DataSource.XIAOMI)
            except AttributeError:
                logger.warning('[XiaomiData] fetch spot_record failed, '
                               + 'device not in database')
                return iter([])
            except WrongDidException:
                logger.warning('[XiaomiData] fetch spot_record failed, '
                               + 'device not in database')
                return iter([])
            device_res = [d for d in self.device_list
                          if d.get('did') == dn].pop()

            param = self._make_resource_parameter(device_res, daterange)
            if param is None:
                return iter([])

            # TODO return the generator
            return ...

        def all(self):
            """ for all devlce on device list """
            resource_params = self._resource_parameter_iter()
            if self.device_list is None:
                return iter([])
            param_list = list(resource_params)

            # TODO return the generator
            return ...

        def _gen(self, resource_params):
            """ top level generator """
            RecordThunk = Generator[
                Callable[
                    [], Optional[Generator[Optional[SpotRecord], None, None]]],
                None,
                None]
            def entrance(resources, params_list) -> RecordThunk:
                ...

        def _resource_parameter_iter(self):
            """ generate request parameter iter """
            if self.device_list is None:
                return None
            logger.info('[dataMidware] creating Xiaomi datapoint params')
            for device in self.device_list:
                yield self._make_resource_parameter(device, )

        @staticmethod
        def _make_resource_parameter(
            device_result: Optional[xGetter.DeviceData],
            time_range: Tuple[dt, dt]) \
                -> Optional[OneResourceParam]:
            """ Make resource parameter for given time range.

            @param device_result:  the list of device
            @param time_range:     For xiaomi the time range is necessary.

            @return:               An optional resource query parameter.
                                   If it is None the caller will omit the
                                   query.
            """
            if not device_result:
                logger.error("no device result")
                return None
            start, end = tuple(map(
                lambda t:
                str(timestamp_setdigits(dt.timestamp(t), 13)), time_range))

            did = device_result.get('did')
            model = device_result.get('model')
            attrs = deviceModels.get(model)
            if did is None or attrs is None:
                return None
            return {
                'did': did,
                'attrs': attrs,
                'startTime': start,
                'endTime': end,
                'pageNum': 1,
                'pageSize': 300
            }


class MakeDict:
    @staticmethod
    def make_location(device_result: xGetter.DeviceResult) -> Location:
        """ deprecated because the API is broken """
        raise NotImplementedError

    @staticmethod
    def make_device(device_result: xGetter.DeviceData) -> Device:
        """ """
        def convert_time(time: Optional[str]):
            result = None
            if time is not None:
                result = dt.fromtimestamp(float(time))
            return result
        create_time = convert_time(device_result.get('registerTime'))
        return Device(location_info=None,
                      device_name=device_result.get('did'),
                      online=device_result.get('state'),
                      device_type=device_result.get('model'),
                      create_time=create_time,
                      modify_time=None)

    @staticmethod
    def make_spot(location: Location) -> Spot:
        """ """
        raise NotImplementedError

    @staticmethod
    def make_spot_record(data: xGetter.ResourceData) -> SpotRecord:
        ...
