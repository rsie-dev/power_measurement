from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class Host:
    host_name: str
    host: str


@dataclass(frozen=True, kw_only=True)
class SSHHost(Host):
    ssh_user: str
