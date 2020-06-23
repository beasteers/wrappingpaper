import sys
import wrappingpaper as wp


def test_presets():
    sys.modules.pop('lazyimport', None)
    from presets import Preset, preset_loader
    try:
        from presets import testpkg
        assert isinstance(testpkg, Preset)
        assert isinstance(testpkg.test_func, wp.configfunction)
        
        assert testpkg.test_func() == 5
        testpkg.update(a=6)
        assert testpkg.test_func() == 6
    finally:
        preset_loader.deactivate()
