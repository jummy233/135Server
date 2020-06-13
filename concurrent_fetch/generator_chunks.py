from itertools import islice, chain
from typing import Iterator, Generator


def chunks(it: Iterator, size=5) -> Generator:
    while True:
        try:
            yield chain((next(it),), islice(it, size - 1))
        except StopIteration:
            return
