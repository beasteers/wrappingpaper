import pytest
import wrappingpaper as wp
from util import interval_checker

@pytest.fixture
def items():
    return list(range(10))

def test_limit(items):
    # test limit
    assert list(wp.limit(items, 3)) == items[:3]
    assert list(wp.limit(iter(items), 3)) == items[:3]


def test_asfunc(items):
    # test asfunc
    getx = wp.asfunc(iter(items))
    for x in items:
        assert x == getx()


def test_throttled(items):
    # test throttled
    ival = interval_checker(0.05)
    for _ in wp.limit(wp.throttled(secs=ival.sec), 10):
        ival()
    ival.check()

    ival = interval_checker(0.05)
    for _ in wp.throttled(range(10), secs=ival.sec):
        ival()
    ival.check()


def test_time_limit(items):
    # test time_limit
    N = 10
    ival = interval_checker(0.05)
    for _ in wp.throttled(wp.time_limit(secs=ival.sec * N), secs=ival.sec):
        ival()
    ival.check()
    assert len(ival.ts) == N + 1


def test_ignore(items):
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


def test_throttle_exception(items):
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

def test_default_value(items):
    # test default_value
    @wp.default_value(2)
    def defval():
        raise Exception()
    assert defval() == 2


def test_circular():
    with pytest.raises(wp.CircularReference):
        refs = []
        def asdf(k):
            with wp.prevent_circular(refs, k):
                asdf(k)
        asdf('qqq')

    with pytest.raises(wp.CircularReference):
        refs = []
        @wp.prevent_circular_caller
        def asdf(k):
            asdf(k + 'a')
        asdf('qqq')

    @wp.prevent_circular()
    def asdf(k):
        if len(k) < 10:
            asdf(k + 'a')
    asdf('qqq')
