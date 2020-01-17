from math import floor
from datetime import datetime as dt
from datetime import timedelta
from typing import Optional, Tuple, Generator


def currentTimestamp(digit: int) -> int:
    """ return unix timestamp with disired digits """
    factor: int = floor(10 ** (digit - 10))
    return floor(dt.timestamp(dt.utcnow()) * factor)


def str_to_datetime(sdate: Optional[str]) -> Optional[dt]:
    if not sdate:
        return None
    return dt.strptime(sdate, '%Y-%m-%dT%H:%M:%S')


def datetime_to_str(datetime: Optional[dt]) -> str:
    if not datetime:
        return ''
    return '{}-{:02}-{:02}T{:02}:{:02}:{:02}'.format(datetime.year,
                                                     datetime.month,
                                                     datetime.day,
                                                     datetime.hour,
                                                     datetime.minute,
                                                     datetime.second)


def coutback7day_tuple(prev_tuple: Tuple[dt, dt]) -> Tuple[dt, dt]:
    """
    count back 7 days
    if input (2019-11-10, 2019-11-17) return (2019-11-03, 2019-11-10)
    """
    delta_seven = timedelta(days=7)
    start, _ = prev_tuple
    return start - delta_seven, start


def back7daytuple_generator(create_time: dt) -> Generator[Tuple[dt, dt], None, None]:
    """ 7 day tuple generator. stop when back to create time"""
    delta_seven = timedelta(days=7)
    now = dt.utcnow()
    date_tuple = (now - delta_seven, now)

    while date_tuple[0] > create_time:
        yield date_tuple
        date_tuple = coutback7day_tuple(date_tuple)
        d1, d2 = date_tuple

        if d1 < create_time:  # if less than create time construct from create time.
            yield (create_time, d2)

