import os
import types
import inspect
import wrappingpaper as wp


class Preset(types.ModuleType):
    DISPATCH = {}
    DEFAULTS = {}

    def __init__(self, module, dispatch=None, defaults=None):
        self._module = module
        self.__dict__.update(module.__dict__)

        self.DISPATCH[module] = self._dispatch = (
            dispatch if dispatch is not None else
            self.DISPATCH[module] if module in self.DISPATCH else
            {module: self})

        self.DEFAULTS[module] = self._defaults = (
            defaults if defaults is not None else
            self.DEFAULTS[module] if module in self.DEFAULTS else
            {})

        @wp.monkeypatch(module.__loader__)
        def exec_module(module):
            exec_module.super(module)
            self._wrap_module(module)


    def __repr__(self):
        return f'<Preset \n\tfor={self._module} \n\tdefaults={self._defaults}>'


    def _wrap_module(self, module):
        modpath = os.path.dirname(inspect.getfile(module))

        # inspect the target module
        for attr, value in inspect.getmembers(module):
            # If it's a function, wrap it
            if callable(value):
                # Wrap the function in a decorator
                setattr(self, attr, self._wrap_func(value))

            # If it's a module, construct a parameterizer to wrap it
            elif (isinstance(value, types.ModuleType) and
                  hasattr(value, '__file__')):
                # test if this is a submodule of the current module
                submodpath = inspect.getfile(value)

                if os.path.commonprefix([modpath, submodpath]) == modpath:
                    if value not in self._dispatch:
                        # We need to pre-seed the dispatch entry to avoid
                        # cyclic references
                        self._dispatch[value] = None
                        self._dispatch[value] = Preset(
                            value, dispatch=self._dispatch,
                            defaults=self._defaults)

                    setattr(self, attr, self._dispatch[value])
                else:
                    setattr(self, attr, value)

    def _wrap_func(self, func):
        wrapped = wp.configfunction(func)
        wrapped.add(self._defaults)
        wrapped.__doc__ = (
            'WARNING: this function has been modified by the Presets '
            'package.\nDefault parameter values described in the '
            'documentation below may be inaccurate.\n\n{}'.format(wrapped.__doc__))
        return wrapped

    def __getitem__(self, param):
        return self._defaults[param]

    def __delitem__(self, param):
        del self._defaults[param]

    def __contains__(self, param):
        return param in self._defaults

    def __setitem__(self, param, value):
        self._defaults[param] = value

    def keys(self):
        '''Returns a list of currently set parameter defaults'''
        return self._defaults.keys()

    def update(self, *a, **kw):
        '''Updates the default parameter set by a dictionary.'''
        self._defaults.update(*a, **kw)
