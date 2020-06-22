import pytest
import wrappingpaper as wp


def test_context():
    @wp.contextdecorator
    def blah(xs, a, b): # classdecorator.inner
        xs.append(a)
        yield
        xs.append(b)

    xs = []
    @blah(xs, 4, 5) # ContextDecorator.__init__
    def xyz(): # ContextDecorator.__call__
        xs.append(1)
        return xs
    assert xyz() == [4, 1, 5] # ContextDecorator.__call__.inner
    # prints 4, 1, 5

    xs = []
    with blah(xs, 4, 5): # ContextDecorator.__init__, ContextDecorator.__enter__
        xs.append(1)
    assert xs == [4, 1, 5]

def test_empty():
    @wp.contextdecorator
    def asdf():
        return (_ for _ in ())
    with pytest.raises(RuntimeError):
        asdf().__enter__()

def test_custom_caller():
    @wp.contextdecorator
    def blah(xs, a, b): # classdecorator.inner
        xs.append(a)
        yield
        xs.append(b)

    @blah.caller
    def blah(func, xs, *a1, **kw1):
        print(func)
        xs.append(func.__name__)
        def inner(*a, **kw):
            print('asdfasdf', xs)
            with blah(xs, *a1, **kw1):
                return func(*a, **kw)
        return inner

    print(blah.caller)

    xs = []
    @blah(xs, 4, 5)
    def xyz():
        xs.append(1)
        return xs
    assert xyz() == ['xyz', 4, 1, 5]
    assert xyz() == ['xyz', 4, 1, 5, 4, 1, 5]
