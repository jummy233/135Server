"""
Return all the real time device.
"""

import json
from operator import itemgetter
from typing import Generator, NewType, Union, List, Callable
import datetime
import queue
import threading

from flask import Response
from flask import json as FlaskJson
from flask import jsonify, request

from dataGetter.dataGen.jianyanyuanData import JianYanYuanData
from dataGetter.dataGen.xiaomiData import XiaoMiData
from dataGetter.dataGen.dataType import SpotData

from ..api_types import (ApiRequest, ApiResponse, PagingRequest, ReturnCode,
                         is_ApiRequest)
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
    date_back = 1

    def __init__(self, did: int):
        self.did = did
        self.__init_device(did)
        self.__init_datasource(did)

    def __init_device(self, did: int):
        self.device = (Device
                       .query
                       .filter(Device.device_id == did)
                       .first())

    def __init_datasource(self, did: int):
        self.current = datetime.datetime.now()
        self.yesterday = self.current - datetime.timedelta(days=1)
        self.__datasource: List = [JianYanYuanData()]  # TODO xiaomi
        self.__db_datasource = (
            SpotRecord
            .query
            .filter(Device.device_id == did)
            .filter(SpotRecord.spot_record_time
                    < self.yesterday)
            .all())

    def __concate_generator(self):
        return [self.__db_datasource].extend(self.__datasource)

    def generate(self):
        for generator in self.__concate_generator():
            for item in generator:
                yield item
