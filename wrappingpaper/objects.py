from types import ModuleType, FunctionType
from collections import ChainMap


# class snitch:
#     def __getattribute__(self, k):
#         print('snitch ({}.__getattribute__): {}'.format(type(self), k))
#         return super().__getattribute__(k)
#
#
# def make_snitch(cls):
#     return type(cls.__name__, (snitch, cls), {})


class dictproxy(ChainMap, dict):
    pass


# class Mask:
#     def __init__(self, base):
#         self.__class__ = type(
#             base.__class__.__name__,
#             (self.__class__, base.__class__), {})
#         self.__dict__ = dictproxy(self.__dict__, base.__dict__)


def copyobject(obj, **kw):
    '''Make a quick copy of an object.'''
    new = obj.__class__.__new__(obj.__class__)
    new.__dict__.update(obj.__dict__, **kw)
    return new


class namespace(type):
    '''A python module, defined like a class.
    Source: http://code.activestate.com/recipes/578279-using-chainmap-for-embedded-namespaces/

    Example:
    >>> class something(metaclass=wp.namespace):
    ...     a = 10
    ...     b = 11
    ...     def blah():
    ...         return a + b

    >>> assert something.blah() == 10+11
    '''
    def __new__(cls, name, bases, dict):
        mod = ModuleType(name, dict.get("__doc__"))
        for key, obj in dict.items():
            if isinstance(obj, FunctionType):
                obj = cls.scoped_function(cls, obj, mod.__dict__)
            mod.__dict__[key] = obj
        return mod

    def scoped_function(cls, func, d):
        d = dictproxy(d, func.__globals__)
        newfunc = FunctionType(func.__code__, d)
        newfunc.__name__ = func.__name__
        newfunc.__doc__ = func.__doc__
        newfunc.__defaults__ = func.__defaults__
        newfunc.__kwdefaults__ = func.__kwdefaults__
        newfunc.__scope__ = d
        return newfunc
