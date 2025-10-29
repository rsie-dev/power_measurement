import logging
from typing import Callable, List, Optional
import inspect


class Step:
    def __init__(self, func: Callable, name: str):
        self.func = func
        self.name = name
        self.signature = inspect.signature(func)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class Experiment:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps: List[Step] = []
        self._installed_names = set()

    def step(self, name: Optional[str] = None):
        """
        Decorator factory to register a step.
        Usage:
          @Experiment.step()
          def read(): ...
        """
        def decorator(fn: Callable):
            step_name = name or fn.__name__
            if step_name in self._installed_names:
                raise RuntimeError(f"step already registered: {step_name}")

            step = Step(fn, name=step_name)
            self._steps.append(step)
            self._installed_names.add(step_name)
            return fn
        return decorator

    def _get_steps(self):
        # return steps sorted by explicit order then by registration order
        #return sorted(self._steps, key=lambda s: (s.order if s.order is not None else 0, self._steps.index(s)))
        return self._steps[:]

    def run(self):
        """
        Execute the experiment: calls each step.
        """
        for step in self._get_steps():
            self._logger.debug("execute step: %s", step.name)
            fn = step.func
            fn()


E = Experiment()
