
from typing import Optional, Callable, Tuple, NewType, Union, cast, Any, overload
from .caching import is_cache_empty, pass_cache, empty_cache
from .caching import Cache, _LRUDictionary
from .cache_instance import CacheInstance
from functools import wraps
from enum import Enum
import logging
from copy import copy
from datetime import datetime as dt
from ..models import User, Location, Project, ProjectDetail
from ..models import ClimateArea, Company, Permission
from ..models import OutdoorSpot, OutdoorRecord
from ..models import Spot, SpotRecord, Device
from ..models import Data


logging.basicConfig(level=logging.INFO)


class ModelDataEnum(Enum):
    _Project = 1
    _Spot = 2
    _Device = 3
    _Company = 4
    _Location = 5
    _ClimateArea = 6
    _OutdoorRecord = 7
    _OutdoorSpot = 8
    _SpotRecord = 9


GlobalCacheKey = Union[str, int, Tuple[dt, Device]]
GlobalCache = Cache[ModelDataEnum, GlobalCacheKey, Data]
CacheAllDecorator = Callable[..., Callable]

# expensive !


def cache_init_error_info(f):
    logging.error('cache init error')
    return f


@overload
def init_global_cache(cache_instance: CacheInstance) -> CacheInstance:
    ...


@overload
def init_global_cache(cache_instance: None) -> None:
    ...


def init_global_cache(cache_instance: Optional[CacheInstance]
                      ) -> Optional[CacheInstance]:
    """
    global cache facotory
    init_global_cache :: a -> b -> (a, b)
    @ very expensive
    """
    if cache_instance is None:
        return None

    if is_cache_empty(cache_instance.global_cache):

        logging.info('cache instance is empty, make a new one.')

        cache_instance.global_cache = empty_cache()

        # note cacheall is decorator
        cache_instance.global_cacheall = \
            make_cacheall(cache_instance.global_cache)

        return cache_instance

    logging.warning('globale cache is not empty, use existed cache')
    return None


def cache_project(f):
    @wraps(f)
    def cache_it(cache: Cache, *args, **kwargs):

        cache[ModelDataEnum._Project] = {}

        for v in Project.query.all():
            cache[ModelDataEnum._Project][v.project_name] = v

            cache[ModelDataEnum._Project][v.project_id] = copy(v)

        return f(cache, *args, **kwargs)
    return cache_it


def cache_device(f):
    @wraps(f)
    def cache_it(cache: Cache, *args, **kwargs):

        cache[ModelDataEnum._Device] = {}

        for v in Device.query.all():
            cache[ModelDataEnum._Device][v.device_name] = v

            cache[ModelDataEnum._Device][v.device_id] = copy(v)
        return f(cache, *args, **kwargs)
    return cache_it


def cache_spot(f):
    @wraps(f)
    def cache_it(cache: Cache, *args, **kwargs):

        cache[ModelDataEnum._Spot] = {}

        for v in Spot.query.all():
            cache[ModelDataEnum._Spot][v.spot_name] = v

            cache[ModelDataEnum._Spot][v.spot_id] = copy(v)
        return f(cache, *args, **kwargs)
    return cache_it


def cache_spot_record(f):
    logging.info('caching...')

    @wraps(f)
    def cache_it(cache: Cache, *args, **kwargs):
        maxsize: int = 50000

        cache[ModelDataEnum._SpotRecord] = cast(
            _LRUDictionary[dt, Device],
            _LRUDictionary(maxsize=maxsize))

        for v in SpotRecord.query.limit(maxsize).all():
            (
                cache[ModelDataEnum._SpotRecord]
                [(v.spot_record_time, v.device)]
            ) = v

        return f(cache, *args, **kwargs)
    return cache_it


def make_cacheall(cache: Cache) -> Callable:
    """
    return a specialize cache decorator for database types.
    allow pass external cache
    by doing this wrapped operation can modify cache state.

    Usage:
    ```
        cache = empty_cache()
        cacheall = make_cacheall(cache)

        @cacheall
        def foo(): ...
    ```
    """
    logging.info('init caching......')

    @pass_cache(cache)
    @cache_project
    @cache_device
    @cache_spot
    @cache_spot_record
    def init_cache(cache: Cache):
        def _cachall_deco(f):
            logging.debug(
                'cache in cachhe decorator: {}'.format(
                    cache.keys()
                    if cache is not None
                    else 'empty')
            )

            @wraps(f)
            def _cacheall(cache=cache, *args, **kwargs):
                return f(cache, *args, **kwargs)
            return _cacheall
        return _cachall_deco

    return init_cache(cache)
