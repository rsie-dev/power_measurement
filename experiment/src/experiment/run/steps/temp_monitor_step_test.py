import datetime
from unittest.mock import Mock

import pytest
from usb_multimeter import ElectricalMeasurement, Device

from .temp_monitor_step import TempMonitorStep

# pylint: disable=redefined-outer-name
# pylint: disable=protected-access


@pytest.fixture
def test_now():
    times = [
        datetime.datetime(2026, 1, 1, 0, 0, 0),
        datetime.datetime(2026, 1, 1, 0, 0, 3),
    ]

    def fake_now():
        return times.pop(0)

    return fake_now


@pytest.fixture
def test_step(test_now):
    test_step = TempMonitorStep(log_dispatcher=None, max_temp_delta=1.0, now=test_now)
    return test_step


def measurement(temperature: float):
    device = Mock(spec=Device)
    timestamp = datetime.datetime.now()
    return ElectricalMeasurement(device=device,
                                 timestamp=timestamp,
                                 voltage=0, current=0,
                                 dp=0, dn=0,
                                 temperature=temperature,
                                 energy=0,
                                 capacity=0)


def test_in_range_high(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data = measurement(temperature=11.0)

    test_step._log_measurement(test_data)

    assert test_step.abort_measurement() is False


def test_in_range_low(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data = measurement(temperature=9.0)

    test_step._log_measurement(test_data)

    assert test_step.abort_measurement() is False


def test_out_of_range_high(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data1 = measurement(temperature=11.1)
    test_step._log_measurement(test_data1)
    test_data2 = measurement(temperature=11.1)

    test_step._log_measurement(test_data2)

    assert test_step.abort_measurement() is True


def test_out_of_range_low(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data1 = measurement(temperature=8.9)
    test_step._log_measurement(test_data1)
    test_data2 = measurement(temperature=8.9)

    test_step._log_measurement(test_data2)

    assert test_step.abort_measurement() is True


def test_out_of_range_high_low_cross(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data1 = measurement(temperature=11.1)
    test_step._log_measurement(test_data1)
    test_data2 = measurement(temperature=8.9)

    test_step._log_measurement(test_data2)

    assert test_step.abort_measurement() is True


def test_out_of_range_low_high_cross(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data1 = measurement(temperature=8.9)
    test_step._log_measurement(test_data1)
    test_data2 = measurement(temperature=11.1)

    test_step._log_measurement(test_data2)

    assert test_step.abort_measurement() is True


def test_out_of_range_high_to_range(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data1 = measurement(temperature=11.1)
    test_step._log_measurement(test_data1)
    test_data2 = measurement(temperature=10.0)

    test_step._log_measurement(test_data2)

    assert test_step.abort_measurement() is False


def test_out_of_range_low_to_range(test_step):
    init_data = measurement(temperature=10.0)
    test_step._log_measurement(init_data)
    test_data1 = measurement(temperature=8.9)
    test_step._log_measurement(test_data1)
    test_data2 = measurement(temperature=10.0)

    test_step._log_measurement(test_data2)

    assert test_step.abort_measurement() is False
