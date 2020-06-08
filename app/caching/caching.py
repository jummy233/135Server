"""
LRU cache system
The core of the cache system is a orded dictionary which keep
track of the least used entry in a session.

Cache can be turned on in the app creation stage.
if turned on, all the database lookup will be redirect to cache lookup
first, and goes to the actually datbase only if it missed.

Whenever there is a new instance be broungt into ORM the object at the
end of the cache will be removed.
"""

from typing import Dict, Union, Optional, TypeVar, Generic
from collections import OrderedDict
from functools import wraps

##################
#  Cache system  #
##################

# cache can contains dictionary for long term caching
# and WeakValueDictionary for processing large data.

T = TypeVar('T')
U = TypeVar('U')
V = TypeVar('V')
N = TypeVar('N')


class _LRUDictionary(OrderedDict, Generic[U, V]):
    """
    LRU cache to hold for large amount of records.
    """

    def __init__(self, maxsize=3000, *args, **kwargs):
        self.maxsize = maxsize
        super().__init__(*args, **kwargs)

    def __getitem__(self, key: U) -> V:
        value: V = super().__getitem__(key)

        # reschedule.
        self.move_to_end(key)
        return value

    def __setitem__(self, key: U, value: V):
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest: U = next(iter(self))
            del self[oldest]


Cache = (Dict[T, Union[Dict[U, V], _LRUDictionary[U, V]]])


def empty_cache() -> Cache:
    """
    a dummy dictionary to represent
    an empty dict.
    works as a sentinel.
    """
    return dict()


def is_cache_empty(cache: Optional[Cache]):
    return cache == empty_cache() or cache is None


def pass_cache(cache: Cache = empty_cache()):
    """
    begining of cache decorator
    cache will be stored in the closure of decorator,
    One can create different closure to store different type
    of caches, and stack them up.
    """
    def decorator(f):
        @wraps(f)
        def _pass_cache(cache=cache, *args, **kwargs):
            return f(cache, *args, **kwargs)
        return _pass_cache
    return decorator


def get_cache(cache: Cache[T, U, V],
              category_key: T,
              key: Optional[U]) -> Optional[V]:
    """
    get cached value by CachyKey
    """
    if key is None:
        return None

    category = cache.get(category_key)

    if category is None:
        return None

    result = category.get(key)

    if result is None:
        return None

    return result
