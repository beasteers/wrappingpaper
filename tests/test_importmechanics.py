import sys
import pytest
import time
import wrappingpaper as wp



def test_lazy_real_module():
    try:
        from lazyimport import testpkg
        assert time.time() < testpkg.t
    finally:
        wp.lazy_loader.deactivate()

def test_lazy_faux_module():
    with wp.lazy_loader.activated('sosolazy'):
        from sosolazy import testpkg
        assert time.time() < testpkg.t

def test_lazy_nested_faux_module():
    with wp.lazy_loader.activated('sosolazy.sooooooo'):
        from sosolazy.sooooooo import testpkg
        assert time.time() < testpkg.t

def test_lazy_nested_builtin_module():
    with wp.lazy_loader.activated('sosolazy.sooooooo'):
        from sosolazy.sooooooo import glob
        assert glob.glob is not None
        with pytest.raises(ImportError):
            with wp.lazy_loader.deactivated():
                from sosolazy.sooooooo import os

        # for coverage
        assert not wp.BlankLoader().get_data('')

def test_bad_import():
    with wp.lazy_loader.activated('sosolazy'):
        with pytest.raises(ModuleNotFoundError):
            from solazy import glob

def test_not_lazy_import_object():
    with wp.lazy_loader.activated('sosolazy.sooooooo'):
        from sosolazy.sooooooo.testpkg import t
        assert time.time() > t

def test_implicit_import():
    sys.modules.pop('lazyimport', None)
    sys.modules.pop('testpkg', None)
    try:
        from lazyimport import testpkg
        assert time.time() < testpkg.t
        from testpkg import another
        assert time.time() < another.t
    finally:
        wp.lazy_loader.deactivate()

def test_without_implicit_import():
    sys.modules.pop('lazyimport', None)
    sys.modules.pop('testpkg', None)

    wp.lazy_loader.use_implicit = False
    try:
        from lazyimport import testpkg
        assert time.time() < testpkg.t
        from testpkg import another
        assert time.time() > another.t
    finally:
        wp.lazy_loader.deactivate()
        sys.modules.pop('lazyimport', None)
        sys.modules.pop('testpkg', None)
