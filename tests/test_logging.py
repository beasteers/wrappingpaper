import pytest
import wrappingpaper as wp
import logging

log = logging.getLogger(__name__)

def test_logging():
    def asdf():
        raise ValueError()

    asdf_wn = wp.log_error_as_warning(log)(asdf)
    asdf_wn()

    asdf_er = wp.log_error_as_error(log)(asdf)
    asdf_er()

    asdf_ex = wp.log_error_as_exception(log)(asdf)
    asdf_ex()

    asdf_ig = wp.ignore_error()(asdf)
    asdf_ig()

    asdf_time = wp.log_exec_time(log)(asdf_ig)
    asdf_time()

    asdf_er = wp.log_error_as_error(log, should_raise=True)(asdf)
    with pytest.raises(ValueError):
        asdf_er()

    asdf_er = wp.log_error_as_error(log, exit=0)(asdf)
    with pytest.raises(SystemExit):
        asdf_er()
