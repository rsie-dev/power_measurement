from .executor_command import ExecutorCommand


class ClearCacheCommand(ExecutorCommand):
    CLEAR_COMMAND = "sync; echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null"

    def __init__(self):
        super().__init__(self.CLEAR_COMMAND, "/bin/sh")
