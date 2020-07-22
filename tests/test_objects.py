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

    x.add({'b': 15, 'z': 20})
    assert dict(x) == {'a': 5, 'b': 8, 'c': 10, 'z': 20}
    x.set({'c': 15})
    assert dict(x) == {'a': 5, 'b': 8, 'c': 15, 'z': 20}


def test_attrdict():
    x = wp.attrdict({
        'a': 5,
        'b': {'c': 6, 'd': 7}
    }, {'b': {'e': 10}, 'c': {'e': 10}})

    assert 'a' in x and 'b' in x
    assert x.a == 5
    assert isinstance(x.b, wp.attrdict)
    assert x.b.c == 6
    assert x.b.d == 7
    assert x.b.e == 10
    assert x.c.e == 10

    with pytest.raises(AttributeError):
        assert x.q

    with pytest.raises(KeyError):
        assert x['q']


def test_namespace():
    class something(metaclass=wp.namespace):
        a = 5
        b = 6
        def asdf():
            return a + b

    assert something.asdf() == 5+6
    print(dict(**something))
    assert dict(**something) == {'a': 5, 'b': 6, 'asdf': something.asdf}

def test_mask():
    class A:
        x = 5
        y = 6

    a = A()
    x = wp.Mask(a, full=True)

    # check types
    assert isinstance(x, A)
    assert x.__class__.__name__ == 'A'

    # check that existing attributes are the same
    assert a.x == x.x
    assert a.y == x.y

    # instance attribute modified
    a.x = 7
    assert a.x == 7 and x.x == 7

    # base class modified, but instance still overrides
    A.x = 6
    assert a.x == 7 and x.x == 7

    # new attribute added to base class
    A.q = 10
    assert x.q == a.q

    # new attribute added to instance
    a.w = 10
    assert x.w == a.w


    # only changes masked
    x.y = 10
    print(x.y, a.y)
    assert x.y == 10 and a.y == 6

    # new attribute not added to original
    x.s = 3
    assert not hasattr(a, 's')


    # test partial mask
    class B:
        x = 5
        y = 6

    a = B()
    x = wp.Mask(a, x=10)
    # test that mask is applied
    assert a.x == 5 and x.x == 10
    # test partial mask - mask change
    x.y = 8
    assert a.y == 8 and x.y == 8
    # test partial mask - base change
    a.y = 9
    assert a.y == 9 and x.y == 9
    # test that mask is preserved
    x.x = 15
    assert a.x == 5 and x.x == 15
    a.x = 1
    assert a.x == 1 and x.x == 15





def test_subclasses():
    class A:
        pass
    class B(A):
        pass
    class C(A):
        pass
    class D(C):
        pass

    assert wp.all_subclasses(A) == {B, C, D}


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

def test_monkeypatch():
    class A:
        def x(self):
            return 5

    a = A()
    b = A()
    assert a.x() == 5 and b.x() == 5

    @wp.monkeypatch(a)
    def x():
        return 7

    c = A()
    assert a.x() == 7 and b.x() == 5 and c.x() == 5

    a.x.reset()
    @wp.monkeypatch(a)
    def x():
        return x.super() + 7
    assert a.x() == 5+7

    a.x.reset()
    @wp.monkeypatch(a)
    def x():
        x.reset()
        assert a.x != x
        x.repatch()
        assert a.x == x
        return x.super() + 7
    assert a.x() == 5+7


def test_modfuncglobals():
    def asdf():
        return xxxx
    asdf1 = wp.modfuncglobals(asdf, {'xxxx': 5})
    assert asdf1() == 5
    with pytest.raises(NameError):
        asdf()

    asdf1 = wp.modfuncglobals(asdf, xxxx=10)
    assert asdf1() == 10

    asdf1 = wp.modfuncglobals(asdf, {'xxxx': 5}, xxxx=10)
    assert asdf1() == 10

    asdf1 = wp.modfuncglobals(asdf, {'xxxx': 10}, {'xxxx': 5})
    assert asdf1() == 10


# def test_pod():
#     pod = wp.pod([{'a': 5}, {'a': 6}, {}])
#     assert pod.get('a') == [5, 6, None]


def test_snitch():
    class A(wp.snitch):
        b = 1
    assert A().b == 1

    class B:
        b = 1
    C = wp.make_snitch(B)
    assert B().b == 1
    assert C().b == 1


def test_unbound():
    # class prop:
    #     def __get__(self, instance):
    #         return 5

    class A:
        def asdf(self):
            return self
        # x = prop()

    a = A()

    # test method
    assert a.asdf() is a
    with pytest.raises(TypeError):
        assert a.asdf(5)
    assert wp.unbound(a.asdf)(5) is 5

    f_ub = wp.unbound(a.asdf)
    assert wp.unbound(f_ub) is f_ub

    # # test prop
    # assert a.x == 5
