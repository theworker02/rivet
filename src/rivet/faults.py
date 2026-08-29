from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .runtime import RobotRuntime


@dataclass(frozen=True)
class Fault:
    target: str
    kind: str
    active: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"target": self.target, "kind": self.kind, "active": self.active, "detail": self.detail}


class FaultInjector:
    """Simulation-only fault injection that uses the normal bus and safe-state seams."""

    def __init__(self, runtime: RobotRuntime) -> None:
        self.runtime = runtime
        self._faults: dict[str, Fault] = {}
        self._removed: dict[str, Any] = {}

    def disconnect(self, target: str) -> Fault:
        device = self.runtime.devices.get(target)
        if device is None:
            raise KeyError(f"simulated device not found: {target}")
        if hasattr(device, "safe"):
            device.safe()
        self._removed[target] = self.runtime.devices.pop(target)
        fault = Fault(target, "disconnect", True, "device removed by simulation fault injector")
        self._faults[target] = fault
        self.runtime.bus.publish("fault", target, {"code": "SIMULATED_DISCONNECT", "detail": fault.detail})
        return fault

    def restore(self, target: str) -> Fault:
        if target not in self._faults:
            raise KeyError(f"no active simulation fault: {target}")
        fault = Fault(target, self._faults[target].kind, False, "device restored by simulation fault injector")
        self.runtime.devices[target] = self._removed.pop(target)
        self._faults.pop(target, None)
        self.runtime.bus.publish("device.restored", target, {"detail": fault.detail})
        return fault

    def active(self) -> list[dict[str, Any]]:
        return [fault.to_dict() for fault in self._faults.values()]
