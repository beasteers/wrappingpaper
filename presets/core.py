import os
import types
import inspect
import wrappingpaper as wp


class Preset(wp.ModuleWrapper):
    DISPATCH = {}
    DEFAULTS = {}

    def __init__(self, module, dispatch=None, defaults=None):
        self.DISPATCH[module] = self._dispatch = (
            dispatch if dispatch is not None else
            self.DISPATCH[module] if module in self.DISPATCH else
            {module: self})

        self.DEFAULTS[module] = self._defaults = (
            defaults if defaults is not None else
            self.DEFAULTS[module] if module in self.DEFAULTS else
            {})

        super().__init__(module)

    def __str__(self):
        print(999, type(self._module))
        # return f'<prst {super().__repr__()}>'
        return f'<Preset \n\tfor={self._module} \n\tdefaults={self._defaults}>'

    def _wrapattr(self, attr, value):
        # If it's a function, wrap it in a decorator
        print(attr, value)
        if callable(value):
            value = self._wrap_func(value)

        # If it's a submodule, construct a parameterizer to wrap it
        elif self._is_submodule(value):
            if value not in self._dispatch:
                # pre-seed to avoid cyclic references
                self._dispatch[value] = None
                self._dispatch[value] = Preset(
                    value, dispatch=self._dispatch,
                    defaults=self._defaults)
            value = self._dispatch[value]

        super()._wrapattr(attr, value)

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
