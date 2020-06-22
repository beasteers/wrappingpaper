import time
from functools import wraps
from .context import contextdecorator
from . import iters
from .exceptions import CircularReference

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


def retry_on_failure(n=5, exc=Exc):
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


def default_value(value, exc=Exc):
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




#################################
# Circular Dependency Checking
#################################

@contextdecorator
def check_circular(refs, value):
    '''A contextmanager that detects if a circular reference is used.

    Arguments:
        refs (list): the reference to the circular stack
        value (any): the indentifier used to detect circular

    Yields:
        is_circular (bool)

    Examples:
    >>> crefs = []
    >>> def asdf(x):
    ...     with wp.check_circular(crefs, x) as is_circle:
    ...         if is_circle:
    ...             print("I'm getting dizzy!")
    ...             return x
    ...         return asdf((x + 1) % 10)

    >>> assert asdf(0) == 0 # full circle
    '''
    try:
        is_circle = value in refs
        refs.append(value)
        yield is_circle
    finally:
        assert refs.pop() == value # NOTE: this should always be true ????

@contextdecorator
def prevent_circular(refs, value):
    '''A contextmanager that detects if a circular reference is used.

    Arguments:
        refs (list): the reference to the circular stack
        value (any): the indentifier used to detect circular

    Raises:
        CircularReference: if is_circular is True

    Examples:
    >>> crefs = []
    >>> def asdf(x):
    ...     with wp.prevent_circular(crefs, x):
    ...         return asdf((x + 1) % 10)

    >>> asdf(0) # throws CircularReference

    >>> # as a decorator
    >>> @wp.prevent_circular()
    >>> def asdf2(x):
    ...     return asdf((x + 1) % 10)

    >>> asdf(0) # throws CircularReference
    '''
    with check_circular(refs, value) as is_circle:
        if is_circle:
            raise CircularReference(
                'circular reference ({}) - reference stack: {}'.format(value, refs))
        yield

@prevent_circular.caller
def prevent_circular(func, getvalue=None):
    getvalue = getvalue or (lambda *a, **kw: a)
    refs = []
    def inner(*a, **kw):
        with prevent_circular(refs, getvalue(*a, **kw)):
            return func(*a, **kw)
    return inner

def prevent_circular_caller(func):
    '''Prevent calling a function inside itself.'''
    return prevent_circular(lambda *a, **kw: func.__name__)(func)
