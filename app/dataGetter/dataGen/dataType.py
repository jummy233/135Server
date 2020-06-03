"""
Some types definitions and utility tools around this types.
"""

from flask import Flask
from abc import ABC, abstractmethod
import enum
from datetime import datetime as dt
from typing import (List, Callable, Dict, Generator, Iterator, List, NewType,
                    Optional, Tuple, TypedDict, Union, cast, TypeVar)

T = TypeVar('T')


class DataSource(enum.Enum):
    NONE = 0
    JIANYANYUAN = 1
    XIAOMI = 2
    ALL = 3


class Location(TypedDict):
    province: Optional[str]
    city: Optional[str]
    address: Optional[str]
    extra: Optional[str]    # extra useful informatino to determine spot


class Spot(TypedDict):
    """ Spot is generate from location """
    project_name: Optional[str]
    spot_name: Optional[str]
    spot_type: Optional[str]


class SpotRecord(TypedDict):
    device_name: Optional[str]
    spot_record_time: Optional[dt]
    temperature: Optional[float]
    humidity: Optional[float]
    pm25: Optional[float]
    co2: Optional[float]
    window_opened: Optional[bool]
    ac_power: Optional[float]


class Device(TypedDict):
    location_info: Optional[Location]  # Location info help to deduce the spot.
    device_name: Optional[str]
    device_type: Optional[str]
    online: Union[int, bool, None]  # different possible boolean representation
    create_time: Optional[dt]
    modify_time: Optional[dt]


LazySpotRecord = Callable[[], Optional[Generator[Device, None, None]]]

"""
RecordGen:      Generator contains data from one request.
RecordThunk:    Unevaled record data.
RecordThunkGen: Generator of multiple RecordThunk s.
"""
RecordGen = Generator[Optional[SpotRecord], None, None]
RecordThunk = Callable[[], Optional[RecordGen]]
RecordThunkIter = Iterator[RecordThunk]


def unwrap_thunk(thunk: Callable[[], T]) -> T:
    return thunk()


class WrongDidException(Exception):
    pass


def device_check(dname: str, data_source: DataSource) -> str:
    """
    @raise e:  WrongDidException
    """
    if data_source is DataSource.JIANYANYUAN:
        if len(dname) == 20 and dname.isdigit():
            return dname

    elif data_source is DataSource.XIAOMI:
        if dname.startswith('lumi') and len(dname) == 19:
            return dname

    raise WrongDidException


def device_source(dname: str) -> DataSource:
    for source in DataSource:
        try:
            d = device_check(dname, source)
            if isinstance(d, str):
                return source
        except WrongDidException:
            continue
    return DataSource.NONE


class SpotData(ABC):
    """
    A Factory
    Common interface for spot data from different sources.
    """
    token_fetch_error_msg: str = 'Token fetch Error: Token Error'
    datetime_time_eror_msg: str = 'Datetime error: Incorrect datetime'

    @abstractmethod
    def make_device_list(self) -> List:
        """
        Generate new device list.
        """

    @abstractmethod
    def spot(self) -> Optional[Generator]:
        """
        Get spot location information.
        It returns a generator of the list of spot location information
        value returned are used to fill `spot` table in database schema.
        """

    @abstractmethod
    def spot_record(self) -> Iterator[Callable[[], Optional[Generator]]]:
        """
        Get spot record data include temperature, humidity pm2.5 etc.
        value returned are used to fill `spot_record` table in database schema.
        """

    @abstractmethod
    def device(self) -> Optional[Generator]:
        """
        Get device information
        value returned will be used to fill `device` table in database schema.
        """

    @property  # type ignore
    @abstractmethod
    def normed_device_list(self) -> List:
        """ normalized device list """

    @property  # type: ignore
    @abstractmethod
    def app(self) -> Flask:
        """ app instance """
