
"""
These are intermidiate data structrues Datatype returned by midware.
These data will be further piped into DBRecorder module to finally into db.
"""

from flask import Flask
from datetime import datetime as dt
from datetime import timedelta
from functools import partial
from itertools import chain, islice
from typing import (Any, Callable, Dict, Generator, Iterator, List, NewType,
                    Optional, Tuple, TypedDict, Union, cast)

from logger import make_logger
from timeutils.time import (back7daytuple_generator, datetime_to_str,
                            str_to_datetime)

from timeutils.time import currentTimestamp
from app.dataGetter import authConfig
from app.dataGetter.apis import jianyanyuanGetter as jGetter
from app.dataGetter.apis.jianyanyuanGetter import DataPointParam as JdatapointParam
from app.dataGetter.apis.jianyanyuanGetter import DataPointResult as JdatapointResult
from app.dataGetter.apis.jianyanyuanGetter import DeviceParam as JdevParam
from app.dataGetter.apis.jianyanyuanGetter import DeviceResult as JdevResult
from app.dataGetter.dataGen.dataType import Device, Location, Spot, SpotData, SpotRecord, LazySpotRecord, WrongDidException, did_check, DataSource
from .tokenManager import TokenManager

logger = make_logger('dataMidware', 'dataGetter_log')
logger.propagate = False
logger.addHandler

"""
RecordGen:      Generator contains data from one request.
RecordThunk:    Unevaled record data.
RecordThunkGen: Generator of multiple RecordThunk s.
"""
RecordGen = Generator[Optional[SpotRecord], None, None]
RecordThunk = Callable[[], Optional[RecordGen]]
RecordThunkGen = Generator[RecordThunk, None, None]


