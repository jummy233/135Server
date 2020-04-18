"""
app level interface
provides app context.
"""
from flask import Flask
from typing import Callable, Optional
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
        with self.app.app_context() as context:
            if source.value == DataSource.JIANYANYUAN.value:
                return lambda: JianYanYuanData(context)
            elif source.value == DataSource.XIAOMI.value:
                return lambda: XiaoMiData(context)
            return lambda: None

    def realtime_streamer(self) ->



