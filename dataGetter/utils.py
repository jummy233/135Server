from math import floor
from datetime import datetime as dt
from typing import Optional


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
