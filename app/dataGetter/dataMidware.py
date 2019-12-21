from threading import Timer
from typing import NewType, Dict, Optional, Tuple, List, Generator, NamedTuple
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime as dt
import xiaomiGetter as xGetter
import jianyanyuanGetter as jGetter
import authConfig


class Spot(NamedTuple):
    project_id: int
    spot_name: str


class SpotRecord(NamedTuple):
    spot_id: int
    spot_record_time: dt
    temperature: float
    humidity: float
    window_opened: bool
    pm25: int
    co2: int


class Device(NamedTuple):
    spot_id: int
    device_name: str


class SpotData(ABC):

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


class XiaoMiData(SpotData):
    """ Xiaomi data getter implementation """
    token_fetch_error_msg: str = 'Token fetch Error: Xiaomi Token Error, didn\'t refresh token'

    def __init__(self):
        # get authcode and token
        self.auth: xGetter.AuthData = authConfig.xauth
        self.token: Optional[xGetter.TokenResult] = xGetter._get_token(self.auth)
        self.refresh: Optional[str] = None
        if not self.token:
            raise ConnectionError(XiaoMiData.token_fetch_error_msg)

        def _refresh_token():  # token will expire. So need to be refreshed periodcially.
            self.refresh = self.token['refresh_token']
            self.token = xGetter._get_token(self.auth, self.refresh)
            if not self.token:
                raise ConnectionError(XiaoMiData.token_fetch_error_msg)

            del self.time  # reset the timer
            self.timer = Timer(self.token['expires_in'] - 200, _refresh_token)
            self.timer.start()
        self.timer = Timer(self.token['expires_in'] - 200, _refresh_token)  # spin timer.
        self.timer.start()

    def spot_location(self):
        pass

    def spot_record(self):
        pass

    def device(self):
        pass


class JianYanYuanData(SpotData):
    """ Jianyanyuan data getter implementation """
    def spot_location(self):
        pass

    def spot_record(self):
        pass

    def device(self):
        pass


