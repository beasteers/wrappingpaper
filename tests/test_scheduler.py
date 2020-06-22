import pytest
import wrappingpaper as wp
from util import interval_checker


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
