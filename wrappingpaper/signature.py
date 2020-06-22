import functools
import itertools
import collections
import inspect
from inspect import Parameter as Pm


POSARG_TYPES = [Pm.POSITIONAL_ONLY, Pm.POSITIONAL_OR_KEYWORD]
ARG_TYPES = POSARG_TYPES + [Pm.KEYWORD_ONLY]

Spec = collections.namedtuple('Spec', 'args, vararg, varkw, posargs, kwargs, posonlyargs, defaults')

def get_argspec(f):
    '''Get function parameters'''
    ps = inspect.signature(f).parameters.items()
    args = [n for n, p in ps if p.kind in ARG_TYPES]
    defaults = {n: p.default for n, p in ps if p.kind in ARG_TYPES}
    posargs = [n for n, p in ps if p.kind in POSARG_TYPES]
    posonlyargs = [n for n, p in ps if p.kind in POSARG_TYPES and
                   p.default == inspect._empty]
    vararg = next((n for n, p in ps if p.kind == Pm.VAR_POSITIONAL), None)
    varkw = next((n for n, p in ps if p.kind == Pm.VAR_KEYWORD), None)
    kwargs = {n: p.default for n, p in ps if p.default != inspect._empty}
    return Spec(args, vararg, varkw, posargs, kwargs, posonlyargs, defaults)


def filterkw(func):
    '''Remove arguments that aren't in the function signature.'''
    spec = get_argspec(func)
    if spec.varkw:
        return func

    args = set(spec.args)
    @functools.wraps(func)
    def inner(*a, **kw):
        return func(*a, **{k: v for k, v in kw.items() if k in args})
    return inner

def filterpos(func):
    '''Remove arguments that aren't in the function signature.'''
    spec = get_argspec(func)
    print(spec)
    if spec.vararg:
        return func

    @functools.wraps(func)
    def inner(*a, **kw):
        return func(*a[:len(spec.posargs)], **kw)
    return inner


def partial(func, *a, **kw):
    '''Partial argument binding - maintaining the function signature.'''
    @functools.wraps(func)
    def inner(*ai, **kwi):
        return func(*a, *ai, **kw, **kwi)
    return inner


def args(*a, **kw):
    def arguments(func):
        return partial(func, *a, **kw)
    arguments.__doc__ = '''
    Arguments containing:
        *args: {}
        **kwargs: {}

    Call this function to bind arguments to a function.
    '''.format(a, kw)

    arguments.args = a
    arguments.kwargs = kw
    return arguments


class configfunction:
    '''Allow functions to have easily overrideable default arguments.
    Works with mixed positional and keyword arguments.

    @configfunction
    def abc(a=5, b=6):
        return a + b
    assert abc() == 11
    abc.update(a=10)
    assert abc() == 16
    assert abc(2) == 8

    '''
    def __init__(self, func, fill_varkw=True, view=None):
        self.function = func
        self.name = func.__name__
        self.spec = get_argspec(func)
        functools.update_wrapper(self, func)

        self.config = {}
        self.fill_varkw = fill_varkw

    def __call__(self, *a, _cfg=None, **kw):
        a, kw = self.config_args(self.merge_config(_cfg), *a, **kw)
        return self.function(*a, **kw)

    def config_args(self, cfg, *a, **kw):
        # fill in any positional arguments we can
        a += tuple(cfg[x] for x in itertools.takewhile(
            lambda x: x not in kw and x in cfg,
            self.spec.posargs[len(a):]))

        # update keywords with vars not passed in call
        kw.update((k, cfg[k]) for k in (
            set(cfg) - set(self.spec.posargs[:len(a)]) - set(kw)
            if self.fill_varkw and self.spec.varkw else
            set(cfg) & set(self.spec.args[len(a):]) - set(kw)))
        return a, kw

    def merge_config(self, cfg):
        return self.config if cfg is None else dict(self.config, **cfg)

    def update(self, *a, **kw):
        self.config.update(*a, **kw)
        return self

    def clear(self, *a):
        self.config = (
            {k: v for k, v in self.config.items() if k not in a} if a else {})
        return self
