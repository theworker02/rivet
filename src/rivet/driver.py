from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol, runtime_checkable

from .contracts import validate_contract
from .device import Device, validate_capability
from .models import Capability


@dataclass(frozen=True)
class DriverInfo:
    name: str
    version: str
    supported_types: tuple[str, ...]
    simulated: bool = False
    qualification: str = "EXPERIMENTAL"
    platforms: tuple[str, ...] = ()
    buses: tuple[str, ...] = ()
    verification: dict[str, bool] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "supported_types": list(self.supported_types),
            "simulated": self.simulated,
            "qualification": "SIMULATED" if self.simulated else self.qualification,
            "platforms": list(self.platforms),
            "buses": list(self.buses),
            "verification": dict(self.verification or {}),
        }


@dataclass(frozen=True)
class DriverQualification:
    name: str
    status: str
    checks: tuple[dict[str, Any], ...]

    @property
    def passed(self) -> bool:
        return all(check["passed"] for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status, "passed": self.passed, "checks": list(self.checks)}


@runtime_checkable
class Driver(Protocol):
    info: DriverInfo

    def discover(self) -> Iterable[tuple[Capability, Device]]: ...

    def close(self) -> None: ...


class DriverRegistry:
    """Explicit driver registry; hardware dependencies stay outside core startup."""

    def __init__(self) -> None:
        self._drivers: dict[str, Driver] = {}

    def register(self, driver: Driver) -> None:
        name = driver.info.name
        if name in self._drivers:
            raise ValueError(f"driver already registered: {name}")
        self._drivers[name] = driver

    def get(self, name: str) -> Driver:
        return self._drivers[name]

    def discover(self, name: str) -> list[tuple[Capability, Device]]:
        driver = self.get(name)
        discovered = list(driver.discover())
        paths: set[str] = set()
        for capability, device in discovered:
            validate_capability(capability)
            validate_contract(capability)
            if capability.path in paths:
                raise ValueError(f"driver discovered duplicate capability: {capability.path}")
            paths.add(capability.path)
            if not hasattr(device, "command") or not hasattr(device, "safe"):
                raise ValueError(f"driver device is missing command/safe contract: {capability.path}")
        return discovered

    def qualify(self, name: str) -> DriverQualification:
        driver = self.get(name)
        checks: list[dict[str, Any]] = []
        try:
            discovered = self.discover(name)
            checks.append({"name": "discovery", "passed": True, "detail": f"{len(discovered)} device(s) discovered"})
        except Exception as exc:
            checks.append({"name": "discovery", "passed": False, "detail": f"{type(exc).__name__}: {exc}"})
            return DriverQualification(name, "EXPERIMENTAL", tuple(checks))
        safe_ok = True
        for capability, device in discovered:
            try:
                safe_state = device.safe()
                safe_ok = safe_ok and isinstance(safe_state, dict)
            except Exception as exc:
                safe_ok = False
                checks.append({"name": f"safe:{capability.path}", "passed": False, "detail": str(exc)})
        checks.append({"name": "safe-state", "passed": safe_ok, "detail": "all discovered devices expose a dictionary safe state"})
        if driver.info.simulated:
            status = "SIMULATED"
        elif all(check["passed"] for check in checks):
            status = "TESTED"
        else:
            status = "EXPERIMENTAL"
        return DriverQualification(name, status, tuple(checks))

    def infos(self) -> list[dict[str, Any]]:
        return [self._drivers[name].info.to_dict() for name in sorted(self._drivers)]

    def qualifications(self) -> list[dict[str, Any]]:
        return [self.qualify(name).to_dict() for name in sorted(self._drivers)]

    def close(self) -> None:
        for driver in self._drivers.values():
            driver.close()
