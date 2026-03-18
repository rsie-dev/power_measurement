from dataclasses import dataclass


@dataclass(frozen=True)
class HostInfo:
    user: str
    host_name: str
