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
from ..dateSequence import DateSequence, date_sequence
from timeutils.time import back7daytuple_generator, datetime_to_str, str_to_datetime, timestamp_setdigits
from .tokenManager import TokenManager
from .dataType import (Device, Location, Spot, SpotData,
                       SpotRecord)

logger = make_logger('dataMidware', 'dataGetter_log')
logger.propagate = False

logger.addHandler

deviceResources: Dict = {
    'lumi.acpartner.v3': ["on_off_status", "cost_energy"],  # AC
    'lumi.gateway.aq1': [],  # ignore
    'lumi.plug.v1': ["plug_status", "cost_energy"],  # AC
    'lumi.sensor_ht.v1': ["humitidy_value", "temperature_value"],
    'lumi.sensor_magnet.v2': ["magnet_status"],
    'lumi.sensor_motion.v2': []  # ignore
}


def ResJSONParam(TypedDict):
    did: str
    attrs: List[str]


def mkResouceParam(
        device: xGetter.DeviceData,
        start: dt,
        end: dt,
        pn: int = 1,
        psz: int = 300) -> Dict:
    did = device.get('did')
    model = device.get('model')
    attrs = deviceResources.get(model)
    return {
        'did': did,
        'attrs': attrs,
        'startTime': str(timestamp_setdigits(start.timestamp(), 13)),
        'pageNum': pn,
        'pageSize': psz
    }


class XiaoMiData(SpotData):
    """
    Xiaomi data getter implementation
    """
    source: str = '<xiaomi>'
    expires_in: int = 5000  # token is valid in 20 seconds.

    def __init__(self, app: Flask):
        # get authcode and token
        self.app = app
        self.device_list: List = []
        self.auth: xGetter.AuthData = authConfig.xauth
        self.tokenManager = TokenManager(
            partial(xGetter._get_token, self.auth),
            XiaoMiData.expires_in)

        self.refresh: Optional[str] = None
        self._init_device_list()

    def _init_device_list(self):
        def query_device_amount() -> int:
            param: xGetter.DeviceParam = {
                'pageNum': 1,
                'pageSize': 1
            }
            response: Optional[xGetter.DeviceResult] = xGetter._get_device(
                self.auth, self.token, param)
            device_amount: int = response['totalCount'] if response else 0
            return device_amount
        device_amount = query_device_amount()
        if device_amount is not None and device_amount > 0:
            param: xGetter.DeviceParam = {
                'pageNum': 1,
                'pageSize': device_amount
            }
            response = xGetter._get_device(self.auth, self.token, param)
            response_result = response.get('data') if response else []
            device_list = response_result
        self.device_amount, self.device_list = device_amount, device_list

    @property
    def token(self):
        return self.tokenManager.token

    def spot_location(self) -> Optional[Generator]:
        ...

    def spot_record(self) -> Iterator[Callable[[], Optional[Generator]]]:
        ...

    def device(self) -> Optional[Generator]:
        if not self.device_list:
            return None
        return (self.make_device(d) for d in self.device_list)

    def spot(self) -> Optional[Generator]:
        ...

    def rt_spot_record(self) -> Optional[Generator]:
        ...

    @staticmethod
    def make_location(device_result: xGetter.DeviceResult) -> Location:
        ...

    @staticmethod
    def make_device(device_result: xGetter.DeviceResult) -> Device:
        ...

    @staticmethod
    def make_spot(location: Location) -> Spot:
        ...

    @staticmethod
    def make_spot_record(data: xGetter.ResourceData) -> SpotRecord:
        ...