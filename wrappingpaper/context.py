import functools
import contextlib
import wrappingpaper as wp


class ContextBase:
    '''Super basic boilerplate for context managers / file-like objects.
    '''
    def open(self):
        return self

    def close(self):
        return self

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class returngen(object):
    '''A wrapper that can iterate over and capture the return value from a
    generator.
    '''
    value = wp.EMPTY
    def __init__(self, g, default=None):
        self.g = g
        self.value = default

    def __iter__(self):
        self.value = yield from self.g


class withif:
    '''Skip body execution if an exception is thrown in __enter__ (sort of).
    The issue is that it will catch the exception you specify in the function
    body as well.

    I also haven't figured out how to bundle it with a context manager using
    a decorator or something so it can be run once at definition instead of
    using it at every incarnation.

    Usage:
    >>> @contextmanager
    ... def something():
    ...     raise ValueError

    >>> with wp.withif(ValueError), something():
    ...     print('I never get printed')
    '''
    def __init__(self, exc=None):
        self.exc = exc or Exception

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        return issubclass(exc_type, self.exc)
        # return True

    # @contextlib.contextmanager
    # def __call__(self):
    #     with self, self.context:
    #         yield



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
        if callable(self.caller):
            return self.caller(func, *self.a, **self.kw)

        @functools.wraps(self.func)
        def wrapper(*a, **kw):
            with self:
                return func(*a, **kw)
            return self.default_value
        return wrapper



# def contextfunc(func):
#     '''
#     @contextfunc
#     def reset():
#         obj.value = old_value
#
#     @reset.undo
#     def restore():
#         obj.value = new_value
#
#     with obj.reset(): # reset temporarily
#          pass
#
#     obj.reset() # reset permanently
#     '''
#     inner._return = None
#     def inner(*a, **kw):
#         inner._return = func(*a, **kw)
#         return inner._return
#
#     inner.__enter__ = lambda: inner._return
#     inner.__exit__ = lambda: inner.undo()
#
#     def undo(func=None):
#         if callable(func):
#             inner.undo = func
#             return func
#     inner.undo = undo



# class _Skip(Exception):
#     pass
#
# def contextflag(obj, name, value=True, default=None):
#     @contextmanager
#     def inner(value):
#         try:
#             notset = setattr(obj, name) != value
#             setattr(obj, name, value)
#             yield notset
#         finally:
#             setattr(obj, name, default)
#     return inner
