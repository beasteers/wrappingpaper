from functools import wraps
import contextlib


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
    @wraps(func)
    def inner(*a, **kw):
        cm = _ContextDecorator(func, *a, **kw)
        cm.wrapper = inner.wrapper
        return cm
    inner.wrap = setter(inner, 'wrapper')
    return inner


def setter(obj, attr, default=None):
    def inner(value):
        setattr(obj, attr, value)
    inner(default)
    return inner


class _ContextDecorator(contextlib._GeneratorContextManager):
    '''Helper for @contextdecorator decorator.'''
    wrapper = None
    def __init__(self, func, *a, **kw):
        self.func, self.a, self.kw = func, a, kw
        self.__doc__ = getattr(func, "__doc__", None) or type(self).__doc__

    def __enter__(self):
        self.gen = self.func(*self.a, **self.kw)
        try:
            return next(self.gen)
        except StopIteration:
            raise RuntimeError("generator didn't yield") from None

    def __call__(self, func):
        @wraps(func)
        def inner(*a, **kw):
            with self:
                return func(*a, **kw)
        return self.wrapper(inner) if callable(self.wrapper) else inner
