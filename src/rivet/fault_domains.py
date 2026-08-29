from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DOMAINS = ("core", "safety", "motion", "perception", "network", "missions", "ui", "recording")


@dataclass(frozen=True)
class DomainFault:
    domain: str
    detail: str
    state: str = "failed"

    def to_dict(self) -> dict[str, str]:
        return {"domain": self.domain, "detail": self.detail, "state": self.state}


class FaultDomainManager:
    """Contains non-safety failures while making safety failure fail closed."""

    def __init__(self, bus: Any, runtime: Any, domains: tuple[str, ...] = DOMAINS) -> None:
        self.bus = bus
        self.runtime = runtime
        self._states = {domain: "healthy" for domain in domains}
        self._faults: list[DomainFault] = []

    def record(self, domain: str, detail: str) -> DomainFault:
        if domain not in self._states:
            raise ValueError(f"unknown fault domain: {domain}")
        fault = DomainFault(domain, detail)
        self._states[domain] = "failed"
        self._faults.append(fault)
        self.bus.publish("fault.domain", domain, fault.to_dict())
        if domain == "safety":
            for device in self.runtime.devices.values():
                if hasattr(device, "safe"):
                    device.safe()
            self.runtime.leases.revoke_all()
            self.runtime.authority.revoke_all()
            self.bus.publish("safety.failure", "fault-domains", {"detail": detail, "actuators": "disabled"})
        return fault

    def recover(self, domain: str) -> None:
        if domain not in self._states:
            raise ValueError(f"unknown fault domain: {domain}")
        self._states[domain] = "healthy"
        self.bus.publish("fault.domain.recovered", domain, {})

    def status(self) -> dict[str, str]:
        return dict(self._states)

    def faults(self) -> list[dict[str, str]]:
        return [fault.to_dict() for fault in self._faults]
