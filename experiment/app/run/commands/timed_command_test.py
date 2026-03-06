from .timed_command import _parse_time_line


def test_parse_time_line_short():
    actual_entry = _parse_time_line("real 0.10")

    assert actual_entry == ("real", 0.1)


def test_parse_time_line_long():
    actual_entry = _parse_time_line("real 651.00")

    assert actual_entry == ("real", 651.00)
