import os
import sys
import types
import inspect
import importlib
import wrappingpaper as wp
from contextlib import contextmanager


class BaseImportFinder(importlib.abc.MetaPathFinder):
    '''This handles basic import finder activation/deactivation as well as
    module monkey patching and importer creation utils.


    '''
    module_name = None
    def __init__(self, create_module=None, exec_module=None, modify_spec=None, **kw):
        self.create_module = create_module
        self.exec_module = exec_module
        self.modify_spec = modify_spec
        super().__init__(**kw)

    def activate(self, name=None):
        '''Add this module finder to the top of sys.meta_path.'''
        if name:
            self.module_name = _as_parts(name)
        # assert self.module_name, 'You must specify a parent module.'
        if self not in sys.meta_path:
            sys.meta_path.insert(0, self)
        return self

    def deactivate(self):
        '''Add this module finder to the top of sys.meta_path.'''
        if self in sys.meta_path:
            sys.meta_path.remove(self)
        return self

    @contextmanager
    def activated(self, name):
        '''Activate the finder temporarily.'''
        try:
            self.activate(name)
            yield self
        finally:
            self.deactivate()

    @contextmanager
    def deactivated(self):
        '''Deactivate the finder temporarily.'''
        try:
            self.deactivate()
            yield self
        finally:
            self.activate()

    _already_matched = None # track circular calls
    def _find_spec(self, parts):
        '''Find the module spec while preventing recursion.'''
        if self._already_matched != parts:
            self._already_matched = parts
            try:
                return importlib.util.find_spec('.'.join(parts))
            # except ModuleNotFoundError:
            #     pass
            finally:
                self._already_matched = None


    def wrap_module_spec(self, spec):
        if self.modify_spec:
            spec = self.modify_spec(spec)

        # monkey patch in the module wrapper
        if self.create_module:
            @wp.monkeypatch(spec.loader)
            def create_module(spec):
                create_module.reset() # replace old method to avoid infinite recursion
                return self.create_module(spec)

        if self.exec_module:
            @wp.monkeypatch(spec.loader)
            def exec_module(module):
                _ = exec_module.super(module)
                self.exec_module(module)
                return _
        return spec

    def blank_spec(self, parts):
        return importlib.machinery.ModuleSpec(
            '.'.join(parts), BlankLoader())

    @classmethod
    def moduleloader(cls, _func=None, **kw):
        '''Create a module loader.'''
        def inner(func):
            return cls(create_module=func, **kw)
        return inner(_func) if callable(_func) else inner

    @classmethod
    def modulemodifier(cls, _func=None, **kw):
        '''Create a module loader.'''
        def inner(func):
            return cls(exec_module=func, **kw)
        return inner(_func) if callable(_func) else inner

    @classmethod
    def specmodifier(cls, _func=None, **kw):
        '''Create a module loader.'''
        def inner(func):
            return cls(modify_spec=func, **kw)
        return inner(_func) if callable(_func) else inner


def _as_parts(name):
    return tuple(name.split('.') if isinstance(name, str) else name)


