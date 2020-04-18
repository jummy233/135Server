import datetime
import threading
from typing import Callable, Generator, List, NewType, Union
from flask import Flask

from app.dataGetter.dataGen.dataType import SpotData
from app.dataGetter.dataGen.jianyanyuanData import JianYanYuanData
from app.dataGetter.dataGen.xiaomiData import XiaoMiData
from app.models import Device, SpotRecord


class RealtimeGenProxy:
    """ fetch realtime data and existed data together """

    def __init__(self, did: int, app: Flask):
        self._reatimegen = RealTimeGen(did, app)

    def generate(self) -> Generator:
        while self._reatimegen._datastream == []:
            # yiedl proxy dummy data
            yield
        for item in self._reatimegen.generate():
            yield item


class RealTimeGen:
    def __init__(self, did: int, app: Flask):
        self.app = app
        self.did = did
        self._init_datasource(did)
        self._init_datastream()
        self.t = None

    def generate(self) -> Generator:
        for generator in self._datastream:
            for item in generator:
                yield item

    @property
    def datastream(self):
        """ datastream is the main stream of realtime data."""
        return self._datastream

    def _init_datasource(self, did: int):
        self._db_datasource: List = []
        self.current = datetime.datetime.now()
        self.yesterday = self.current - datetime.timedelta(days=1)

        # TODO need to push a context
        def getdata():
            with self.app.app_context():
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

        def getdata():
            __import__('pdb').set_trace()
            data = JianYanYuanData()
            date = (self.yesterday, self.current)
            self._datastream = data.spot_record(self.did, date)

        t = threading.Thread(target=getdata)
        t.start()
