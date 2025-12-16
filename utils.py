from contextlib import contextmanager
from time import perf_counter

@contextmanager
def timed(msg='', width=40):
    start = perf_counter()
    yield lambda: stop - start
    stop = perf_counter()
    print(f"{msg:<{width}}{stop - start:.3f}s")
