"""
Separate elements in generator into sub iterators.
Better for concurrent eval.
"""

from itertools import islice
from copy import copy
from typing import (
    Iterator, Generator, List, Any, Tuple,
    TypeVar, Generic, Iterable, Union)


T = TypeVar('T')


class Mono(List[T]):
    """ list garantee has only one element """

    max_len = 1

    def __init__(self, data: Union[Iterable[T], T]):
        if isinstance(data, Iterable):
            super().__init__(copy(data))
        else:  # avoid evaluate argument
            super().__init__([copy(data)])

    def __setitem__(self, key, value):
        if key != 0:
            raise ValueError
        super().__setitem__(key, value)

    def __getitem__(self, key):
        if key != 0:
            raise ValueError
        return super().__getitem__(key)

    def mutate(self, data):
        self.__setitem__(0, data)

    def append(self, data):
        """ append only mutate data """
        self.mutate(data)

    def extend(self, data):
        self.mutate(data)

    def eval(self):
        return self.__getitem__(0)


class LazyBox(Iterator[T]):
    """ iterator with only 1 element """

    def __init__(self, data: Union[Iterable[T], T]):
        self.lazybox: Iterator[T] = iter(Mono(data))

    def __iter__(self):
        return self

    def __next__(self):
        """ fetch from lazy box """
        return next(self.lazybox)

    def eval(self) -> T:
        # next can contain state.
        try:
            res = next(self)
        except StopIteration:
            raise

        return res


class LazyGenerator(Generator[LazyBox[T], None, None]):
    islice_bound: Tuple[int, int] = (0, 1)

    def __init__(self, data: Iterator):
        """ make Generator that yield LazyBox once at a time """
        self.lazy_generator = self._be_lazy(data)

        self.count = 0

    def __next__(self):
        return next(self.lazy_generator)

    def __iter__(self):
        return self

    def send(self):
        pass

    def throw(self):
        pass

    def close(self):
        self.lazy_generator.close()

    def _be_lazy(self, data: Iterator[T]) -> Generator[LazyBox, None, None]:
        try:
            while True:  # slice the iter rather than eval it.

                yield LazyBox(islice(data, *LazyGenerator.islice_bound))

        except StopIteration:
            return

