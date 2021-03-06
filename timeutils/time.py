"""
Utilities for dealing with time.
"""

from datetime import datetime as dt
import time
from datetime import timedelta
from math import floor
from typing import Generator, Optional, Tuple, List, Union
from threading import Thread, Condition, Event


class PeriodicTimer:
    """
    interval is in second.
    it can be choosen to be a daemon thread or not.
    when it runs as daemon, a call to close() will
    do nothing.
    """
    def __init__(self, interval: float, daemon: bool = True):
        self._flag = 0x0
        self._invertal = interval
        self._cv = Condition()
        self._daemon = daemon
        self._quit = Event()

    def __del__(self):
        self.close()

    def start(self):
        self.t = Thread(target=self.run)
        self.t.daemon = self._daemon
        self.t.start()

    def run(self):
        while not self._quit.is_set():
            self._quit.wait(self._invertal)
            with self._cv:
                self._flag ^= 0x1
                self._cv.notify_all()

    def close(self):
        if not self._daemon:
            self._quit.set()

    def wait_for_tick(self):
        """
        block the caller until the condition
        is triggerd.
        """
        with self._cv:
            last_flag = self._flag
            while last_flag == self._flag:
                self._cv.wait()


def timestamp_setdigits(ts: Union[float, int], digit: int) -> int:
    factor: int = floor(10 ** (digit - 10))
    return floor(int(ts) * factor)


def currentTimestamp(digit: int) -> int:
    """ return unix timestamp with disired digits """
    factor: int = floor(10 ** (digit - 10))
    return floor(dt.timestamp(dt.utcnow()) * factor)


def datetime_format_resolver(datetime_str: str, formats: List[str]
                             ) -> Optional[dt]:
    """
    This abomination shouldn't exist, but it is here anyway.
    there is plan to move time verification to the frontend
    so this will soon be deprecated.
    if this comment is not modified it means it is still
    currently in use.
    It basically use exception as a flow control to handle
    failure case ...
    """
    if len(formats) > 20:
        raise RecursionError("too many datetime formats")
    if len(formats) == 0:  # no match.
        return None
    res: Optional[dt] = None

    try:
        f = formats.pop(0)
        res = dt.strptime(datetime_str, f)
    except ValueError:
        res = datetime_format_resolver(datetime_str, formats)
    except Exception:  # programmer error. should not return None here.
        raise
    return res


def str_to_datetime(sdate: Optional[str]) -> Optional[dt]:
    if not sdate:
        return None
    formats: List[str] = [
        '%Y-%m-%d:%H-%M-%S',
        '%Y-%m-%d:%H-%M',
        '%Y-%m-%d:%H',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M',
        '%Y-%m-%dT%H',
        '%Y-%m-%d',
        '%Y-%m',
        '%Y',
        '%Y/%m/%d',
        '%Y/%m',
        '%Y',
    ]

    res = datetime_format_resolver(sdate, formats)
    return res


def datetime_to_str(datetime: Optional[dt]) -> str:
    """
    It will generate jianyanyuan compatible datetime string.
    """
    if not datetime:
        return ''
    return '{}-{:02}-{:02}T{:02}:{:02}:{:02}'.format(
        datetime.year,
        datetime.month,
        datetime.day,
        datetime.hour,
        datetime.minute,
        datetime.second)


def date_range_iter(create_time: dt, countback: timedelta) \
        -> Generator[Tuple[dt, dt], None, None]:
    """
    date range tuple generator. stop when hit the device create time
    scheduler can use this to control which segment of data to
    query.
    countback argument needs to be altered based on specific
    situation and specific data source.

    For instance xiaomi allows 300 entries per request maximum,
    and it record generally every 1 minute (in practice is smaller
    because it check value every 1 minute, and only report if the difference
    from it and previous value is larger than certain threshold).
    so countback can be set to (300 * 60) seconds. This way we don't miss
    out any data.
    """
    now = dt.utcnow()
    date_tuple = (now - countback, now)
    while date_tuple[0] > create_time:
        yield date_tuple
        # the datetuple.
        # ((2020, 1, 3), (2020, 1 2)) -> ((2020, 1, 2), (202, 1, 1))
        start, _ = date_tuple
        date_tuple = (start - countback, start)
        d1, d2 = date_tuple

        # if less than create time construct from create time.
        if d1 < create_time:
            yield (create_time, d2)
    yield (create_time, now)  # finish iteration.
    return
