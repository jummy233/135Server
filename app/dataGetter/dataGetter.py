"""
app level interface
provides app context.
"""
from flask import Flask
from typing import Callable, Optional
from utils import partialclass
from app.dataGetter.dataGen.dataType import DataSource, SpotData
from app.dataGetter.dataGen.jianyanyuanData import JianYanYuanData
from app.dataGetter.dataGen.xiaomiData import XiaoMiData
from app.dataGetter.reatime.RealTimeStreamGetter import RealtimeGenProxy


class DataGetterFactory:
    def __init__(self):
        self.is_init: bool = False

    def init_app(self, app: Flask):
        self.app = app

    def get_data_getter(self, source: DataSource) \
            -> Callable[[], Optional[SpotData]]:
        """
        TODO: unfinished. need to provide a universial interface.
        """
        if source.value == DataSource.JIANYANYUAN.value:
            return lambda: JianYanYuanData(self.app)
        elif source.value == DataSource.XIAOMI.value:
            return lambda: XiaoMiData(self.app)
        return lambda: None

    def get_data_streamer(self, did: int) -> RealtimeGenProxy:
        return RealtimeGenProxy(self.app, did)
