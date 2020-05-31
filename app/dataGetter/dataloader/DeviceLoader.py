from queue import Queue
from typing import (Any, Callable, Dict, Generator, Generic, Iterator, List,
                    NewType, Optional, Tuple, Type, TypeVar, Union)
from app import db
from app.modelOperations import ModelOperations, commit
from app.models import ClimateArea, Device, Location, Project, Spot, SpotRecord
from functools import partial
from itertools import islice
from logging import DEBUG
from lazybox import LazyBox, LazyGenerator
from logger import make_logger
import threading
from concurrent_fetch import thread_fetcher
from app.dataGetter.dataloader.Actor import Actor

logger = make_logger('db_init', 'app_log', DEBUG)
T = TypeVar('T')
U = TypeVar('U')
Job = Callable[[], Optional[Generator[T, None, None]]]

