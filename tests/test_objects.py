import pytest
import wrappingpaper as wp


def test_dictproxy():
    a = {'a': 5, 'b': 6}
    b = {'b': 7}
    x = wp.dictproxy(b, a)

    assert isinstance(x, dict)
    assert list(x.items()) == [('a', 5), ('b', 7)]
    b['b'] = 8
    assert list(x.items()) == [('a', 5), ('b', 8)]
    x['c'] = 10
    assert b == {'b': 8, 'c': 10}


def test_namespace():
    class something(metaclass=wp.namespace):
        a = 5
        b = 6
        def asdf():
            return a + b

    assert something.asdf() == 5+6

# def test_mask():
#     class A:
#         x = 5
#         y = 6
#
#     a = A()
#     x = wp.Mask(a)
#
#     # check types
#     assert isinstance(x, A)
#     assert isinstance(x.__dict__, wp.dictproxy)
#     # dd = x.__dict__
#
#     # check that existing attributes are the same
#     assert a.x == x.x
#     assert a.y == x.y
#
#     # instance attribute modified
#     a.x = 7
#     # x.__dict__ = wp.make_snitch(dict)(dd)
#     print(x.__dict__, dict(x.__dict__))
#     assert a.x == 7 and x.x == 7
#
#     # base class modified, but instance still overrides
#     A.x = 6
#     # x.__dict__ = wp.make_snitch(dict)(dd)
#     assert a.x == 7 and x.x == 7
#
#     # new attribute added to base class
#     A.q = 10
#     assert x.q == a.q
#
#     # new attribute added to instance
#     a.w = 10
#     # x.__dict__ = wp.make_snitch(dict)(dd)
#     assert x.w == a.w
#
#
#     # only changes masked
#     x.y = 10
#     assert x.y == 10 and a.y == 6
#
#     # new attribute not added to original
#     x.s = 3
#     assert not hasattr(a, 's')


def test_copyobject():
    class A:
        x = 5
        y = 6

    a = A()
    x = wp.copyobject(a)

    assert a.x == x.x
    assert a.y == x.y

    x.x = 10
    assert a.x != x.x

    x.z = 7
    with pytest.raises(AttributeError):
        assert x.z != a.z
