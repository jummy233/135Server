"""
Actors for concurrent record fetching.

Scheduler       responsible for periodically send update message to UpdateActor

UpdateActor     construct FetchMsg and dispatch to correct FetchActor.

FetchActor      Non block fetching.

SpotData        abstract layer for raw api. return iterator of data.

raw apis        the basic wrapper for calling server.

Server          data source.
"""

from flask import Flask
from queue import Queue
import threading
import multiprocessing
from abc import ABC, abstractmethod
from typing import Generic
from typing import TypeVar
from typing import Tuple
from typing import List
from typing import Generator
from typing import Optional
from typing import Dict
from typing import cast
from typing import NamedTuple
from typing import Iterator
from datetime import datetime as dt
from datetime import timedelta
from app.dataGetter.dataGen import JianYanYuanData
from app.dataGetter.dataGen import XiaoMiData
from app.dataGetter.dataGen.dataType import RecordThunkIter, RecordGen
from app.dataGetter.dataGen.dataType import thunk_iter
from app.dataGetter.dataGen.dataType import DataSource
from app.dataGetter.dataGen.dataType import device_source
from app.dataGetter.dataGen.dataType import SpotData, SpotRecord, Device
from concurrent.futures import ThreadPoolExecutor
from itertools import chain
from timeutils.time import PeriodicTimer
from app.modelcoro import record_send, device_send
from multiprocessing import Pool
import logging

logger = logging.getLogger(__name__)


T = TypeVar('T')

""" typed for scheduling one record query """
FetchMsg = Tuple[int, Tuple[dt, dt]]


class ActorExit(Exception):
    pass


class Actor(ABC, Generic[T]):
    def __init__(self, proc=False):
        self._proc = proc
        self._queue = Queue()

    def send(self, msg: T):
        self._queue.put(msg)

    def recv(self):
        msg = self._queue.get()
        if msg is ActorExit:
            raise ActorExit()
        return msg

    def close(self):
        # logger.debug("actor closed %s", str(self))
        self.send(ActorExit)

    def start(self):
        if not self._proc:
            t = threading.Thread(target=self._bootstrap)
            self._terminated = threading.Event()
        else:
            t = multiprocessing.Process(target=self._bootstrap)
            self._terminated = multiprocessing.Event()

        t.daemon = True
        # logger.debug("start new actor %s", str(self))
        t.start()

    def _bootstrap(self):
        try:
            self.run()
        except ActorExit:
            pass
        finally:
            self._terminated.set()

    def join(self):
        self._terminated.wait()

    @abstractmethod
    def run(self):
        raise NotImplementedError("Actor needs to be overriden")


class FetchActor(Actor):
    """
    Fetch Records...

    Feeded with did and time range.
    DataGen object will create a corresponding iterator for given did
    and time range.
    FetchActor will iter through the iterator with additional threads.

    Note: FetchActor is only responsible for fetching data.
    It is up to upstream actors to decide if it is necessary to fetch.
    For example, Another actor will check if data of the current online devices
    are up to date. If it's not, It will send query message and specific query
    range to FetchActor.

    @send FetchMsg:  a tuple of device id and time range.
                     device id corresponds to device name in our databse.
    """

    def __init__(self, app: Flask, datagen: SpotData):
        super().__init__()
        self._datagen = datagen
        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)

    @property
    def datagen(self):
        return self._datagen

    def run(self):
        """ periodically fetch new data """

        while True:
            msg: FetchMsg = self.recv()
            did, time_range = msg

            jobs: RecordThunkIter
            jobs = self.datagen.spot_record(did, time_range)
            print("jobs: ", list(jobs))

            generator_chain: Iterator[SpotRecord] = thunk_iter(jobs)

            with self.datagen.app.app_context():
                with Pool(5) as pool:
                    for n in pool.imap_unordered(record_send, generator_chain):
                        pass

            print(threading.enumerate())


class UpdateMsg:
    def __init__(self, tag: DataSource, payload: FetchMsg):
        self._tag: DataSource = tag
        self._payload = payload

    @property
    def tag(self):
        return self._tag

    @property
    def payload(self) -> Tuple:
        return self._payload


