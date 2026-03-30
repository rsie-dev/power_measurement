import random
from collections import defaultdict
from experiment.run.steps import MeasurementStep


def command_config_shuffle(configs: list[MeasurementStep.CommandConfig], rng: random.Random | None = None
                           ) -> list[MeasurementStep.CommandConfig]:
    if rng is None:
        rng = random

    # Group and sort each chain with ascending runs
    groups = defaultdict(list)
    for cfg in configs:
        groups[cfg.tag].append(cfg)
    for key in groups:
        groups[key].sort(key=lambda x: x.run)

    queues = list(groups.values())

    result = []
    while queues:
        queue = rng.choice(queues)
        result.append(queue.pop(0))
        if not queue:
            queues.remove(queue)

    return result
