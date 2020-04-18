from abc import ABC, abstractmethod
import enum
from datetime import datetime as dt
from typing import (Any, Callable, Dict, Generator, Iterator, List, NewType,
                    Optional, Tuple, TypedDict, Union, cast)

LazySpotRecord = Callable[[], Optional[Generator]]


class DataSource(enum.Enum):
    JIANYANYUAN = 0
    XIAOMI = 1


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
    online: Union[int, bool, None]
    create_time: Optional[dt]
    modify_time: Optional[dt]


class SpotData(ABC):
    """
    A Factory
    Common interface for spot data from different sources.
    """
    token_fetch_error_msg: str = 'Token fetch Error: Token Error'
    datetime_time_eror_msg: str = 'Datetime error: Incorrect datetime'

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