class JianYanYuanData(SpotData):
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

    def __init__(self, app: Flask,
                 datetime_range: Optional[Tuple[dt, dt]] = None):
        logger.info('init JianYanYuanData')
        self.app = app
        self.auth = authConfig.jauth
        self.tokenManager = TokenManager(
            lambda: jGetter.get_token(self.auth, currentTimestamp(digit=13)),
            JianYanYuanData.expires_in)
        self.tokenManager.start()

        # data within this date will be collected.
        if datetime_range is not None:
            self.datetime_range = datetime_range

        if not self.tokenManager.token:
            logger.critical('%s %s', self.source,
                            SpotData.token_fetch_error_msg)
            raise ConnectionError(self.source, SpotData.token_fetch_error_msg)

        # common states
        self.device_list = jGetter.get_device_list(
            self.auth, self.token, cast(Dict, JianYanYuanData.device_params))

    @property
    def token(self):
        return self.tokenManager.token

    def close(self):
        """ tear down """
        self.tokenManager.close()
        del self

    def spot(self) -> Optional[Generator]:
        """ return spot generator """
        if not self.device_list:
            return None

        return (MakeDict.make_spot(MakeDict.make_location(d))
                for d in self.device_list)

    def spot_record(
            self,
            did: Optional[int] = None,
            daterange: Optional[Tuple[dt, dt]] = None) \
            -> Iterator[LazySpotRecord]:
        """
        By defualt spot_record() generate all data.
        spot_record(did) generate data for device did in the same day.
        the date range can be changed by pass a datetime tuple.

        @param did:  chose a specific device. by default fetch from all devices
        @param daterange:  default is all time.

        @return:  Iterator of spot record thunk
        """
        if not self.device_list:
            return iter([])
        sr = self._SpotRecord(self)
        dr: Tuple[dt, dt] = (dt.now() - timedelta(days=1), dt.now()) \
            if not daterange else daterange

        if did is None:
            generator = sr.all()
        else:
            generator = sr.one(did, dr)

        if not any(generator):
            return iter([])
        return generator

    def device(self) -> Optional[Generator]:
        if not self.device_list:
            return None
        return (MakeDict.make_device(d) for d in self.device_list)

    ####################################
    #  spot_location helper functions  #
    ####################################

    class _SpotRecord:
        """
        Handle spotrecord
        """

        def __init__(self, data: 'JianYanYuanData'):
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

        # need to push a context
        def one(self, did: int, daterange: Tuple[dt, dt]):
            """ generator for one device """
            try:
                with self.data.app.app_context():
                    from app.models import Device as MD
                    device = (MD.query.
                              filter(MD.device_id == did).first())
                dn = did_check(device.device_name, DataSource.JIANYANYUAN)
            except AttributeError:
                logger.warning("JianYanYuanData] fetch spot_record failed, "
                               + "device is not in database")
                return iter([])
            except WrongDidException:
                logger.warning('[XiaomiData] fetch spot_record failed, '
                               + 'device not in database')
                return iter([])

            # get one from the list.
            device_res = [d for d in self.device_list
                          if d.get("deviceId") == dn].pop()

            param = self._make_datapoint_param(device_res, daterange)
            if param is None:
                return iter([])

            return self._gen([param])

        def all(self):
            """ for all devlce on device list """
            datapoint_params = self._mk_datapoint_param_iter()
            if datapoint_params is None:
                return iter([])
            params_list = list(datapoint_params)  # construct param list
            return self._gen(params_list)

        def _gen(self, datapoint_params) -> RecordThunkGen:
            """
            * Main generator entrance.
            Both self.one() and self.all() will use this generator to obtain
            """
            def entrance(datapoints, params_list) -> RecordThunkGen:
                """
                Return a generator iter througth an effectful generator
                effectful_pair is the inner most layer of the generator.
                It comprise a iterator of a datapoint-parameter pair.

                """
                effectful = zip(datapoints, params_list)

                while True:  # send unevalued slice of iterator.
                    try:
                        yield (lambda: type(self)._records_factory(
                            islice(effectful, 1)))
                    except Exception:
                        break

            datapoints = map(self._datapoint, datapoint_params)
            # print(datapoint_params[:2])
            # print(list(datapoints)[:2])
            return entrance(datapoints, datapoint_params)

        def _mk_datapoint_param_iter(self) \
                -> Optional[Iterator[JdatapointParam]]:
            """
            ***
            Datapoint paramter generator. One parameter match to one datapoint.
            No side effect. just use local device_list fetched eailer to make
            parameter list.
            The parameter iter will later be used to fetch datapoints.
            """
            if self.device_list is None:
                return None
            logger.info('[dataMidware] creating Jianyanyuan datapoint params')
            # Fetch data within 7 day periodcially. use 7 day is because the
            # api can only fetch data of 7 data at once.

            def param_gen():
                """ param generator based on time sequence """
                for d in self.device_list:
                    b7gen = back7daytuple_generator(
                        str_to_datetime(d.get('createTime')))
                    for back7tuple in b7gen:
                        param = (JianYanYuanData
                                 ._SpotRecord
                                 ._make_datapoint_param(d, back7tuple))
                        if param is not None:
                            yield param

            datapoint_param_iter = chain.from_iterable(param_gen())
            if not any(datapoint_param_iter):
                logger.warning(JianYanYuanData.source +
                               'No datapoint parameter.')
                return None
            return datapoint_param_iter

        def _datapoint(self,
                       datapoint_param: JdatapointParam) \
                -> Optional[List[JdatapointResult]]:
            """
            *** EFFECTFUL
            datapoint of one device.
            query for datapoint based on the parameter passed in.

            @param datapoint_param:
            @return: list of query result.
            """
            logger.debug('getting datapoint {}'.format(datapoint_param))
            return jGetter.get_data_points(self.auth,
                                           self.token, datapoint_param)

        @staticmethod
        def _records_factory(
                arg: Iterator[Tuple[Optional[List[JdatapointResult]],
                                    JdatapointParam]]) -> Optional[RecordGen]:
            """
            * generate database compatible record data type.
            """
            data, param = next(arg)
            if data is None:
                return None
            return (MakeDict.make_spot_record(sr, param) for sr in data)

        @staticmethod
        def _make_datapoint_param(
            device_result: JdevResult,
            time_range: Optional[Tuple[dt, dt]] = None) \
                -> Optional[JdatapointParam]:
            """
            make query parameter datapoint query.
            DataPoint query parameter format:
                gid: str
                did: str
                aid: int
                startTime: str, yyyy-MM-ddTHH:mm:ss
                endTime: str, yyyy-MM-ddTHH:mm:ss
            """
            if not device_result:
                logger.error('no device result')
                return None

            gid = device_result.get('gid')
            did = device_result.get('deviceId')
            createTime = str_to_datetime(device_result.get('createTime'))
            modifyTime = str_to_datetime(device_result.get('modifyTime'))

            def get_aid() -> str:
                return '1,2,3,4,32,155'

            if not time_range:
                startTime: Optional[dt] = createTime
                endTime: Optional[dt] = (
                    modifyTime if modifyTime  # 1 hour gap avoid bug.
                    else dt.utcnow() - timedelta(hours=1))
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


class MakeDict:
    """ Convert json response from server into TypedDict """

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
            MakeDict._filter_location_attrs,
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
            logger.error('datapoint is empty')
            return None

        aS: Optional[Dict] = datapoint.get('as')

        if aS is None:
            logger.error('datapoint `as` record is empty')
            return None

        key: Optional[str] = datapoint.get('key')
        if key is None:
            logger.error('datapoint `key` record is empty')
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
            if not device_name:
                logger.error('[dataMidware] no device_name %s',
                             datapoint_param)

        spot_record = SpotRecord(
            spot_record_time=spot_record_time,
            device_name=device_name,
            temperature=temperature,
            humidity=humidity,
            pm25=pm25,
            co2=co2,
            window_opened=None,
            ac_power=ac_power)

        return spot_record

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
        # TODO: pick the most suitable infor from location attrs 2019-12-23
        # Location need to match with project.
        # So this function need to be implemented with project information.
        return Spot(project_name=loc_attrs.get('address'),
                    spot_name=None,
                    spot_type=None)

    @staticmethod
    def make_device(device_result: JdevResult) -> Device:
        return Device(location_info=MakeDict.make_location(device_result),
                      device_name=device_result.get('deviceId'),
                      online=device_result.get('online'),
                      device_type=device_result.get('productName'),
                      create_time=device_result.get('createTime'),
                      modify_time=device_result.get('modifyTime'))

    @staticmethod
    def _filter_location_attrs(device_result: JdevResult,
                               location_attrs: Dict) -> Dict:
        """
        filter location attributes from device results
        """
        return {k: v for k, v in device_result.items() if k in location_attrs}
