"""
NOTE: Deprecated! Use Scheduler instead.
"""

import datetime
import threading
from typing import Callable, Iterator, List, NewType, Union, Generator
from flask import Flask

from app.dataGetter.dataGen.dataType import SpotData
from app.dataGetter.dataGen.dataType import SpotRecord as SpotRecordT
from app.dataGetter.dataGen.jianyanyuanData import JianYanYuanData
from app.dataGetter.dataGen.xiaomiData import XiaoMiData
from app.dataGetter.dataGen.dataType import LazySpotRecord


class RealtimeGenProxy:
    """ fetch realtime data and existed data together """

    def __init__(self, app: Flask, did: int):
        self._reatimegen = RealTimeGen(app, did)

    def generate(self) -> Generator[LazySpotRecord, None, None]:
        # note item is a generator.
        # TODO proxy dummy data for error handling.
        for item in self._reatimegen.generate():
            yield item


class RealTimeGen:
    def __init__(self, app: Flask, did: int):
        self.app = app
        self.did = did
        self._init_datasource(did)
        self._init_datastream()
        self.t = None

    def generate(self) -> Generator[LazySpotRecord, None, None]:
        # steeam data. output None if datastream is not avaiable.
        # how to handle None is up to the caller.
        try:
            if self._datastream is None:
                yield None

            for generator in self._datastream:
                for item in generator:
                    yield item()
        except StopIteration:
            return

    @property
    def datastream(self):
        """ datastream is the main stream of realtime data."""
        return self._datastream

    def _init_datastream(self):
        self._datastream: List[Iterator[LazySpotRecord]] = []

        def getdata():
            data = JianYanYuanData(self.app)
            date = (self.yesterday, self.current)
            self._datastream.append(data.spot_record(self.did, date))

        t = threading.Thread(target=getdata)
        t.start()

    def _init_datasource(self, did: int):
        self._db_datasource: List = []
        self.current = datetime.datetime.now()
        self.yesterday = self.current - datetime.timedelta(days=1)

        # TODO need to push a context
        def getdata():
            with self.app.app_context():
                from app.models import Device, SpotRecord
                self._db_datasource = (
                    SpotRecord
                    .query
                    .filter(Device.device_id == did)
                    .filter(SpotRecord.spot_record_time >= self.yesterday)
                    .all())

        t = threading.Thread(target=getdata)
        t.start()
