"""
Return all the real time device.
"""

from typing import Callable, Generator, List, NewType, Union

from flask import Response, jsonify, request

from app.api import api
from app.api.api_types import ApiResponse, ReturnCode
from app.models import Device, SpotRecord
from app.dataGetter.reatime.RealTimeStreamGetter import RealtimeGenProxy

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