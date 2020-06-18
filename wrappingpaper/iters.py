import time
import itertools
from . import misc


def limit(it, n=None):
    return it if n is None else (x for i, x in zip(range(n), it))


def asfunc(it):
    it = iter(it)
    return lambda: next(it)


def infinite(i=0, inc=1):
    '''Infinite generator. Turn a while loop into a for loop.'''
    while True:
        yield i
        i += inc


def throttled(seconds=1):
    '''Force an iterable to take at minimum x seconds.'''
    dt = asleep = 0
    while True:
        t0 = time.time()
        yield dt, asleep # time asleep
        if seconds:
            dt = time.time() - t0
            asleep = max(seconds - dt, 0)
            time.sleep(asleep)


def pre_check_iter(it, n=1):
    '''Check the value first n items of an iterator without unloading them
    from the iterator queue.'''
    it = iter(it)
    items = [_ for i, _ in zip(range(n), it)]
    return items, itertools.chain(items, it)


def run_iter_forever(get_iter, none_if_empty=None, throttle=None, timeout=None):
    '''Return a never ending iterable.

    Arguments:
        get_iter (func): creates a new iterator.
        none_if_empty (bool, optional): if True, return None on an empty iterator.
        as_func (bool): whether to return an iterator or it.__next__
        throttle (float): throttle to make sure iterations aren't faster than
            `throttle` seconds.
        timeout (float): if no iterations are produced for x seconds, return None.
    '''
    required_item = int(bool(none_if_empty or timeout))
    def forever():
        t0 = timeout and time.time()
        for _ in throttled(throttle):
            # get the iterator and see if it has at least n items
            items, it = pre_check_iter(get_iter() or (), required_item)

            # check if iterable is considered empty and should yield None
            if len(items) >= required_item:
                # yield iterator items
                t0 = timeout and time.time()
                yield from it
            elif none_if_empty or timeout and time.time() - t0 > timeout:
                yield None
    return forever()
