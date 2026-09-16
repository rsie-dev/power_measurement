from unittest.mock import Mock, create_autospec

import pytest

from experiment.run.base import ExperimentEnvironment, ExperimentRuntime
from experiment.run.steps import Step

from .experiment_runner import ExperimentRunner

# pylint: disable=redefined-outer-name


def _step(name: str, events: list[str]) -> Mock:
    step = create_autospec(Step, instance=True)
    step.name = name
    step.description = name

    step.prepare.side_effect = lambda *_args: events.append(f"prepare:{name}")
    step.start.side_effect = lambda *_args: events.append(f"start:{name}")
    step.execute.side_effect = lambda *_args: events.append(f"execute:{name}")
    step.stop.side_effect = lambda *_args: events.append(f"stop:{name}")
    return step


@pytest.fixture
def lifecycle():
    return {
        "executor": Mock(),
        "runtime": create_autospec(ExperimentRuntime, instance=True),
        "environment": create_autospec(ExperimentEnvironment, instance=True),
    }


def test_execute_runs_lifecycle(tmp_path, lifecycle):
    events = []
    first = _step("first", events)
    second = _step("second", events)
    runner = ExperimentRunner(lifecycle["executor"], tmp_path, [first, second])

    runner.execute_runs(lifecycle["runtime"], lifecycle["environment"])

    assert events == [
        "prepare:first",
        "prepare:second",
        "start:first",
        "start:second",
        "execute:first",
        "execute:second",
        "stop:second",
        "stop:first",
    ]


def test_execute_runs_only_stop_started(tmp_path, lifecycle):
    events = []
    first = _step("first", events)
    second = _step("failing", events)
    third = _step("never-started", events)

    def fail_start(*_args):
        events.append("start:failing")
        raise RuntimeError("start failed")

    second.start.side_effect = fail_start
    runner = ExperimentRunner(
        lifecycle["executor"],
        tmp_path,
        [first, second, third],
    )

    with pytest.raises(RuntimeError):
        runner.execute_runs(lifecycle["runtime"], lifecycle["environment"])

    assert events == [
        "prepare:first",
        "prepare:failing",
        "prepare:never-started",
        "start:first",
        "start:failing",
        "stop:failing",
        "stop:first",
    ]
    first.stop.assert_called_once()
    second.stop.assert_called_once()
    third.start.assert_not_called()
    third.stop.assert_not_called()
