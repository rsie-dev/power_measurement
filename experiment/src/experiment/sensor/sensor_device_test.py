import pytest
from digitemp.device import DS18B20

from .sensor_device import _get_max_update_interval


@pytest.mark.parametrize(
    ("resolution", "expected_interval"),
    [
        (DS18B20.RES_9_BIT, 10),
        (DS18B20.RES_10_BIT, 5),
        (DS18B20.RES_11_BIT, 2),
        (DS18B20.RES_12_BIT, 1),
    ],
)
def test_get_max_update_interval(resolution: int, expected_interval: int):
    assert _get_max_update_interval(resolution) == expected_interval


def test_unsupported_resolution():
    with pytest.raises(ValueError, match="Unsupported resolution"):
        _get_max_update_interval(8)
