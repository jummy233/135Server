"""
Control the update frequency.
"""
import threading
import time
from collections import defaultdict
from typing import Dict
from app.dataGetter.reatime.Exchange import Exchange
from enum import Enum


class UpdateClock:
    """
    Send update pulse.
    """
    def __init__(self, interval: float):
        self._flag = 0x0
        self._interval = interval
        self._cv = threading.Condition()

    def start(self):
        t = threading(target=self.run)
        t.daemon = True
        t.start()

    def run(self):
        while True:
            time.sleep(self._interval)
            with self._cv:
                self._flag != 0x1
                self._cv.notify_all()

    def wait_for_tick(self):
        with self._cv:
            last_flag = self._flag
            while last_flag == self._flag:
                self._cv.wait()


class ExchangeTag(Enum):
    Update = 0
    Probe = 1
    Upgrade = 2


class DBDupdateScheduler:
    """
    Schedule task for database update.
    """

    def __init__(self, interval: float):
        self._clock = UpdateClock(interval)
        self._exchange: Dict[str, Exchange] = defaultdict(Exchange)

    def _init_exchanges(self):
        """ initialize exchanges """

    def schedule(self):
        pass
