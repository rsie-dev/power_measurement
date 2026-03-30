from collections import defaultdict
import random

import pytest

from experiment.run.steps import MeasurementStep
from .command_config_shuffle import command_config_shuffle


@pytest.fixture
def config_list():
    return [
        MeasurementStep.CommandConfig(run=1, runs=2, commands=[], tag="a", log_providers=[]),
        MeasurementStep.CommandConfig(run=2, runs=2, commands=[], tag="a", log_providers=[]),
        MeasurementStep.CommandConfig(run=1, runs=3, commands=[], tag="b", log_providers=[]),
        MeasurementStep.CommandConfig(run=2, runs=3, commands=[], tag="b", log_providers=[]),
        MeasurementStep.CommandConfig(run=3, runs=3, commands=[], tag="b", log_providers=[]),
    ]


def test_command_config_shuffle_preserves_run_order(config_list):  # pylint: disable=redefined-outer-name
    result = command_config_shuffle(config_list)

    # Track last seen run per group
    last_seen = defaultdict(lambda: 0)

    for cfg in result:
        key = cfg.tag
        assert cfg.run > last_seen[key], \
            f"Order violated for group {key}"
        last_seen[key] = cfg.run


def test_command_config_shuffle_changes_order(config_list):  # pylint: disable=redefined-outer-name
    # Run multiple times to reduce flakiness
    results = [tuple(command_config_shuffle(config_list)) for _ in range(10)]

    # At least one result should differ from input order
    assert any(list(r) != config_list for r in results)


def test_command_config_shuffle_deterministic(config_list):  # pylint: disable=redefined-outer-name
    rng = random.Random(0)

    result = command_config_shuffle(config_list, rng=rng)

    assert result == [
        MeasurementStep.CommandConfig(run=1, runs=3, commands=[], tag="b", log_providers=[]),
        MeasurementStep.CommandConfig(run=2, runs=3, commands=[], tag="b", log_providers=[]),
        MeasurementStep.CommandConfig(run=1, runs=2, commands=[], tag="a", log_providers=[]),
        MeasurementStep.CommandConfig(run=3, runs=3, commands=[], tag="b", log_providers=[]),
        MeasurementStep.CommandConfig(run=2, runs=2, commands=[], tag="a", log_providers=[]),
    ]
