from abc import abstractmethod

from .step import Step


class RunResourceStep(Step):
    @abstractmethod
    def get_run_prefix(self) -> str:
        pass
