import hashlib
import inspect
from .exceptions import CircularReference


def uid(x, digits=None):
    xid = int(hashlib.sha256(str(x).encode('utf-8')).hexdigest(), 16)
    return xid % 10 ** digits if digits else xid


def get_stack_id(x=None, frames=1, digits=16):
    return uid(str(x) + ''.join(
        str((s.filename, s.lineno, s.function))
        for s in inspect.stack()[1:][:frames]), digits)


# def circular(*keys, **kw):
#     xid = get_stack_id(keys, **kw)
#     if circular.__stack_refs__.get(xid):
#         raise CircularReference(
#             'Circular reference detected with '
#             'reference id: {}. keys={}.'.format(xid, keys))
#     circular.__stack_refs__[xid] = True
#     yield
#     del circular.__stack_refs__[xid]
# circular.__stack_refs__ = {}
