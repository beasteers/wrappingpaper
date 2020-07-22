import time
import functools
import itertools


def limit(it, n=None):
    '''Limit an iterator to n elements.'''
    return it if n is None else (x for i, x in zip(range(n), it))


def asfunc(it):
    '''Convert an iterable to a function that returns the next item.'''
    it = iter(it)
    return lambda: next(it)


def infinite(i=0, inc=1):
    '''Infinite generator. Turn a while loop into a for loop.'''
    while True:
        yield i
        i += inc

done = object()
def until(it):
    '''Mimic a while loop.'''
    for x in it:
        if x is done:
            break
        yield x


def _throttled(secs=1):
    '''Force an iterable to take at minimum x seconds.'''
    dt = asleep = 0
    while True:
        t0 = time.time()
        yield dt, asleep # time asleep
        if secs:
            dt = time.time() - t0
            asleep = max(secs - dt, 0)
            time.sleep(asleep)


def throttled(it=None, secs=1):
    '''Throttle an iterable so that it takes a minimum number of seconds
    per iteration.'''
    if it is not None:
        it = (x for x, _ in zip(it, _throttled(secs)))
    else:
        it = _throttled(secs)
    yield from it


def time_limit(it=None, secs=10):
    '''Set a time limit on an iterable. Exits the iterable after a certain
    amount of time.'''
    t0 = time.time()
    for x in it or infinite():
        yield x
        if time.time() - t0 > secs:
            break


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
        for _ in throttled(secs=throttle):
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


# def make_timeout(secs=None, stepped=False):
#     def check():
#         if secs is not None and time.time() - check.t0 > secs:
#             raise TimeoutError()
#         if stepped:
#             check.t0 = time.time()
#         return True
#     check.t0 = time.time()
#     return check

def _trigger_load(func):
    @functools.wraps(func)
    def inner(self, *a, **kw):
        if self._iterable is not None:
            it, self._iterable = self._iterable, None
            self.extend(it)
            self.loaded = True
        return func(self, *a, **kw)
    return inner

class lazylist(list):
    loaded = False
    def __init__(self, iterable):
        self._iterable = iterable
        super().__init__()

    __len__ = _trigger_load(list.__len__)
    __contains__ = _trigger_load(list.__contains__)
    __getitem__ = _trigger_load(list.__getitem__)
    __setitem__ = _trigger_load(list.__setitem__)
    __delitem__ = _trigger_load(list.__delitem__)
    __add__ = _trigger_load(list.__add__)
    __iadd__ = _trigger_load(list.__iadd__)
    __mul__ = _trigger_load(list.__mul__)
    __imul__ = _trigger_load(list.__imul__)
    __reversed__ = _trigger_load(list.__reversed__)
    append = _trigger_load(list.append)
    extend = _trigger_load(list.extend)
    copy = _trigger_load(list.copy)
    count = _trigger_load(list.count)
    index = _trigger_load(list.index)
    insert = _trigger_load(list.insert)
    pop = _trigger_load(list.pop)
    remove = _trigger_load(list.remove)
    reverse = _trigger_load(list.reverse)
    sort = _trigger_load(list.sort)

    # def __mul__(self, other):
    #     if self._iterable is not None:
    #         self._iterable = (
    #             x for xs in itertools.repeat(self._iterable, other) for x in xs)
    #     return super().__mul__(other)
    #
    # def __rmul__(self, other):
    #     return other.__mul__(self)

    # def insert(self, pos, element):
    #     if super().__len__() <

    def clear(self):
        self._iterable = None
        return super().clear()
