from .metrics import SystemMeasurement


class MeasurementLogger:
    def init(self) -> None:
        pass

    def log(self, measurement: SystemMeasurement) -> None:
        pass

    def close(self) -> None:
        pass
