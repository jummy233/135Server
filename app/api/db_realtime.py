"""
Return all the real time device.
"""

from typing import Generator, NewType, Union, List, Callable
import datetime
import threading

from flask import Response
from flask import jsonify, request

from dataGetter.dataGen.jianyanyuanData import JianYanYuanData
from dataGetter.dataGen.xiaomiData import XiaoMiData
from dataGetter.dataGen.dataType import SpotData

from ..api_types import ApiResponse, ReturnCode
from ..models import Device, SpotRecord
from . import api

Json = NewType('Json', str)


@api.route('/realtime/devices', methods=["GET"])
def realtime_device() -> Json:
    """
    return list of device that are online.
    """
    online_devices = (
        Device
        .query
        .filter(Device.online))

    response_object = (
        ApiResponse(
            status=ReturnCode.OK.value,
            message="data fetched",
            data=[device.to_json() for device in online_devices]))

    return jsonify(response_object)


@api.route('/realtime/device/<did>/spot_records', methods=["GET", "DELETTE"])
def realtime_spot_record(did: int) -> Union[Response, Json]:
    """
    Stream realtime data to client.
    """
    if request.method == 'DELETTE':
        # stop existing generator.
        return jsonify(
            ApiResponse(status=ReturnCode.OK.value,
                        message="stream stopped"))

    realtime = RealtimeGenProxy(did)
    return Response(
        realtime.generate(),
        mimetype="application/json")


class RealtimeGenProxy:
    """ fetch realtime data and existed data together """

    def __init__(self, did: int):
        self._reatimegen = RealTimeGen(did)

    def generate(self) -> Generator:
        while self._reatimegen._concate_generator() == []:
            # yiedl proxy dummy data
            yield

        for item in self._reatimegen.generate():
            yield item


class RealTimeGen:
    def __init__(self, did: int):
        self.did = did
        self._init_datasource(did)
        self._init_datastream()

    def generate(self) -> Generator:
        if self._db_datasource_event.is_set() \
                and self._datastream_event.is_set():
            for generator in self._concate_generator():
                for item in generator:
                    yield item

    def _init_datasource(self, did: int):
        self._db_datasource: List = []
        self._db_datasource_event = threading.Event()
        self.current = datetime.datetime.now()
        self.yesterday = self.current - datetime.timedelta(days=1)

        def getdata():
            self._db_datasource = (
                SpotRecord
                .query
                .filter(Device.device_id == did)
                .filter(SpotRecord.spot_record_time >= self.yesterday)
                .all())

        t = threading.Thread(target=getdata)
        t.start()

    def _init_datastream(self):
        self._datastream: List = []
        self._datastream_event = threading.Event()

        def getdata():
            self._datastream = JianYanYuanData().spot_record()

        t = threading.Thread(target=getdata)
        t.start()
        self._datastream_event.set()

    def _concate_generator(self):
        return [self._db_datasource].extend(self._datasource)
