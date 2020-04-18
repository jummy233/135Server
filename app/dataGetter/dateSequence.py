"""
This module contain a generator that create datetime sequentially
with given time interval.
"""
import datetime
import itertools
from copy import deepcopy
from datetime import datetime as dt
from datetime import timedelta
from typing import Generator, NewType, Optional

DateSequence = Generator[dt, dt, None]


def date_sequence(begin: dt, end: dt, min_interval: int) \
        -> Optional[DateSequence]:
    """ min_interval is in minutes """
    if end < begin:
        return None

    current: dt = deepcopy(begin)

    while current <= end:
        v = (yield current)
        if v is not None:
            current = v
        else:
            current += timedelta(minutes=min_interval)
