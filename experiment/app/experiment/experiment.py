import logging
from typing import List

from .steps import Step


class Experiment:
    def __init__(self, steps: List[Step]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps = steps

    def _get_steps(self):
        return self._steps[:]

    def run(self):
        """
        Execute the experiment: calls each step.
        """
        for step in self._get_steps():
            self._logger.debug("execute step: %s", step.name)
            step.execute()
