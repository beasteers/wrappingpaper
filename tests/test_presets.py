# import sys
# import wrappingpaper as wp
#
#
# def test_presets():
#     sys.modules.pop('lazyimport', None)
#     from presets import Preset, preset_loader
#     try:
#         from presets import testpkg
#         assert isinstance(testpkg, Preset)
#         assert isinstance(testpkg.test_func, wp.configfunction)
#         assert str(testpkg).startswith('<Preset')
#
#         assert testpkg.test_func() == 5
#         testpkg.update(a=6)
#         assert testpkg.test_func() == 6
#         assert testpkg['a'] == 6
#         assert 'a' in testpkg
#         assert list(testpkg.keys()) == ['a']
#         testpkg['a'] = 10
#         assert testpkg['a'] == 10
#         del testpkg['a']
#         assert 'a' not in testpkg
#
#
#     finally:
#         preset_loader.deactivate()
