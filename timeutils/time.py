from datetime import datetime as dt
import time
from datetime import timedelta
from math import floor
from typing import Generator, Optional, Tuple, List, Union


def timestamp_setdigits(ts: Union[float, int], digit: int) -> int:
    factor: int = floor(10 ** (digit - 10))
    return floor(int(ts) * factor)


def currentTimestamp(digit: int) -> int:
    """ return unix timestamp with disired digits """
    factor: int = floor(10 ** (digit - 10))
    return floor(dt.timestamp(dt.utcnow()) * factor)


def datetime_format_resolver(datetime_str: str, formats: List[str]
                             ) -> Optional[dt]:
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
    # accept multiple formats
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
    if not datetime:
        return ''
    return '{}-{:02}-{:02}T{:02}:{:02}:{:02}'.format(
        datetime.year,
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


def back7daytuple_generator(create_time: Optional[dt]) \
        -> Generator[Tuple[dt, dt], None, None]:
    """ 7 day tuple generator. stop when back to create time"""
    delta_seven = timedelta(days=7)
    now = dt.utcnow()

    if create_time is None:  # if no create time default go back for a month.
        create_time = now - 30 * delta_seven
    date_tuple = (now - delta_seven, now)

    if date_tuple[0] < create_time:
        yield (create_time, now)

    while date_tuple[0] > create_time:
        yield date_tuple
        date_tuple = coutback7day_tuple(date_tuple)
        d1, d2 = date_tuple
        # if less than create time construct from create time.
        if d1 < create_time:
            yield (create_time, d2)
