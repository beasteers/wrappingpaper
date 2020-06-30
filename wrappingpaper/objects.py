from types import ModuleType, FunctionType
from collections import ChainMap
import wrappingpaper as wp

class snitch:
    def __getattribute__(self, k):
        print('snitch ({}.__getattribute__): {}'.format(type(self), k))
        return super().__getattribute__(k)


def make_snitch(cls):
    return type(cls.__name__, (snitch, cls), {})


class dictproxy(ChainMap, dict):
    def add(self, *cfg):
        for d in cfg:
            self.maps.append(d)
        return self

    def set(self, *cfg):
        for d in cfg[::-1]:
            self.maps.insert(0, d)
        return self


class attrdict(dictproxy):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, name):
        try:
            items = (d[name] for d in self.maps if name in d)
            item = next(items)
            if isinstance(item, dict):
                item = attrdict(
                    item, *wp.until(
                        d if isinstance(d, dict) else wp.done
                        for d in items))
            return item
        except StopIteration:
            raise KeyError(name)




# class Mask:
#     def __init__(self, base):
#         self.__class__ = type(
#             base.__class__.__name__,
#             (self.__class__, base.__class__), {})
#         self.__dict__ = dictproxy(self.__dict__, base.__dict__)


def all_subclasses(cls):
    '''Recursively return all subclasses of a class.'''
    return set(cls.__subclasses__()).union([
        s for c in cls.__subclasses__() for s in all_subclasses(c)])


def copyobject(obj, **kw):
    '''Make a quick copy of an object.'''
    new = obj.__class__.__new__(obj.__class__)
    new.__dict__.update(obj.__dict__, **kw)
    return new


def monkeypatch(obj, name=None, prefix='_monkey_patched_'):
    def inner(func, name=name):
        name = name or func.__name__

        # get the old function and save on new object
        func.super = oldfunc = getattr(obj, name, None)
        if oldfunc is not None:
            setattr(obj, prefix + name, func)
        # patch in new function
        setattr(obj, name, func)

        # add method to reset function
        def reset():
            setattr(obj, name, oldfunc)
            return func
        func.reset = reset

        def repatch():
            setattr(obj, name, func)
            return func
        func.repatch = repatch
        return func
    return inner


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
    class Module(ModuleType):
        def keys(self):
            return [
                k for k in self.__dict__.keys()
                if not k.startswith('__')]

        def __getitem__(self, k):
            return self.__dict__[k]

    def __new__(cls, name, bases, dct):
        mod = cls.Module(name, dct.get("__doc__"))
        for key, obj in dct.items():
            if isinstance(obj, FunctionType):
                obj = modfuncglobals(obj, mod.__dict__)
            mod.__dict__[key] = obj
        return mod



def modfuncglobals(func, *ds, **kw):
    '''Add globals to a function.'''
    dp = dictproxy()
    newfunc = FunctionType(func.__code__, dictproxy(dp, func.__globals__))
    newfunc.__name__ = func.__name__
    newfunc.__doc__ = func.__doc__
    newfunc.__defaults__ = func.__defaults__
    newfunc.__kwdefaults__ = func.__kwdefaults__
    newfunc.__scopes__ = dp.maps

    def add(*ds, **kw):
        for d in ds[::-1]:
            newfunc.__scopes__.insert(0, d)
        if kw:
            newfunc.add(kw)
        return newfunc
    newfunc.add = add
    newfunc.add(*ds, **kw)
    return newfunc


def unbound(f):
    '''Get the unbound version of a method.
    i.e. `assert unbound(func.__get__(self)) == func`
    '''
    self = getattr(f, '__self__', None)
    if self is not None and not isinstance(self, (type, ModuleType)):
        if hasattr(f, '__func__'):
            return f.__func__
        return getattr(type(f.__self__), f.__name__)
    raise TypeError('not a bound method')
