import sys
import pytest
import time
import wrappingpaper as wp

# untested:
#   71 BaseImportFinder.modify_spec=True
#   81-85 BaseImportFinder.exec_module=True
#   102-104 BaseImportFinder.modulemodifier
#   109-111 BaseImportFinder.specmodifier
#   242 NoLoader.get_data
#   263-264 lazy_loader.exec_module.__getattribute__


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

@remove_added_imports()
def test_no_import():
    with wp.blank_import_loader.activated('blanksss'):
        from blanksss import testpkg
        assert not hasattr(testpkg, 't')


@remove_added_imports()
def test_blank_mark():
    with wp.blank_import_loader.activated('blanksss') as blanksss:
        blanksss.mark('testpkg')
        import testpkg
        assert not hasattr(testpkg, 't')
        blanksss.unmark('testpkg')
        del sys.modules['testpkg']
        import testpkg
        assert hasattr(testpkg, 't')


# @remove_added_imports()
def test_presets():
    from presets import Preset, preset_loader
    try:
        from presets import testpkg
        print(testpkg)
        assert isinstance(testpkg, Preset)
        assert isinstance(testpkg.test_func, wp.configfunction)
        assert str(testpkg).startswith('<Preset')

        assert testpkg.test_func() == 5
        testpkg.update(a=6)
        assert testpkg.test_func() == 6
        assert testpkg['a'] == 6
        assert 'a' in testpkg
        assert list(testpkg.keys()) == ['a']
        testpkg['a'] = 10
        assert testpkg['a'] == 10
        del testpkg['a']
        assert 'a' not in testpkg
    finally:
        preset_loader.deactivate()
