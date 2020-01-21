""" cache system """

from weakref import WeakValueDictionary
from typing import Dict, Optional, Union, Tuple, NewType, Optional, Any, TypeVar, Generic
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


class _WeakValueDictionaryType(Generic[U, V], WeakValueDictionary):
    ...


Cache = (
    Dict[
        T,

        Union[
            Dict[U, V],

            _WeakValueDictionaryType[U, V]
        ]
    ]
)


def empty_cache() -> Cache:
    return dict()


def is_cache_empty(cache: Optional[Cache]):
    return cache == empty_cache() or cache is None


def pass_cache(cache: Cache = empty_cache()):
    """ begining of cache decorator """
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



