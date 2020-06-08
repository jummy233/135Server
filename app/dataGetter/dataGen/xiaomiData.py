from flask import Flask
from multiprocessing import Process
from queue import Queue
from datetime import datetime as dt
from datetime import timedelta
from threading import RLock, Timer
from functools import partial
from itertools import chain, islice
from typing import (Any, Callable, Dict, Generator, Iterator, List, NewType,
                    Optional, Tuple, TypedDict, Union, cast)

from logger import make_logger

from .. import authConfig
from ..apis import xiaomiGetter as xGetter
from ..apis.xiaomiGetter import ResourceParam, DeviceData, ResourceData, ResourceDataTrimed, ResourceResponse
from ..dateSequence import DateSequence, date_sequence
from timeutils.time import date_range_iter, datetime_to_str, str_to_datetime, timestamp_setdigits
from .tokenManager import TokenManager
from .dataType import (Device, Location, Spot, SpotData,
                       SpotRecord, LazySpotRecord, WrongDidException,
                       device_check, DataSource, RecordGen, RecordThunkIter)

logger = make_logger('dataMidware', 'dataGetter_log')
logger.propagate = False


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
    expires_in: int = 5000 - 5  # token is valid for 30 min.

    def __init__(self, app: Flask):
        # get authcode and token
        self._app = app
        self.device_list: List = []
        self.auth: xGetter.AuthData = authConfig.xauth
        self.tokenManager = TokenManager(
            lambda: xGetter.get_token(self.auth),
            XiaoMiData.expires_in)

        self.tokenManager.start()

        self.refresh: Optional[str] = None
        self.make_device_list()

    def make_device_list(self):
        def query_device_amount() -> int:
            param: xGetter.DeviceParam = {
                'pageNum': 1,
                'pageSize': 1
            }
            response: Optional[xGetter.DeviceResult]
            response = xGetter.get_device(self.auth, self.token, param)
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

    def __del__(self):
        self.tokenManager.close()

    @property
    def normed_device_list(self) -> List:
        return list(map(MakeDict.make_device, self.device_list))

    @property
    def app(self):
        return self._app

    @property
    def token(self):
        return self.tokenManager.token

    def close(self):
        """ tear down """
        self.tokenManager.close()
        del self

    def spot_location(self) -> Optional[Generator]:
        raise NotImplementedError

    def spot_record(
            self,
            did: Optional[int] = None,
            daterange: Optional[Tuple[dt, dt]] = None) -> RecordThunkIter:
        """ get spot record based on device list """
        if not self.device_list:
            return iter([])
        sr = self._SpotRecord(self)
        dr: Tuple[dt, dt]
        dr = (dt.now() - timedelta(days=1), dt.now()) \
            if not daterange else daterange

        if did is None:
            generator = sr.all()
        else:
            generator = sr.one(did, dr)

        return generator

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
                dn = device_check(device.device_name, DataSource.XIAOMI)
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
            return self._gen([param])

        def all(self):
            """ for all devlce on device list """
            resource_params = self._mk_resource_parameter_iter()
            if self.device_list is None:
                return iter([])
            param_list = list(resource_params)
            return self._gen(param_list)

        def _gen(self, res_params: List[ResourceParam]) -> RecordThunkIter:
            """
            use map_thunk_iter() in dataType to access the return value.
            """

            def entrance(resources, params_list) -> RecordThunkIter:
                """ *** SIDE EFFECT """

                size = len(params_list)
                effectful = zip(resources, params_list)

                def g():
                    """ SIDE EFFECTFUL """
                    data, param = next(effectful)
                    return ((MakeDict.make_spot_record(record, param)
                             for record in trim_resource_data(data, param))
                            if data is not None
                            else iter([]))

                for _ in range(size):
                    yield g

            resources = map(self._resource, res_params)
            return entrance(resources, res_params)

        def _resource(self, resource_params) -> Optional[List[ResourceData]]:
            logger.debug('getting resource {}'.format(resource_params))

            with self.data.tokenManager.valid_token_ctx() as token:
                res: Optional[ResourceResponse] = xGetter.get_hist_resource(
                    self.auth, token, resource_params)
            return res['data'] if res is not None and 'data' in res else None

        def __mk_resource_parameter_iter(self):
            """ generate request parameter iter """
            if self.device_list is None:
                return None
            logger.info('[dataMidware] creating Xiaomi datapoint params')

            def param_gen():
                """
                param generator based on time sequence
                each Xiaopi api history query only support 300 item.
                Xiaomi records record per minute, so 300 items translate
                to 50 minutes.
                Each request advance by 50 minutes until it reach resigerTime
                of the device.
                """
                for d in self.device_list:
                    back50mins = date_range_iter(
                        str_to_datetime(d.get("registerTime")))
                    for date_tuple in back50mins:
                        param = (XiaoMiData
                                 ._SpotRecord
                                 ._make_resource_parameter(d, date_tuple))
                        if param is not None:
                            yield param

            resouce_param_iter = chain.from_iterable(param_gen())
            if not any(resouce_param_iter):
                logger.warning(XiaoMiData.source +
                               'No datapoint parameter.')
                return None
            return resouce_param_iter

        @staticmethod
        def _make_resource_parameter(
                device_result: Optional[xGetter.DeviceData],
                time_range: Tuple[dt, dt]) -> Optional[ResourceParam]:
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
                'pageSize': 300  # maxium 300
            }


