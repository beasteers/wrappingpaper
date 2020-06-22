import functools
import wrappingpaper as wp


class cachedproperty:
    """A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property."""
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func
        self.cacheid = '_cached~{}'.format(self.func.__name__)
        functools.update_wrapper(self, func)

    def __get__(self, obj, cls):
        d = obj.__dict__
        if self.cacheid not in d:
            d[self.cacheid] = self.func(obj)
        return d[self.cacheid]

    def __delete__(self, obj):
        d = obj.__dict__
        if self.cacheid in d:
            del d[self.cacheid]


class onceproperty:
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func
        self.value = wp.EMPTY
        functools.update_wrapper(self, func)

    def __get__(self, obj, cls):
        if self.value is wp.EMPTY:
            self.value = self.func(obj)
        return self.value

    def __delete__(self, obj):
        self.value = wp.EMPTY


class overridable_property:
    def __init__(self, func):
        self.name = getattr(func, '__name__', None) or 'func{}'.format(id(func))
        self.__doc__ = (
            getattr(func, '__doc__', None) or
            'Overridable Property: {}'.format(self.name))
        self.value_name = '_{}'.format(self.name)
        self.func = func
        self.unset = None
        functools.update_wrapper(self, func)

    def __get__(self, obj, cls):
        value = getattr(obj, self.value_name, self.unset)
        return self.func(obj) if value is self.unset else value

    def __set__(self, obj, value):
        setattr(obj, self.value_name, value)

    def __delete__(self, obj):
        setattr(obj, self.value_name, self.unset)


class classinstancemethod:
    '''A method that works as both a classmethod and an instance method.'''
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)

    def __get__(self, instance, owner=None):
        return self.func.__get__(owner if instance is None else instance)


class _propobject:
    '''A property that can have it's own methods with access to
    instance and owner.'''
    def __init__(self, func, instance=None, owner=None):
        self.func, self.instance, self.owner = func, instance, owner
        functools.update_wrapper(self, func)

    @property
    def target(self):
        return (
            self.instance if self.instance is not None else
            self.owner if self.owner is not None else self.func)

    def __get__(self, instance, owner=None):
        return wp.copyobject(self, instance=instance, owner=owner)

    def __call__(self, *a, **kw):
        return self.func(self.target, *a, **kw)


class overridable_method(_propobject):
    '''
    class A:
        on_call = wp.instancedef('_on_call')

        @wp.instancedef
        def on_write(self): # default
            with self:
                print(0, 1)

        def asdf(self):
            self._on_call()

    a = A()

    @a.on_call.define
    def on_call(self):
        with self:
            print(1, 2, 3)

    a.asdf()

    '''
    def __init__(self, func, **kw):
        self.name = '_' + func.__name__
        super().__init__(func, **kw)

    def _(self, func):
        setattr(self.target, self.name, func)
        return self

    def __call__(self, *a, **kw):
        obj = self.target
        func = getattr(obj, self.name, None) or self.func.__get__(obj)
        return func(*a, **kw)

    def reset(self):
        delattr(self.target, self.name)
