import functools
import wrappingpaper as wp



class _prop:
    '''A method that works as both a classmethod and an instance method.'''
    def __init__(self, func):
        self.__func__ = func
        functools.update_wrapper(self, func)

    def __get__(self, instance, owner=None):
        return self.__func__.__get__(instance, owner)

    def __gettarget__(self, obj=None, cls=None):
        return next((
            x for x in (obj, cls, self.__func__)
            if x is not None), self)


class cachedproperty(_prop):
    """A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property."""
    __unset__ = wp.EMPTY
    __hidden_name__ = None
    def __init__(self, func):
        super().__init__(func)
        if self.__hidden_name__ is None:
            self.__hidden_name__ = '_cached~{}'.format(func.__name__)

    def __get__(self, obj, cls):
        obj = self.__gettarget__(obj, cls)
        value = getattr(obj, self.__hidden_name__, self.__unset__)
        if value is self.__unset__:
            value = self.__func__(obj)
            setattr(obj, self.__hidden_name__, value)
        return value

    def __set__(self, obj, value):
        obj = self.__gettarget__(obj)
        if self.__hidden_name__ and obj is not None:
            setattr(obj, self.__hidden_name__, value)

    def __delete__(self, obj):
        obj = self.__gettarget__(obj)
        if self.__hidden_name__ and obj is not None:
            delattr(obj, self.__hidden_name__)


class onceproperty(cachedproperty):
    '''A property that is only run once. The value is cached on the class object.'''
    __hidden_name__ = '__value__'

    def __gettarget__(self, obj=None, cls=None):
        return self


class overridable_property(cachedproperty):
    '''A property that works like a normal property, but can be overridden.'''
    __unset__ = None

    def __get__(self, obj, cls):
        obj = self.__gettarget__(obj)
        value = getattr(obj, self.__hidden_name__, self.__unset__)
        return self.__func__(obj) if value is self.__unset__ else value


class classinstancemethod(_prop):
    '''A method that works as both a classmethod and an instance method.'''
    def __get__(self, instance, owner=None):
        return self.__func__.__get__(self.__gettarget__(instance, owner))


class propobject:
    '''A property that can have it's own methods with access to
    instance and owner.'''
    __hidden_name__ = None
    def __init__(self, func=None, __instance__=None, __owner__=None):
        self.__func__, self.__instance__, self.__owner__ = func, __instance__, __owner__
        if callable(func):
            functools.update_wrapper(self, func)

        if self.__hidden_name__ is None:
            name = getattr(func, '__name__', None) or 'func{}'.format(id(func))
            self.__hidden_name__ = '_{}_prop_'.format(name)

    @property
    def __target__(self):
        return next((
            x for x in (self.__instance__, self.__owner__, self.__func__)
            if x is not None), self)

    @property
    def __method__(self):
        return self.__func__.__get__(self.__target__)

    def __get__(self, instance, owner=None):
        return self._store_as_attr(
            instance if instance is not None else owner,
            self.__hidden_name__,
            lambda: self._bind_instance(instance, owner))

    def _bind_instance(self, instance, owner=None):
        prop = self._new(__instance__=instance, __owner__=owner)
        prop.__init_instance__()
        return prop

    def __init_instance__(self):
        pass

    def _new(self, **kw):
        return wp.copyobject(self, **kw)

    def __call__(self, *a, **kw):
        if callable(self.__func__):
            return self.__method__(*a, **kw)


    def _store_as_attr(self, obj, name, get_value, check_type=True):
        # check for existing
        if name and obj is not None:
            prop = getattr(obj, name, None)
            if prop is not None and (
                    not check_type or isinstance(prop, self.__class__)):
                return prop
        # set existing
        prop = get_value()
        if name and obj is not None:
            setattr(obj, name, prop)
        return prop



# class patchprop(propobject):
#     '''A settable property where you can override attributes on the child object.
#     '''
#     def __init__(self, default=wp.UNSET, **kw):
#         self.value = default
#         super().__init__(**kw)
#
#     def __init_instance__(self):
#         self.value = self._get_value()
#
#     def __get__(self, instance, owner=None):
#         if self.value is wp.UNSET:
#             raise AttributeError # how to get key name ???
#         return super().__get__(instance, owner)
#
#     def __set__(self, instance, value):
#         self.value = value
#
#     def __getattr__(self, name):
#         return getattr(self.value, name)
#
#     def __dir__(self):
#         return dir(self.value)


class flag:
    '''A

    Example:
    >>> class A:
    ...     should_print = flag(2, skip=8)

    >>> def asdf(x):
    ...     if A.should_print:
    ...         print('calling asdf with', x)
    >>> for x in range(20):
    ...     print(x)
    calling asdf with 0
    calling asdf with 8
    calling asdf with 16
    '''
    def __init__(self, n=1, check=None, skip=None):
        self.check = check if callable(check) else (
            lambda flag: flag.count and not flag.n_called % flag.skip)
        self.count = n
        self.n_called = 0
        self.skip = skip or 1

    @property
    def dec(self):
        try:
            if self:
                self.count = max(0, self.count - 1)
                return True
        finally:
            self.n_called += 1

    @property
    def inc(self):
        self.count += 1
        return bool(self)

    def __bool__(self):
        return bool(self.check(self))
    __nonzero__ = __bool__


# class jinjaprop(overridable_property):
#     '''
#     class Block:
#         ext = 'csv'
#
#         @jinjaprop
#         def filename(self, data, meta):
#             return '{}.{}'.format(
#                 os.path.splitext(meta['filename'])[0],
#                 self.ext.rstrip('.'))
#
#     '''
#     def __get__(self, obj, cls):
#         value = super().__get__(obj, cls)
#         if isinstance(value, str):
#             value = self.env.from_string(value)
#         return value



# class overridable_method(propobject):
#     '''
#     class A:
#         on_call = wp.instancedef('_on_call')
#
#         @wp.instancedef
#         def on_write(self): # default
#             with self:
#                 print(0, 1)
#
#         def asdf(self):
#             self._on_call()
#
#     a = A()
#
#     @a.on_call.define
#     def on_call(self):
#         with self:
#             print(1, 2, 3)
#
#     a.asdf()
#
#     '''
#     def __init__(self, func, **kw):
#         self.name = '_' + func.__name__
#         super().__init__(func, **kw)
#
#     def _(self, func):
#         setattr(self.__target__, self.name, func)
#         return self
#
#     def __call__(self, *a, **kw):
#         obj = self.__target__
#         func = getattr(obj, self.name, None) or self.__method__
#         return func(*a, **kw)
#
#     def reset(self):
#         delattr(self.__target__, self.name)
