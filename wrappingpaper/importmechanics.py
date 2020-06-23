import sys
import importlib
import wrappingpaper as wp
from contextlib import contextmanager


class BaseImportFinder(importlib.abc.MetaPathFinder):
    module_name = None
    def __init__(self, get_module, **kw):
        self.get_module = get_module
        super().__init__(**kw)

    def activate(self, name=None):
        '''Add this module finder to the top of sys.meta_path.'''
        if name:
            self.module_name = _as_parts(name)
        assert self.module_name, 'You must specify a parent module.'
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
            yield
        finally:
            self.deactivate()

    @contextmanager
    def deactivated(self):
        '''Deactivate the finder temporarily.'''
        try:
            self.deactivate()
            yield
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
        # monkey patch in the module wrapper
        @wp.monkeypatch(spec.loader)
        def create_module(spec):
            create_module.reset() # replace old method to avoid infinite recursion
            return self.get_module(spec)
        return spec

    def blank_spec(self, parts):
        return importlib.machinery.ModuleSpec(
            '.'.join(parts), BlankLoader())

    @classmethod
    def moduleloader(cls, _func=None, **kw):
        '''Create a module loader.'''
        def inner(func):
            return cls(func, **kw)
        return inner(_func) if callable(_func) else inner


def _as_parts(name):
    return tuple(name.split('.') if isinstance(name, str) else name)

class PseudoImportFinder(BaseImportFinder):
    '''Define your own import mechanics!

    from somefakemodule import numpy as np
    print(np.something_added_from_somefakemodule) # says hi!
    '''

    module_name = None
    def __init__(self, get_module, use_implicit=True, fake_modules=True, **kw):
        self.use_implicit = use_implicit
        self.fake_modules = fake_modules
        self.wrapped_modules = set() # tracks modules that we've wrapped
        super().__init__(get_module, **kw)

    def already_wrapped(self, parts):
        '''Checks if a module path (split on '.') has been implicitly loaded
        already.'''
        parts = _as_parts(parts)
        return next((name for name in self.wrapped_modules
                     if name == parts[:len(name)]), None)

    def should_wrap(self, *names):
        for name in names:
            self.wrapped_modules.add(_as_parts(name))

    def find_spec(self, fullname, path=None, target=None):
        # presets.librosa => (presets, librosa)
        parts = _as_parts(fullname)

        # e.g. from presets import librosa  <<<<
        explicit_import = self.module_name == parts[:len(self.module_name)]
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
            if spec:
                self.wrapped_modules.add(parts)
                spec = self.wrap_module_spec(spec)
            return spec

        elif explicit_import and self.fake_modules:
            spec = self._find_spec(self.module_name)
            return spec or self.blank_spec(self.module_name)


class BlankLoader(importlib.abc.ResourceLoader):
    def get_data(self, path):
        return b''

    def create_module(self, spec):
        m = type(sys)(spec.name)
        m.__path__ = '.'
        return m

    def exec_module(self, module):
        sys.modules[module.__name__] = module


@PseudoImportFinder.moduleloader
def lazy_loader(spec):
    '''Lazy load modules.'''
    spec.loader = importlib.util.LazyLoader(spec.loader)
    return importlib.util.module_from_spec(spec)
