import time
from functools import wraps


class StopScheduler(Exception):
    '''A special exception that will stop the scheduler.'''

class _IgnoreScheduler(Exception): # dummy exception - no one would throw this
    '''Default ignored exception. Something no one would actually throw.'''


def schedule_task(freq, priority=1, initial_delay=0, ignore=None, stop_signal=StopScheduler, sc=None):
    '''After a task has finished running, schedule it again unless a
    contradicting signal is received.
    '''
    import sched
    sc = sc or sched.scheduler(time.time, time.sleep)
    freq_init = freq if initial_delay is None else initial_delay
    ignore = ignore or _IgnoreScheduler

    def wrapper(func):
        schedule = lambda args, kwargs, freq=freq: sc.enter(
            freq, priority, inner, args, kwargs)

        @wraps(func)
        def inner(*a, **kw):
            try: # try to run the function
                _ = func(*a, **kw)
                if _ == stop_signal: # possibly use return value to exit
                    return

                # update arguments using return result
                if isinstance(_, tuple):
                    a = _
                elif isinstance(_, dict):
                    kw = _
            except StopScheduler: # exit if the built-in stop is raised
                return
            except ignore: # custom ignore exceptions
                pass

            schedule(a, kw)

        def run(*a, **kw):
            schedule(a, kw, freq=freq_init)
            sc.run()
        return run
    return wrapper
