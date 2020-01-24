from itertools import islice, chain
from typing import Iterable, Generator


def chunks(it: Iterable, size=5) -> Generator:
    for head in it:
        yield chain([head], islice(it, size - 1))
