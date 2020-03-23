from multiprocessing import Process
from queue import Queue
from threading import RLock, Timer
from typing import (Any, Callable, Dict, Generator, Iterator, List, NewType,
                    Optional, Tuple, TypedDict, Union, cast)

from logger import make_logger

from .. import authConfig
from ..apis import xiaomiGetter as xGetter
from ..dateSequence import DateSequence, date_sequence
from timeutils.time import back7daytuple_generator, datetime_to_str, str_to_datetime
from .dataType import (Device, Location, RealTimeSpotData, Spot, SpotData,
                       SpotRecord)

logger = make_logger('dataMidware', 'dataGetter_log')
logger.propagate = False

logger.addHandler


class XiaoMiData(SpotData, RealTimeSpotData):
    """
    Xiaomi data getter implementation
    """
    source: str = '<xiaomi>'
    expires_in: int = 5000  # token is valid in 20 seconds.

    def __init__(self):
        # get authcode and token
        self.auth: xGetter.AuthData = authConfig.xauth
        self.token: Optional[xGetter.TokenResult] = xGetter._get_token(self.auth)
        self.refresh: Optional[str] = None
        self.rlock = RLock()

        if not self.token:
            logger.critical('%s %s', self.source, Spot.token_fetch_error_msg)
            raise ConnectionError(self.source, Spot.token_fetch_error_msg)

        def _refresh_token():  # token will expire. So need to be refreshed periodcially.
            def worker(q: Queue):
                with self.rlock:
                    setattr(q.get(),
                            'token', xGetter._get_token(self.auth, self.token))

            q: Queue = Queue()
            # refresh token in another process and pause the current one.
            token_worker = Process(target=worker, args=(q,))

            token_worker.start()
            token_worker.join()
            token_worker.close()

            if not self.token:
                logger.critical('%s %s', self.source, Spot.token_fetch_error_msg)
                raise ConnectionError(self.source, Spot.token_fetch_error_msg)

        def init_device_list(device_list) -> Optional[Tuple[int, List[xGetter.DeviceResult]]]:

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

            return device_amount, device_list

            # reset timer.
            self.timer = Timer(XiaoMiData.expires_in - 5, _refresh_token)
            self.timer.start()

        self.timer = Timer(XiaoMiData.expires_in - 5, _refresh_token)
        self.timer.start()

        # init device list
        self.device_list: List = []
        dev_list_result = init_device_list(self.device_list)
        self.device_amount, self.device_list = dev_list_result if dev_list_result else None

    def spot_location(self) -> Optional[Generator]:
        ...

    def spot_record(self) -> Iterator[Callable[[], Optional[Generator]]]:
        ...

    def device(self) -> Optional[Generator]:
        if not self.device_list:
            return None
        return (self.make_device(d) for d in self.device_list)
    # TODO make deivce 2020-01-15 after philosophy class.

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
