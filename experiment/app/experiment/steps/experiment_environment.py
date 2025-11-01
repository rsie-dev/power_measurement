from pathlib import Path

from app.common import ShutdownHandler


class ExperimentEnvironment:
    def get_resources_path(self) -> Path:
        return None

    def add_shutdown_handler(self, handler: ShutdownHandler):
        pass

    def register_for_system_meter(self, host: str) -> None:
        pass
