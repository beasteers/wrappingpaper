import functools
import contextlib
import wrappingpaper as wp


def contextdecorator(func):
    '''Like contextlib.contextmanager, but the wrapped function also
    doubles as a decorator.

    Example:

        @contextdecorator
        def blah(a, b): # classdecorator.inner
            print(a)
            yield
            print(b)

        @blah(4, 5) # ContextDecorator.__init__
        def xyz(): # ContextDecorator.__call__
            print(1)
        xyz() # ContextDecorator.__call__.inner
        # prints 4, 1, 5

        with blah(4, 5): # ContextDecorator.__init__, ContextDecorator.__enter__
            print(1)
        # prints 4, 1, 5
    '''
    @functools.wraps(func)
    def inner(*a, **kw):
        cm = _ContextDecorator(func, *a, **kw)
        cm.caller = inner._caller
        return cm
    inner.caller = _setter(inner, '_caller')
    return inner


def _setter(obj, attr, default=None):
    def inner(value):
        setattr(obj, attr, value)
        return obj
    inner(default)
    return inner


class returngen(object):
    value = wp.EMPTY
    def __init__(self, g, default=None):
        self.g = g
        self.value = default

    def __iter__(self):
        self.value = yield from self.g


class _ContextDecorator(contextlib._GeneratorContextManager):
    '''Helper for @contextdecorator decorator.'''
    caller = None
    _gen = gen = None
    def __init__(self, func, *a, **kw):
        self.func, self.a, self.kw = func, a, kw
        functools.update_wrapper(self, func)

    @property
    def default_value(self):
        if self._gen and self._gen.value is not wp.EMPTY:
            return self._gen.value

    def __enter__(self):
        self._gen = returngen(self.func(*self.a, **self.kw), wp.EMPTY)
        self.gen = iter(self._gen)
        try:
            return next(self.gen)
        except StopIteration:
            raise RuntimeError("generator didn't yield") from None

    def __call__(self, func):
        print(456456, func, self.caller)
        if callable(self.caller):
            return self.caller(func, *self.a, **self.kw)

        @functools.wraps(self.func)
        def wrapper(*a, **kw):
            with self:
                return func(*a, **kw)
            return self.default_value
        return wrapper
