import time
import wrappingpaper as wp

class propobj(wp.propobject):
    def asdf(self):
        return self.__method__(self.__instance__.other_value)

    @property
    def blah(self):
        return (
            self.__method__(self.__instance__.other_value) +
            self.__instance__.some_value)


class A:
    some_value = 10
    other_value = 11

    @wp.cachedproperty
    def x(self):
        return time.time()

    @wp.onceproperty
    def y(self):
        return time.time()

    @wp.overridable_property
    def z(self):
        return time.time()

    @wp.classinstancemethod
    def c(self):
        return self

    @wp.overridable_method
    def on_done(self, x):
        return x

    @propobj
    def someprop(self, x=None):
        return (x or self.some_value) * 2


def test_cached_once_properties():
    a1, a2 = A(), A()
    x1, x2 = a1.x, a2.x
    y = a1.y

    # test cache persists
    for _ in range(5):
        # test instance cache
        assert a1.x != a2.x and a1.x == x1 and a2.x == x2
        # test class cache
        assert a1.y == a2.y == y

    del a1.x
    assert a1.x != x1 and a2.x == x2
    del a1.y
    assert a1.y != y and a2.y != y

def test_overridable_property():
    # test overridable_property
    a = A()
    z = 'asdf'
    assert a.z != z
    a.z = z
    assert a.z == z
    del a.z
    assert a.z != z

def test_classinstancemethod():
    # test classinstancemethod
    assert A.c() is A
    assert isinstance(A().c(), A)

def test_overridable_method():
    a = A()

    x = 5
    assert a.on_done(x) == x

    @a.on_done._
    def on_done(x):
        return x * 2
    assert a.on_done(x) == x * 2

    a.on_done.reset()
    assert a.on_done(x) == x

def test_propobj():
    a = A()
    assert a.someprop() == 20
    assert a.someprop.asdf() == 22
    assert a.someprop.blah == 22+10
    assert a.someprop.__instance__ is a
    assert a.someprop.__owner__ is A
    assert a.someprop.__target__ is a
