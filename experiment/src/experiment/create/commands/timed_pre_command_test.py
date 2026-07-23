from datetime import timedelta
from unittest.mock import Mock

from .timed_pre_command import _parse_time_line, TimedCommandPreCommand
from experiment.run.log import TimingEntry, Logger

# pylint: disable=redefined-outer-name, protected-access


def test_parse_time_line_short():
    actual_entry = _parse_time_line("real 0.10")

    assert actual_entry == ("real", timedelta(milliseconds=100))


def test_parse_time_line_long():
    actual_entry = _parse_time_line("real 651.00")

    assert actual_entry == ("real", timedelta(seconds=651))


def test_annotations_sleep():
    timing_logger = Mock(spec=Logger[TimingEntry])
    command = TimedCommandPreCommand(timing_logger)
    timings = TimingEntry(entry_nr=1,
                          real=timedelta(seconds=15),
                          user=timedelta(seconds=0),
                          sys=timedelta(seconds=0),
                          command="")

    actual_annotations = command._get_timings_annotations(timings)

    assert actual_annotations == []


def test_annotations_multithreaded():
    timing_logger = Mock(spec=Logger[TimingEntry])
    command = TimedCommandPreCommand(timing_logger)
    timings = TimingEntry(entry_nr=1,
                          real=timedelta(seconds=5),
                          user=timedelta(seconds=10),
                          sys=timedelta(seconds=1),
                          command="")

    actual_annotations = command._get_timings_annotations(timings)

    assert actual_annotations == [TimedCommandPreCommand.MULTITHREADED]


def test_annotations_io():
    timing_logger = Mock(spec=Logger[TimingEntry])
    command = TimedCommandPreCommand(timing_logger)
    timings = TimingEntry(entry_nr=1,
                          real=timedelta(seconds=5),
                          user=timedelta(seconds=1),
                          sys=timedelta(seconds=3),
                          command="")

    actual_annotations = command._get_timings_annotations(timings)

    assert actual_annotations == [TimedCommandPreCommand.IO_BOUND]
