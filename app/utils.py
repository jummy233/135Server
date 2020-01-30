
from enum import Enum
from datetime import datetime, timedelta
import time
from random import uniform
from typing import Callable, Optional
import importlib
import sys


def lazyload(module_name):
    """ load module lazily"""
    try:
        return sys.modules[module_name]
    except KeyError:
        spec = importlib.util.find_spec(module_name)
        module = importlib.util.module_from_spec(spec)
        loader = importlib.util.LazyLoader(spec.loader)

        loader.exec_module(module)
        return module


def rand_date_in(date1: datetime, date2: datetime) -> Callable:
    def f() -> datetime:
        unix_time1 = time.mktime(date1.timetuple())
        unix_time2 = time.mktime(date2.timetuple())
        unix_rand_date = uniform(unix_time1, unix_time2)
        return datetime.fromtimestamp(unix_rand_date).replace(microsecond=0)
    return f


class TimeAccuracy(Enum):
    """
    control the number of records retrived from db.
    """
    YEAR_ACCURACY = 0
    MONTH_ACCURACY = 1
    DAY_ACCURACY = 2


def is_nice_time(step_min: int) -> Callable:
    """
    step len in minute
    """

    def f(dt: datetime) -> bool:
        return dt.minute % step_min == 0
    return f


def normalize_time(step_min: int) -> Callable:
    """
    step len in minute
    """

    assert (step_min % 2 == 0 or
            step_min % 3 == 0 or
            step_min % 5 == 0), "time step is not divisible by 60"

    def f(dt: Optional[datetime]) -> Optional[datetime]:
        if dt is None:
            return None
        if step_min < 60:                       # within an hour.
            step_num = round(dt.minute / step_min)
            minute = step_num * step_min

            if minute == 60:
                normalized_time = datetime(
                    dt.year,
                    dt.month,
                    dt.day,
                    dt.hour,
                    0) + timedelta(hours=1)
            else:
                normalized_time = datetime(dt.year, dt.month, dt.day, dt.hour, minute)

            return normalized_time
        else:                                    # cross hours, accurate to nearest hour
            step_num = round((dt.hour * 60 + dt.minute) / step_min)
            minutes = step_num * step_min          # e,g ((240 + 32) / 120) * 120 = 240
            hour = minutes / 60                    # 240 / 60 = 4
            normalized_time = datetime(dt.year, dt.month, dt.day) + timedelta(hours=hour)
            return normalized_time
    return f


