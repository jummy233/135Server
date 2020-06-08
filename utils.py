from functools import partialmethod
from typing import Dict


def partialclass(cls, *args, **kwargs):
    class NewCls(cls):
        __init__ = partialmethod(cls.__init__, *args, **kwargs)

    return NewCls


def spread(*keys):
    """ usage:
    a, b, c = spread('a', 'b', 'c')({'a':1, 'b': 2})
    where a = 1, b = 2, c = None
    """
    def run(dictionary: Dict):
        return tuple(dictionary.get(key) for key in keys)
    return run
