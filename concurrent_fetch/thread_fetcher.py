from threading import Thread, Lock
from queue import Queue
from typing import TypeVar, Iterable, Callable, List, cast
from itertools import islice
from .generator_chunks import chunks

from logger import make_logger
logger = make_logger('concurrent_fetch', 'concurrent_fetch_log')
logger.propagate = False


T = TypeVar("T")
LazyBox = Iterable  # iter with only one element. for lazy eval
JobBox = LazyBox[T]


def thread_fetcher(jobs: Iterable[Callable[[], T]],
                   max_thread: int,
                   fetcher: Callable[[Queue, Callable[[], T], Lock], None],
                   consumer: Callable[[Queue], None] = lambda q: None,
                   before_consume_hook: Callable = lambda: None,
                   after_consume_hook: Callable = lambda: None) -> None:
    """
    Threaded worker for data fetching

    All evaluation of generators happens in worker so the
    work load of side effect can be properly splited.

    @param jobs: An iterator of tasks. Can contain huge side effects to iter.
    @param max_thread: number of threads to spawn.

    @param fetcher: fetcher to fetch data. take in a chunk of job
    @param consumer: consume data.

    @param before_consume_hook: callback called after consume.
    @param after_consume_hook: callback called after consume.

    """
    logger.info('start threaded fetcher')

    queue: Queue = Queue()

    try:
        idx = 0
        while True:
            subjobs = next(chunks(jobs, max_thread))

            logger.info(f"chunk {idx} Started ----->")

            _spawn_threads(subjobs, queue, fetcher)

            before_consume_hook()

            logger.info('running consumer')

            consumer(queue)

            after_consume_hook()

            idx += 1
            logger.info(f"chunk {idx} Finshed ----->")

    except StopIteration:
        logger.info("all jobs done")


def _spawn_threads(subjobs: LazyBox[Callable[[], T]],
                   queue: Queue,
                   fetcher: Callable[[Queue, Callable[[], T], Lock], None]
                   ) -> None:

    """
    take iterator, slice it into LazyBox and dispatch to workers
    """
    threads: List[Thread] = list()
    lock: Lock = Lock()

    for idx, job in enumerate(subjobs):  # pass slice of one element.

        cast(JobBox, job)

        t = Thread(target=fetcher, args=(queue, job, lock))
        threads.append(t)
        t.start()
        logger.debug(f'Thread {idx} started')

    for idx, t in enumerate(threads):

        t.join()
        logger.debug(f"Thread {idx} joined")