class MakeDict:
    @staticmethod
    def make_location(device_result: xGetter.DeviceResult) -> Location:
        """ deprecated because the API is broken """
        raise NotImplementedError

    @staticmethod
    def make_device(device_result: xGetter.DeviceData) -> Optional[Device]:
        def convert_time(time: Optional[str]):
            result = None
            if time is not None:
                # note the time is in millisecond accuracy,
                # needs to convert to second to be compatible with
                # python datetime.
                result = dt.fromtimestamp(float(time) / 1000.0)
            return result
        create_time = convert_time(device_result.get('registerTime'))
        did = device_result.get('did')
        if did is None:
            return None
        return Device(location_info=None,
                      device_name=did,
                      online=device_result.get('state'),
                      device_type=device_result.get('model'),
                      create_time=create_time,
                      modify_time=None)

    @staticmethod
    def make_spot(location: Location) -> Spot:
        """ """
        raise NotImplementedError

    @staticmethod
    def make_spot_record(
        data: Optional[xGetter.ResourceDataTrimed],
            parms: Optional[xGetter.ResourceParam]) -> Optional[SpotRecord]:
        """
        format:
            { 'did': 'lumi.158d0001fd5c50',
               'attr': 'humidity_value',
               'value': '8354',
               'timeStamp': '1591393050203' }
        xiaomi record is based on value change. if change is smaller than a
        threshold there will be no data recorded, leave a time gap.

        The gap will be filled in later database clean phase.
        """
        if data is None:
            return None
        time_stamp = data.get('time_stamp')
        did = data.get('did')
        if time_stamp is None or did is None:
            return None

        time = dt.fromtimestamp(time_stamp / 1000.0)

        return SpotRecord(
            spot_record_time=time,
            device_name=did,
            pm25=None,
            co2=None,
            temperature=_XUnit.tempreture(data.get('temperature_value')),
            humidity=_XUnit.humidity(data.get('humidity_value')),
            ac_power=_XUnit.energy(data.get('cost_energy')),
            window_opened=_XUnit.winmag(data.get('magnet_status')))


class _XUnit:
    """
    Unit conversion utility. conform the database unit.
    """
    @staticmethod
    def to_int(val: Union[str, int, None]) -> Optional[int]:
        if isinstance(val, str):
            return int(val)
        return val

    @staticmethod
    def tempreture(tem_: Union[str, int, None]):
        """ C """
        tem = _XUnit.to_int(tem_)
        return tem / 10 if tem is not None else None

    @staticmethod
    def humidity(hum_: Union[str, int, None]):
        """ g/kg """
        hum = _XUnit.to_int(hum_)
        return hum / 10 if hum is not None else None

    @staticmethod
    def energy(en_: Union[str, int, None]):
        """ kwh """
        en = _XUnit.to_int(en_)
        return en * 1000 if en is not None else None

    @staticmethod
    def online(on_: Union[str, int, None]):
        """ bool """
        on = _XUnit.to_int(on_)
        return bool(on) if on is not None else None

    @staticmethod
    def winmag(mag_: Union[str, int, None]):
        """ bool """
        mag = _XUnit.to_int(mag_)
        return bool(mag) if mag is not None else None


def trim_resource_data(data: List[ResourceData], param: ResourceParam):
    """
    Note: each argument corresponds to one device,
    so did is the same across the entire list.

    turn a list of
        { 'did': 'lumi.158d0001fd5c50',
           'attr': 'humidity_value',
           'value': '8354',
           'timeStamp': 1591393050203 }
    to a list of
        {'time_stamp': 1591393050203,
         'temperature_value': 2739,
         'humidity_value': 8354,
         'cost_energy': None,
         'magnet_status': None }
    which each dictionary corresponds to one record from a device.
    """
    did = param.get('did')

    time_stamps = [
        t for d in data
        if (t := d.get('timeStamp'))
    ]

    time_dict: Dict[int, Dict] = {
        t:
        {d.get('attr'): d.get('value')
            for d in data if d.get('timeStamp') == t}
        for t in time_stamps if t is not None
    }

    return [{**v, 'time_stamp': int(k), 'did': did}
            for k, v in time_dict.items()]
