import os
import hashlib
import inspect
from . import text
# from .exceptions import CircularReference


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


def stack_summary(message=None, fn=None, offset=0):
    stack = inspect.stack()
    f = stack[offset+1]
    return text.block_text(
        message,
        text.blue(text.l_(f.function, f.lineno, f.filename)), '',
        text.tbl(*(
            (f.function, f.lineno, f.filename, f'>>> {f.code_context[0].strip()}')
            for f in stack[offset+2:]
            if not fn or fn in f.filename
        )), ch=text.yellow('*')
    )

def print_stack(message=None, *a, offset=0, **kw):
    print(stack_summary(message, *a, offset=offset + 1, **kw))


def short_stack_summary(match=None, file=False, sep=' << ', n=None):
    '''Print out a compressed view of the stack.'''
    return sep.join(
        (f'{f.function} ({os.path.basename(f.filename)}:{f.lineno})'
         if file else f.function)
        for f in inspect.stack()[1:][:n]
        if not match or match in f.filename
    )
