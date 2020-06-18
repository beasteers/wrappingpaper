import time
import pytest
import wrappingpaper as wp

def interval_checker(sec):
    def f():
        f.ts.append(int((time.time() - f.t0) / f.sec))
    f.ts = []
    f.t0 = time.time()
    f.sec = sec

    def check():
        assert (
            f.ts == list(range(len(f.ts))) or
            f.ts == list(range(1, 1 + len(f.ts))))
    f.check = check
    return f


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

    @wp.contextdecorator
    def asdf():
        return (_ for _ in ())
    with pytest.raises(RuntimeError):
        with asdf():
            pass


def test_misc():
    # test limit
    items = list(range(10))
    assert list(wp.limit(items, 3)) == items[:3]
    assert list(wp.limit(iter(items), 3)) == items[:3]

    # test asfunc
    getx = wp.asfunc(iter(items))
    for x in items:
        assert x == getx()

    # test throttled
    ival = interval_checker(0.05)
    for _ in wp.limit(wp.throttled(ival.sec), 10):
        ival()
    ival.check()

    # test ignore
    @wp.ignore()
    def ign():
        raise Exception
    assert ign() == None

    ival = interval_checker(0.05)
    @wp.retry_on_failure(5)
    def retry():
        ival()
        raise Exception
    with pytest.raises(Exception):
        retry()
    assert len(ival.ts) == 5


    # test throttle_exception, retry_on_failure
    ival = interval_checker(0.05)
    @wp.ignore()
    @wp.retry_on_failure(5)
    @wp.throttle_exception(ival.sec)
    def threxc():
        ival()
        raise Exception
    assert threxc() == None
    assert len(ival.ts) == 5
    ival.check()

    # test default_value
    @wp.default_value(2)
    def defval():
        raise Exception()
    assert defval() == 2


def test_iters():
    items = list(range(10))

    # test precheck
    it = iter(items)
    first, it = wp.pre_check_iter(it, 3)
    assert first == [0, 1, 2]
    assert list(it) == items

    # test run forever
    N = 5
    repit = wp.run_iter_forever(lambda: items)
    assert list(wp.limit(repit, len(items) * N)) == items * N

    # test run forever returns None if empty
    it = iter(items)
    repit = wp.run_iter_forever(lambda: it, none_if_empty=True)
    assert list(wp.limit(repit, len(items) + 2)) == items + [None]*2


def test_props():
    class A:
        @wp.cachedproperty
        def x(self):
            return time.time()

        @wp.onceproperty
        def y(self):
            return time.time()

        @wp.overridable_property
        def z(self):
            return time.time()

    a1, a2 = A(), A()
    x1, x2 = a1.x, a2.x
    y = a1.y

    # test cache persists
    for _ in range(5):
        # test instance cache
        assert a1.x != a2.x and a1.x == x1 and a2.x == x2
        # test class cache
        assert a1.y == a2.y == y

    # test overrideable_property
    z = a1.z
    a1.z = 'asdf'
    assert a1.z == 'asdf' and a1.z != z


def test_scheduler():
    ival = interval_checker(0.05)

    @wp.schedule_task(ival.sec, stop_signal=False)
    def task(a=1):
        ival()
        assert a == len(ival.ts)
        if a >= 10:
            return False # end
        return {'a': a + 1}
    task()
    ival.check()

    class ignored:
        raised = False
    ival = interval_checker(0.05)
    @wp.schedule_task(ival.sec, stop_signal=False, ignore=ValueError)
    def task2(a=1):
        if a >= 10:
            if ignored.raised == False:
                ignored.raised = True
                raise ValueError
            raise wp.StopScheduler

        ival()
        assert a == len(ival.ts)
        return (a + 1,)
    task2()
    ival.check()


def test_logging():
    pass


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

    @wp.filterkw
    def asdf(a=5, b=6):
        return a + b
    assert asdf(d=12) == 11

    @wp.filterkw
    def asdf2(a=5, b=6, **kw):
        return a + b + sum(v for v in kw.values())
    assert asdf2(d=12) == 11 + 12
