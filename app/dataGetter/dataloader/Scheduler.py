"""
Actors for concurrent record fetching.

Scheduler       responsible for periodically send update message to UpdateActor

UpdateActor     construct FetchMsg and dispatch to correct FetchActor.

FetchActor      Non block fetching.

SpotData        abstract layer for raw api. return iterator of data.

raw apis        the basic wrapper for calling server.

Server          data source.
"""

from queue import Queue
import threading
from flask import Flask
import multiprocessing
from abc import ABC, abstractmethod
from typing import (Generic, TypeVar, Tuple, List, Generator, Optional,
                    Dict, cast)
from datetime import datetime as dt
from datetime import timedelta
from app.dataGetter.dataGen import JianYanYuanData
from app.dataGetter.dataGen import XiaoMiData
from app.dataGetter.dataGen.dataType import (
    LazySpotRecord, RecordThunkIter, RecordGen, RecordThunk, unwrap_thunk,
    SpotData, SpotRecord, Device, DataSource, device_source)
from concurrent.futures import ThreadPoolExecutor
from logger import make_logger
from itertools import chain
from timeutils.time import PeriodicTimer

logger = make_logger('actors', 'actors_log')

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
        self._record: Generator = self.record(self._datagen.app)
        self._device: Generator = self.device(self._datagen.app)
        self._pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)

    @property
    def datagen(self):
        return self._datagen

    def run(self):
        """ periodically fetch new data """
        def worker(thunk: RecordThunk):
            print("worker")  # DEBUG
            record_gen: Optional[RecordGen] = unwrap_thunk(thunk)
            if record_gen is None:
                logger.info("worker skipped")
                return
            logger.info("worker running")
            self._record.send(next(record_gen))

        while True:
            msg: FetchMsg = self.recv()
            did, time_range = msg
            jobs: RecordThunkIter = self.datagen.spot_record(
                did, time_range)
            print("jobs: ", list(jobs))
            with self._pool as pool:
                pool.map(worker, jobs, chunksize=1)
            print(threading.enumerate())

    @staticmethod
    def record(app: Flask) -> Generator[None, SpotRecord, None]:
        """
        a coroutine receives databse compatible dictionary
        and record them into database
        """
        with app.app_context():
            from app.modelOperations import ModelOperations, commit
            while True:
                data: SpotRecord = yield
                try:
                    # NOTE:
                    # data here is an intermediate representation of
                    # Record which is a subset of the device dictionary
                    # that been used by ModelOperations.
                    # cast is fine. if a field doesn't exist models will
                    # just ignore it.
                    __import__('pdb').set_trace()
                    print(data)  # DEBUG
                    ModelOperations.Add.add_spot_record(cast(Dict, data))
                    commit()
                except Exception:
                    logger.error("Fetch Actor failed in commit record")
                    break

    @staticmethod
    def device(app: Flask) -> Generator[None, Device, None]:
        """
        a croutine record device into database.
        """
        with app.app_context():
            from app.modelOperations import ModelOperations, commit
            while True:
                data: Device = yield
                try:
                    # NOTE:
                    # data here is an intermediate representation of
                    # Device which is a subset of the device dictionary
                    # that been used by ModelOperations.
                    # cast is fine. if a field doesn't exist models will
                    # just ignore it.
                    ModelOperations.Add.add_device(cast(Dict, data))
                    commit()
                except Exception:
                    logger.error("Fetch Actor failed in commit device")
                    break


class UpdateMsg:
    def __init__(self, tag: DataSource, payload: Tuple):
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
                self.jianyanyuan_actor.send(msg.payload)
            elif msg.tag is DataSource.XIAOMI:
                self.xiaomi_actor.send(msg.payload)

    def close(self):
        super().close()
        self.jianyanyuan_actor.close()
        self.xiaomi_actor.close()

    def overall_update(self):
        """ update all data """


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

    def __init__(self):
        self.overall_timer = PeriodicTimer(60 * 60 * 24)
        self.realtime_timer = PeriodicTimer(60 * 5)

    def init_app(self, app: Flask):
        self.update_actor = UpdateActor(app)
        self.app = app

    def start(self):
        self.overall_timer.start()
        self.realtime_timer.start()
        self.update_actor.start()

    def close(self):
        self.update_actor.close()

    def force_overall_update(self):
        self.update_actor.send(UpdateMsg("all", ()))

    @property
    def online_device_list(self) -> List[UpdateMsg]:
        """
        This will be called in each realtime update.
        There're not many online device so the performance is pretty ok.
        It might be a problem when there're arount thounds of online devices
        Which is pretty impossible in the near feature.

        @returntype: list of device id in database.
        """
        with self.app.app_context():
            from app.models import Device as MD
            device = MD.query.filter(MD.online).all()

        return [UpdateMsg(device_source(d.device_name),
                          (dt.now() - timedelta(minutes=5), dt.now()))
                for d in device]

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

    def realtime_update(self):
        """
        Update the newest records from online devices.
        """
        onlines = self.online_device_list()
        for online in onlines:
            self.update_actor.send(online)
