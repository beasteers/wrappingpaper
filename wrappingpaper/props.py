
EMPTY = object()

class cachedproperty:
    """A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property."""
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func
        self.cacheid = '_cached~{}'.format(self.func.__name__)

    def __get__(self, obj, cls):
        d = obj.__dict__
        if self.cacheid not in d:
            d[self.cacheid] = self.func(obj)
        return d[self.cacheid]

class onceproperty:
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func
        self.value = EMPTY

    def __get__(self, obj, cls):
        if self.value is EMPTY:
            self.value = self.func(obj)
        return self.value

class overrideable_property:
    def __init__(self, func):
        self.name = getattr(func, '__name__', None) or 'func{}'.format(id(func))
        self.__doc__ = (
            getattr(func, '__doc__', None) or
            'Overridable Property: {}'.format(self.name))
        self.value_name = '_{}'.format(self.name)
        self.func = func
        self.unset = None

    def __get__(self, obj, cls):
        value = getattr(obj, self.value_name, self.unset)
        return self.func(obj) if value is self.unset else value

    def __set__(self, obj, value):
        setattr(obj, self.value_name, value)