class PseudoImportFinder(BaseImportFinder):
    '''Define your own import mechanics!

    from somefakemodule import numpy as np
    print(np.something_added_from_somefakemodule) # says hi!
    '''

    module_name = None
    def __init__(self, *a, use_implicit=True, fake_modules=True, **kw):
        self.use_implicit = use_implicit
        self.fake_modules = fake_modules
        self.wrapped_modules = set() # tracks modules that we've wrapped
        super().__init__(*a, **kw)

    def already_wrapped(self, parts):
        '''Checks if a module path (split on '.') has been implicitly loaded
        already.'''
        parts = _as_parts(parts)
        return next((name for name in self.wrapped_modules
                     if name == parts[:len(name)]), None)

    def mark(self, *names):
        '''Mark a module as a wrapped module.'''
        for name in names:
            self.wrapped_modules.add(_as_parts(name))

    def unmark(self, *names):
        '''Unmark a module as a wrapped module.'''
        for name in names:
            self.wrapped_modules.remove(_as_parts(name))

    def find_spec(self, fullname, path=None, target=None):
        # print(fullname, path, target)
        # presets.librosa => (presets, librosa)
        parts = _as_parts(fullname)

        # e.g. from presets import librosa  <<<<
        explicit_import = self.module_name[:len(parts)] == parts[:len(self.module_name)]

        if explicit_import:
            parts = parts[len(self.module_name):] # cut off prefix
        elif not self.use_implicit:
            return

        # i.e. from presets import librosa
        #      import librosa.display       <<<<
        wrapped = self.already_wrapped(parts)
        if not (explicit_import or wrapped): # no matches
            return

        # find and load the module:

        # prevent inf recursion, get module the normal way
        if parts:
            spec = self._find_spec(parts)
            if spec is not None:
                self.wrapped_modules.add(parts)
                spec = self.wrap_module_spec(spec)
            return spec

        if explicit_import and self.fake_modules:
            spec = self._find_spec(self.module_name)
            if spec is None:
                spec = self.blank_spec(self.module_name)
            return spec


class ModuleWrapper(types.ModuleType):
    def __init__(self, module):
        self._module = module
        self.__dict__.update(module.__dict__)
        self.modpath = (
            os.path.dirname(inspect.getfile(module))
            if hasattr(module, '__file__') else None)

        @wp.monkeypatch(module.__loader__)
        def exec_module(module):
            exec_module.super(self._module)
            self._wrap()

    # def __str__(self):
    #     return '<wrapped({})({})>'.format(
    #         self.__class__.__name__, self._module)

    def _wrap(self):
        # inspect the target module
        for attr, value in inspect.getmembers(self._module):
            self._wrapattr(attr, value)

    def _wrapattr(self, attr, value):
        setattr(self, attr, value)

    def _is_submodule(self, value):
        return (
            isinstance(value, types.ModuleType) and
            hasattr(value, '__file__') and
            self.modpath and
            os.path.commonprefix(
                [self.modpath, inspect.getfile(value)]) == self.modpath)

    # @classmethod
    # def from_existing(cls, name):
    #     m = sys.modules[name] = cls(sys.modules[name])
    #     return m



class BlankLoader(importlib.abc.ResourceLoader):
    def get_data(self, path):
        return b''

    def create_module(self, spec):
        m = type(sys)(spec.name)
        m.__path__ = '.'
        return m

    def exec_module(self, module):
        sys.modules[module.__name__] = module


class NoLoader(importlib.abc.ResourceLoader):
    def get_data(self, path):
        return b''

    def __init__(self, loader):
        self.loader = loader

    def create_module(self, spec):
        return self.loader.create_module(spec)

    def exec_module(self, module):
        sys.modules[module.__name__] = module


@PseudoImportFinder.moduleloader
def lazy_loader(spec):
    '''Lazy load modules.'''
    spec.loader = importlib.util.LazyLoader(spec.loader)

    @wp.monkeypatch(spec.loader)
    def exec_module(module):
        @wp.monkeypatch(module, '__getattribute__')
        def ga(attr):
            spec.finder.unmark(spec.name)
            return ga.super(attr)
        exec_module.super(module)

    return importlib.util.module_from_spec(spec)

# @PseudoImportFinder.moduleloader(use_implicit=False)
# def single_lazy_loader(spec):
#     '''Lazy load modules.'''
#     spec.loader = importlib.util.LazyLoader(spec.loader)
#     return importlib.util.module_from_spec(spec)


@PseudoImportFinder.moduleloader
def blank_import_loader(spec):
    spec.loader = NoLoader(spec.loader)
    return importlib.util.module_from_spec(spec)


# @PseudoImportFinder.moduleloader(use_implicit=False)
# def single_blank_import_loader(spec):
#     spec.loader = NoLoader(spec.loader)
#     return importlib.util.module_from_spec(spec)
