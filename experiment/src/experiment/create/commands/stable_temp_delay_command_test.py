from datetime import timedelta, datetime
from unittest.mock import Mock

import pytest

from experiment.run.log import LogDispatcher, TemperatureEntry
from .stable_temp_delay_command import StableTemperatureDelayCommand

# pylint: disable=redefined-outer-name, protected-access


STABLE1 = """
2026-07-14T13:28:59.396+02:00, 56.20
2026-07-14T13:29:00.408+02:00, 55.65
2026-07-14T13:29:01.396+02:00, 55.65
2026-07-14T13:29:02.406+02:00, 55.10
2026-07-14T13:29:03.396+02:00, 54.00
2026-07-14T13:29:04.408+02:00, 55.10
2026-07-14T13:29:05.397+02:00, 54.55
2026-07-14T13:29:06.397+02:00, 54.00
2026-07-14T13:29:07.396+02:00, 54.55
2026-07-14T13:29:08.408+02:00, 54.55
"""

STABLE2 = """
2026-07-13T16:29:04.657+02:00, 54.55
2026-07-13T16:29:05.670+02:00, 54.55
2026-07-13T16:29:06.684+02:00, 54.00
2026-07-13T16:29:07.697+02:00, 54.55
2026-07-13T16:29:08.711+02:00, 54.55
2026-07-13T16:29:09.725+02:00, 54.55
"""

UNSTABLE1 = """
2026-07-14T15:43:51.750+02:00, 62.25
2026-07-14T15:43:52.759+02:00, 61.15
2026-07-14T15:43:53.749+02:00, 61.7
2026-07-14T15:43:54.750+02:00, 58.95
2026-07-14T15:43:55.749+02:00, 58.95
2026-07-14T15:43:56.759+02:00, 58.95
2026-07-14T15:43:57.749+02:00, 58.4
"""

UNSTABLE2 = """
2026-07-14T15:43:51.750+02:00, 62.25
2026-07-14T15:43:52.759+02:00, 61.15
2026-07-14T15:43:53.749+02:00, 61.7
2026-07-14T15:43:54.750+02:00, 58.95
2026-07-14T15:43:55.749+02:00, 58.95
2026-07-14T15:43:56.759+02:00, 58.95
"""


@pytest.fixture(params=[STABLE1, STABLE2], ids=["stable1", "stable2"])
def history_stable(request):
    return _read_data(request.param)


@pytest.fixture(params=[UNSTABLE1, UNSTABLE2], ids=["unstable1", "unstable2"])
def history_unstable(request):
    return _read_data(request.param)


def _read_data(data: str) -> list[TemperatureEntry]:
    entries = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        tokens = line.split(",")
        timestamp = datetime.fromisoformat(tokens[0])
        value = float(tokens[1].strip())
        entries.append(TemperatureEntry(
            timestamp=timestamp,
            temperature=value,
        ))
    return entries


def _create_config(min_delay: float, max_delay: float, threshold: float):
    dispatcher = Mock(spec=LogDispatcher[TemperatureEntry])
    return StableTemperatureDelayCommand.Config(
        min_delay=timedelta(seconds=min_delay),
        max_delay=timedelta(seconds=max_delay),
        kind="test",
        temp_dispatcher=dispatcher,
        slope_threshold=threshold
    )


@pytest.fixture
def config():
    config = _create_config(5, 20, 0.1)
    return config


@pytest.fixture
def command(config):
    return StableTemperatureDelayCommand(config)


def test_append_ensure_timespan(command):
    data = _read_data(STABLE1)

    command._append_data(data)

    history_start = command._history[0].timestamp
    history_end = command._history[-1].timestamp
    history_time = history_end - history_start
    assert history_time >= command._config.min_delay


def test_stable(command, history_stable):
    command._append_data(history_stable)

    assert command._equilibrium_reached(command._history)


def test_unstable(command, history_unstable):
    command._append_data(history_unstable)

    assert not command._equilibrium_reached(command._history)
