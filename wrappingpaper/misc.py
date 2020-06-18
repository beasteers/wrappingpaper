import time
from functools import wraps
from .context import contextdecorator
from . import iters

Exc = Exception


@contextdecorator
def ignore(exc=Exc):
    '''Ignore exception raised.'''
    try:
        yield
    except exc:
        pass

def throttle_exception(seconds, exc=Exc):
    '''Throttle a function if an exception was raised. Useful for retrying on
    failure.'''
    def outer(func):
        def inner(*a, **kw):
            try:
                t0 = time.time()
                return func(*a, **kw)
            except exc as e:
                time.sleep(max(0, seconds - (time.time() - t0)))
                raise e
        return inner
    return outer


def retry_on_failure(n=5, exc=Exception):
    def outer(func):
        class X: pass
        def inner(*a, **kw):
            X.e = Exception('Retried {} times.'.format(n))
            for _ in iters.limit(iters.infinite(), n):
                try:
                    return func(*a, **kw)
                except exc as e:
                    X.e = e
                    continue
            raise X.e
        return inner
    return outer


def default_value(value, exc=Exception):
    '''Return a default value if an exception was raised.'''
    def outer(func):
        @wraps(func)
        def inner(*a, **kw):
            try:
                return func(*a, **kw)
            except exc:
                return value() if callable(value) else value
        return inner
    return outer
