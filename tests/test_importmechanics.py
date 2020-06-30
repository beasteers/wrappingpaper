import sys
import pytest
import time
import wrappingpaper as wp
from contextlib import contextmanager


@wp.contextdecorator
def remove_added_imports(*imports):
    try:
        original = set(sys.modules)
        yield
    finally:
        for k in set(imports or sys.modules) - original:
            if k in sys.modules:
                sys.modules.pop(k, None)

@remove_added_imports()
def test_lazy_real_module():
    try:
        from lazyimport import testpkg
        assert time.time() < testpkg.t
    finally:
        wp.lazy_loader.deactivate()

@remove_added_imports()
def test_lazy_faux_module():
    with wp.lazy_loader.activated('sosolazy'):
        from sosolazy import testpkg
        assert time.time() < testpkg.t

@remove_added_imports()
def test_lazy_nested_faux_module():
    with wp.lazy_loader.activated('sosolazy.sooooooo'):
        from sosolazy.sooooooo import testpkg
        assert time.time() < testpkg.t

@remove_added_imports()
def test_lazy_nested_builtin_module():
    with wp.lazy_loader.activated('sosolazy.sooooooo'):
        from sosolazy.sooooooo import glob
        assert glob.glob is not None
        with pytest.raises(ImportError):
            with wp.lazy_loader.deactivated():
                from sosolazy.sooooooo import os

        # for coverage
        assert not wp.BlankLoader().get_data('')

@remove_added_imports()
def test_bad_import():
    with wp.lazy_loader.activated('sosolazy'):
        with pytest.raises(ModuleNotFoundError):
            from solazy import glob

@remove_added_imports()
def test_not_lazy_import_object():
    with wp.lazy_loader.activated('sosolazy.sooooooo'):
        from sosolazy.sooooooo.testpkg import t
        assert time.time() > t

@remove_added_imports()
def test_implicit_import():
    try:
        from lazyimport import testpkg
        assert time.time() < testpkg.t
        from testpkg import another
        assert time.time() < another.t
    finally:
        wp.lazy_loader.deactivate()

@remove_added_imports()
def test_without_implicit_import():
    wp.lazy_loader.use_implicit = False
    try:
        from lazyimport import testpkg
        assert time.time() < testpkg.t
        from testpkg import another
        assert time.time() > another.t
    finally:
        wp.lazy_loader.deactivate()
        wp.lazy_loader.use_implicit = True

@remove_added_imports()
def test_nested_import():
    import importlib

    with wp.lazy_loader.activated('sososolazy'):
        from sososolazy import testpkg
        assert isinstance(testpkg, importlib.util._LazyModule)
        testpkg.t
        assert not isinstance(testpkg, importlib.util._LazyModule)

        from testpkg import nested
        assert isinstance(nested, importlib.util._LazyModule)
