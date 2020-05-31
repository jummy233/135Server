from collections import defaultdict
from typing import Dict, Set, Tuple, Sequence
from contextlib import contextmanager


class Exchange:

    def __init__(self):
        self._subscriber: Set = set()

    def attach(self, task):
        self._subscriber.add(task)

    def detach(self, task):
        self._subscriber.remove(task)

    @contextmanager
    def subsribe(self, *tasks):
        for task in tasks:
            self.attach(task)
        try:
            yield
        finally:
            for task in tasks:
                self.detach(task)

    def send(self, msg):
        for subsriber in self._subscriber:
            subsriber.send(msg)


class UpdateExchange(Exchange):
    pass


class ProbeExchange(Exchange):
    pass



