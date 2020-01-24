from queue import Queue
from typing import TypeVar, Callable
from multiprocessing.pool import Pool

from logger import make_logger
logger = make_logger('concurrent_consume', 'concurrent_fetch_log')
logger.propagate = False


def process_consumer(consumer: Callable[[Queue], None],
                     queue: Queue) -> None:
    with Pool(6) as pool:
        pool.map(consumer, (queue for _ in range(queue.qsize())))

