import sys
import time
from functools import wraps
from .context import contextdecorator


def log_error_as_warning(logger, *a, **kw):
    '''Instead of throwing an error, log as a warning.'''
    return handle_error(logger.warning, *a, **kw)

def log_error_as_error(logger, *a, **kw):
    '''Instead of throwing an error, log as an error.'''
    return handle_error(logger.error, *a, **kw)

def log_error_as_exception(logger, *a, **kw):
    '''Instead of throwing an error, log as an error.'''
    return handle_error(logger.exception, *a, **kw)

def ignore_error(ignore=(Exception,), **kw):
    '''Ignore error thrown.'''
    return handle_error(None, exc=(), ignore=ignore, **kw)


@contextdecorator
def handle_error(log, msg='Exception:', should_raise=False, exc=(Exception,),
                 log_traceback=False, ignore=(), exit=False,
                 default=None):
    '''Catch errors thrown within context manager.

    Arguments:
        should_raise (bool): should we still raise the exception? default: False.
        log_traceback (bool): if True, log the traceback as well.
        ignore (Exception, tuple of Exceptions): any exceptions to ignore.
        exit (int): if specified, call sys.exit(exit) where exit is the exit code.
        throttle (float): if specified, sleep to ensure that the function takes
            `throttle` seconds if an error is thrown. This is to prevent
            functions going into rapid failure cycles.
        default (any): the value to return if an exception is raised.
    '''
    try:
        yield
    except ignore:
        pass
    except exc as e:
        # TODO: any way to pass exception and use that as a trace? idk this is FINE for now
        #       later reading: https://stackoverflow.com/questions/1278705/when-i-catch-an-exception-how-do-i-get-the-type-file-and-line-number
        log(msg + ' ({}) {}'.format(type(e).__name__, e),
            extra={'override': get_exec_info(drop=1)},
            exc_info=log_traceback and sys.exc_info())
        if should_raise:
            raise e
        if exit or exit is 0: # int or True
            exit_code = int(1 if exit is True else exit)
            log('Exiting with code: %d', exit_code)
            sys.exit(exit_code)
    return default


@handle_error.caller
def handle_error(func, log, msg='', **kwargs):
    msg = msg or 'Exception in {}: '.format(func.__qualname__)
    @wraps(func)
    def inner(*a, **kw):
        with handle_error(log, msg, **kwargs):
            return func(*a, **kw)
    return inner


def log_exec_time(logger, msg='{name} took {sec}s'):
    '''Log the function execution time.'''
    def outer(func):
        @wraps(func)
        def inner(*a, **kw):
            t0 = time.time()
            try:
                return func(*a, **kw)
            finally:
                t = time.time() - t0
                logger.info(msg.format(
                    sec=t, ms=t*1000, min=t/60.,
                    name=func.__name__))
        return inner
    return outer



###############
# Utils
###############


def gather_tbs():
    tbs = [sys.exc_info()[-1]]
    while True:
        if tbs[-1].tb_next is None:
            return tbs[::-1]
        tbs.append(tbs[-1].tb_next)

def get_exec_info(depth=0, sep='|', drop=0):
    exc_tbs = gather_tbs()
    exc_tbs = exc_tbs[depth:len(exc_tbs) - drop]
    trace = [tb.tb_frame.f_code.co_name for tb in exc_tbs]
    return {
        'filename': exc_tbs[0].tb_frame.f_code.co_filename,
        'funcName': sep.join(trace),
        'lineno'  : exc_tbs[0].tb_lineno,
        'trace': trace,
    }