class UpdateActor(Actor):
    """
    deal with all updates.
    Either it is real time update or overall update.
    """

    def __init__(self, app: Flask):
        super().__init__()
        self._app = app
        self.jianyanyuan_actor = FetchActor(app, JianYanYuanData(app))
        self.xiaomi_actor = FetchActor(app, XiaoMiData(app))

    def start(self):
        super().start()
        self.jianyanyuan_actor.start()
        self.xiaomi_actor.start()

    def run(self):
        while True:
            msg: UpdateMsg = self.recv()
            if msg.tag is DataSource.ALL:
                self.overall_update()
            elif msg.tag is DataSource.JIANYANYUAN:
                __import__('pdb').set_trace()
                self.jianyanyuan_actor.send(msg.payload)
            elif msg.tag is DataSource.XIAOMI:
                self.xiaomi_actor.send(msg.payload)

    def close(self):
        super().close()
        self.jianyanyuan_actor.close()
        self.xiaomi_actor.close()

    def overall_update(self):
        """ update all data """


class ScheduleTable(NamedTuple):
    """
    config the duration of each event
    A None field indicates cancel the corresponding schedule.
    """
    overall: int                   # overall update
    realtime: int                  # update online devices.
    device: Optional[int]          # update device list.
    backup: Optional[int]          # backup database
    healthcheck: Optional[int]     # check the health of database.

    @staticmethod
    def default() -> 'ScheduleTable':
        return ScheduleTable(
            overall=59 * 60 * 24,
            realtime=60*5,
            device=None,
            backup=None,
            healthcheck=None)


class UpdateScheduler:
    """
    Update scheduler.
    overall timer trigger overall update each day.
    an overall update will update device list first, then update records
    are based on the newly generated device list.

    realtime timer trigger update each 5 minute. and only update
    online devices.

    device timer update device each day.
    """

    def __init__(self, config: Optional[ScheduleTable] = None):
        """ plan schedules based on the config tuple passed in. """
        if config is None:
            # the basic default schedule
            self._config = ScheduleTable.default()
        else:
            self._config = config

        self._setup_timer()

    def _setup_timer(self):
        """ setup timer based on schedule table """
        config = self._config
        self.overall_timer = PeriodicTimer(config.overall)
        self.realtime_timer = PeriodicTimer(config.realtime)

        if config.device:
            self.device_update_timer = PeriodicTimer(config.device)
        if config.backup:
            self.backup_timer = PeriodicTimer(config.backup)
        if config.healthcheck:
            self.healthcheck_timer = PeriodicTimer(config.healthcheck)

    def init_app(self, app: Flask):
        """ get flask app context."""
        self.update_actor = UpdateActor(app)
        self.app = app

    def start(self):
        self.overall_timer.start()
        self.realtime_timer.start()
        self.update_actor.start()

    def close(self):
        self.update_actor.close()

    def force_overall_update(self):
        self.update_actor.send(UpdateMsg(DataSource.ALL, ()))

    def update_device(self):
        """
        generate new list, store it into database.
        """
        self.update_actor.xiaomi_actor.datagen.make_device_list()
        self.update_actor.jianyanyuan_actor.datagen.make_device_list()
        devices = chain(
            self.update_actor.xiaomi_actor.datagen.normed_device_list,
            self.update_actor.jianyanyuan_actor.datagen.normed_device_list)
        with self.app.app_context():
            from app.models import Device as MD
            from app.modelOperations import ModelOperations, commit
            for device in devices:  # dataType.Device
                dname = device.get("device_name")
                if (dname is not None
                    and
                    MD.query
                      .filter(MD.device_name == dname)
                      .count() == 0):
                    ModelOperations.Add.add_device(cast(Dict, device))
                    commit()

    def update_realtime(self):
        """
        Update the newest records from online devices.

        A list of UpdateMsg will be constructed for every update.
        There're not many online device so the performance is pretty ok.
        It might be a problem when there're arount thounds of online devices
        Which is pretty impossible in the near feature.
        """
        with self.app.app_context():
            from app.models import Device as MD
            devices = MD.query.filter(MD.online).all()

        onlines = [
            UpdateMsg(device_source(d.device_name),
                      (d.device_id,
                       (dt.now() - timedelta(minutes=5), dt.now())))
            for d in devices]

        for online in onlines:
            self.update_actor.send(online)
