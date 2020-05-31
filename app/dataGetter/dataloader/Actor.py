from queue import Queue
import threading
import multiprocessing
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Tuple, Callable
from datetime import datetime as dt

T = TypeVar('T')


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
        self.send(ActorExit)

    def start(self):
        if (self._proc):
            t = threading.Thread(target=self._bootstrap)
            self._terminated = threading.Event()
        else:
            t = multiprocessing.Process(target=self._bootstrap)
            self._terminated = multiprocessing.Event()

        t.daemon = True
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


class FetchActor(Actor, ABC):
    def __init__(self, daterange: Tuple[dt, dt]):
        self._daterange = daterange

    def run(self):
        """ periodically fetch new data """
        pass

    @abstractmethod
    def fetch(self):
        """
        fetch a single data
        """


class XiaomiRealTimeFetchActor(FetchActor):
    def __init__(self):
        pass


class JianyanyuanRealTimeFetchActor(FetchActor):
    def __init__(self):
        pass

    def run(self):
        pass


def DBPeriodicalUpdateActor(Actor):
    """
    deal with overall update.
    """
    def run(self):
        pass


def ProbeActor(Actor, ABC):
    """
    Probe for connection
    """
    def __init__(self, prober: Callable):
        """
        @param prober:
        @type  Callable:

        prober is a wrapper of arbitrary the basic data api.
        """
        self._prober = prober

    @abstractmethod
    def probe(self) -> bool:
        """
        Test for given condition. Token validity, data format,
        etc.
        """


class XiaomiTokenProbeActor(ProbeActor):
    pass


class JianyanYuanTokenProbeActor(ProbeActor):
    pass


class JianyanYuanDataPointProbeActor(ProbeActor):
    pass

