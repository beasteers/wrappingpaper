import os
import wrappingpaper as wp


def test_signature():
    @wp.configfunction
    def abc(a=5, b=6):
        return a + b

    # test update
    assert abc() == 11
    abc.update(a=10)
    assert abc() == 16
    assert abc(2) == 8
    abc.update(b=10)
    assert abc() == 20

    # test add / set
    abc.add({'a': 12})
    assert abc() == 20
    abc.set({'a': 12})
    assert abc() == 22

    # test clear
    abc.clear('b')
    assert abc() == 18
    abc.clear()
    assert abc() == 11


def test_filterkw():
    @wp.filterkw
    def asdf(a=5, b=6):
        return a + b
    assert asdf(d=12) == 11

    @wp.filterkw
    def asdf2(a=5, b=6, **kw):
        return a + b + sum(v for v in kw.values())
    assert asdf2(d=12) == 11 + 12


def test_filterpos():
    @wp.filterpos
    def asdf(a, b=6):
        return a + b
    assert asdf(1, 2, 3, 4, 5) == 1+2

    @wp.filterpos
    def asdf(a, b=6, *x):
        return a + b + sum(x)
    assert asdf(1, 2, 3, 4, 5) == 1+2+3+4+5


def test_partial():
    def asdf(a, b=6):
        return a + b
    asdf1 = wp.partial(asdf, 10)

    assert asdf1() == 10+6


def test_args():
    def asdf(a, b=6):
        return a + b

    asdfargs = wp.args(10, 12)
    assert asdfargs.args == (10, 12)

    asdf1 = asdfargs(asdf)
    assert asdf1() == 10+12


def test_funccapture():
    cfgcap = wp.FunctionCapture()

    @cfgcap.capture
    def build_model(inputs=['asdf/asdf'], window_size=5):
        return 5

    out_file = os.path.join(os.path.dirname(__file__), 'test-cfg.yml')
    @cfgcap.capture(called=True, output=out_file)
    def main(data_dir='data', train_split=0.2):
        build_model()
        return 10

    assert main('data2', train_split=0.3) == 10
    assert main('data2', train_split=0.1) == 10
    print(cfgcap.dump())
    assert cfgcap.dump() == {
        'defaults': {
            'build_model': dict(inputs=['asdf/asdf'], window_size=5),
            'main': dict(data_dir='data', train_split=0.2),
        },
        'called_with': {'main': dict(data_dir='data2')}
    }

    assert os.path.isfile(out_file)
    import yaml
    with open(out_file, 'r') as f:
        data = yaml.safe_load(f)
    assert data == cfgcap.dump()
    os.remove(out_file)
