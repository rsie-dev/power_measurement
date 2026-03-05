
from .timed_command import _parse_time_line

def test_parse_time_line_short():
    actual_entry = _parse_time_line("real 0.00")

    assert actual_entry == ("real", 0.0)
