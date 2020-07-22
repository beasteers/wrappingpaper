import functools
import itertools
import collections
import inspect
from inspect import Parameter as Pm
import wrappingpaper as wp


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
    if spec.vararg:
        return func

    @functools.wraps(func)
    def inner(*a, **kw):
        return func(*a[:len(spec.posargs)], **kw)
    return inner


# def assign_args(func):
#     '''Assign specified arguments in __init__ to self.'''
#     spec = get_argspec(func)
#     @functools.wraps(func)
#     def inner(self, *a, **kw):
#         self.__dict__.update(dict(zip(spec.args, a)))
#         self.__dict__.update({k: kw[k] for k in spec.kwargs if k in kw})
#         return func(self, *a, **kw)
#     return inner


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
        self.name = self.__name__ = func.__name__
        self.spec = get_argspec(func)
        functools.update_wrapper(self, func)

        self.config = collections.ChainMap()
        self.fill_varkw = fill_varkw

    def __call__(self, *a, **kw):
        return self.call(*a, **kw)

    def call(self, *a, _cfg=None, **kw):  # so that we can patch it
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

    def add(self, *cfg):
        for d in cfg:
            self.config.maps.append(d)
        return self

    def set(self, *cfg):
        for d in cfg[::-1]:
            self.config.maps.insert(0, d)
        return self

    def clear(self, *a):
        if a:
            for k in a:
                for m in self.config.maps:
                    m.pop(k, None)
        else:
            self.config = collections.ChainMap()
        return self


class FunctionCapture:
    '''

    cfgcap = wp.FunctionCapture()

    @cfgcap.capture
    def build_model(inputs=('asdf/asdf',), window_size=5):
        return

    @cfgcap.capture(called=True, output='run-args.yml')
    def main(data_dir='data', train_split=0.2):
        ...

    main(train_split=0.3)  # call captured function

    print(cfgcap.dump())  # outputs

    defaults:
        build_model:
            inputs: ['asdf/asdf']
            window_size: 5
        main:
            data_dir: data
            train_split: 0.2

    called_with:
        main:
            train_split: 0.3


    '''
    def __init__(self, skip_types=None):
        self.functions = {}
        self.called_args = {}
        self.skip_types = skip_types

    def capture(self, func=None, called=False, output=False):
        def inner(func):
            func2 = self.functions[func.__name__] = configfunction(func)

            @wp.monkeypatch(func2, 'call')
            def call(*a, **kw):
                if called:
                    self._record_called_args(func2, *a, **kw)
                _ = call.super()
                if output:
                    self.save(output)
                return _

            return func2
        return inner(func) if callable(func) else inner

    # def main(self, func=None, called=True, output=True):
    #     return self.capture(func, called=called, output=output)

    def _record_called_args(self, func, *a, **kw):
        name = func.__name__
        # get/new previous called arg dict
        prevargs = self.called_args.get(name)
        # get called arg dict
        args = dict(zip(func.spec.posargs, a), **kw)
        # update recorded args
        self.called_args[name] = {
            k: args[k] for k in set(args) & set(prevargs or args)
            if ((not self.skip_types or isinstance(args[k], self.skip_types))
                and (prevargs is None or args[k] == prevargs[k])  # XXX: numpy ughhhhh
               )
        }

    def save(self, out_file):
        import yaml
        with open(out_file, 'w') as f:
            yaml.safe_dump(self.dump(), f)

    def dump(self):
        return {
            'defaults': {
                name: {
                    k: v for k, v in func.spec.defaults.items()
                    if not self.skip_types or isinstance(v, self.skip_types)
                }
                for name, func in self.functions.items()
            },
            'called_with': self.called_args
        }
