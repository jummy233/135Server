from math import floor
from datetime import datetime as dt


def currentTimestamp(digit: int) -> int:
    """ return unix timestamp with disired digits """
    factor: int = floor(10 ** (digit - 10))
    return floor(dt.timestamp(dt.utcnow()) * factor)


def str_to_datetime(sdate: str) -> dt:
    return dt.strptime(sdate, '%Y-%m-%dT%H:%M:%S')


def datetime_to_str(datetime: dt) -> str:
    return '{}-{}-{}T{}:{}:{}'.format(datetime.year,
                                      datetime.month,
                                      datetime.day,
                                      datetime.hour,
                                      datetime.minute,
                                      str(datetime.second)[:2])


