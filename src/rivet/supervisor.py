from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ServiceSpec:
    name: str
    critical: bool = False
    max_restarts: int = 3


@dataclass
class ServiceStatus:
    name: str
    state: str = "stopped"
    restart_count: int = 0
    last_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RivetSupervisor:
    """Restart policy model; process execution remains an integration boundary."""

    def __init__(self) -> None:
        self.specs: dict[str, ServiceSpec] = {}
        self.services: dict[str, ServiceStatus] = {}

    def register(self, spec: ServiceSpec) -> None:
        self.specs[spec.name] = spec
        self.services[spec.name] = ServiceStatus(spec.name)

    def start(self, name: str) -> ServiceStatus:
        status = self.services[name]
        status.state = "running"
        return status

    def exited(self, name: str, reason: str) -> ServiceStatus:
        spec = self.specs[name]
        status = self.services[name]
        status.last_reason = reason
        if status.restart_count < spec.max_restarts:
            status.restart_count += 1
            status.state = "restarting"
        else:
            status.state = "failed" if spec.critical else "stopped"
        return status

    def status(self) -> list[dict[str, Any]]:
        return [status.to_dict() for status in sorted(self.services.values(), key=lambda item: item.name)]
