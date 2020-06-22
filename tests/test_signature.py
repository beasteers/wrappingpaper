import wrappingpaper as wp


def test_signature():
    @wp.configfunction
    def abc(a=5, b=6):
        return a + b

    assert abc() == 11
    abc.update(a=10)
    assert abc() == 16
    assert abc(2) == 8
    abc.update(b=10)
    assert abc() == 20
    abc.clear('b')
    assert abc() == 16
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
