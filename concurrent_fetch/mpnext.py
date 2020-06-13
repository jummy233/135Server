from multiprocessing.pool import Pool
from multiprocessing import Queue
from typing import Iterator


q: Queue = Queue()


def mptraversal(jobs) -> Iterator:
    """
    traversal a iter and put the data into queue.
    it's helpful to evaluated a generator contains
    computation.
    """
    with Pool(5) as pool:
        pool.map(put_in_queue, jobs)
    print(q.qsize())
    q.put(None)
    return iter(q.get, None)


def put_in_queue(chunks: Iterator):
    for ch in chunks:
        q.put(ch)
