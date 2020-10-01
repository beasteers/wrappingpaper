class _Null:
    def __bool__(self):
        return False
    __nonzero__ = __bool__

_ = UNSET = EMPTY = UNDEFINED = _Null()


from .exceptions import *
from .iters import *
from .misc import *
from .context import *
from .logs import *
from .props import *
from . import text
from .stack import *
from .objects import *
from .schedule import *
from .signature import *
from .importmechanics import *
