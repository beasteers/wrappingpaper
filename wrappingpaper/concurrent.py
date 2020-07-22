import sys
import queue
import threading

FINISHED = object()


def _run_yield_worker(func, q, *a, **kw):
    try:
        for x in func(*a, **kw):
            q.put(x)
    except BaseException as e:
        e._sys_exec_info = sys.exc_info()
        q.put(e)
    finally:
        q.put(FINISHED)


def yieldq(func=None, timeout=None):
    def outer(func):
        def inner(*a, **kw):
            q = queue.Queue()
            t = threading.Thread(
                target=_run_yield_worker, args=(func, q) + a, kwargs=kw)
            t.start()

            def run():
                try:
                    while True:
                        x = q.get()
                        if x is FINISHED:
                            break
                        if isinstance(x, Exception):
                            raise x
                        yield x
                finally:
                    t.join(timeout)

            return generator(run(), thread=t, join=t.join)
        return inner
    return outer(func) if callable(func) else outer


class generator:
    '''A generator object with attributes.'''
    def __init__(self, it, **kw):
        self.__dict__.update(kw)
        self.it = iter(it)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.it)


if __name__ == '__main__':
    import time

    def asdf(t=0.2):
        for i in range(5):
            print(111, i)
            time.sleep(t)
            yield i


    asdf2 = yieldq(asdf)

    it = asdf()
    time.sleep(1)
    t0 = time.time()
    print('start iter')
    xs = list(it)
    print(time.time() - t0)

    it = asdf2()
    time.sleep(1)
    t0 = time.time()
    print('start iter')
    xs = list(it)
    print(time.time() - t0)
