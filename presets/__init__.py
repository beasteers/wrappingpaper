import importlib
import wrappingpaper as wp
from .core import Preset

@wp.PseudoImportFinder.moduleloader
def preset_loader(spec):
    return Preset(importlib.util.module_from_spec(spec))

preset_loader.activate(__name__)
