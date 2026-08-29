from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Callable, Any

from .runtime import RobotRuntime


@dataclass(frozen=True)
class GuardStatus:
    armed: bool
    estop: bool
    reason: str | None
    watched_heartbeats: int
    safety_mode: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class _Heartbeat:
    name: str
    expires_at: float


class RivetGuard:
    """Small, dependency-light safety boundary that can outlive high-level services."""

    def __init__(self, runtime: RobotRuntime, clock: Callable[[], float] | None = None) -> None:
        self.runtime = runtime
        self._clock = clock or time.monotonic
        self._heartbeats: dict[str, _Heartbeat] = {}
        self.armed = False
        self.estop = False
        self.reason: str | None = None

    def arm(self) -> None:
        if self.estop:
            raise RuntimeError("cannot arm while emergency stop is active")
        self.armed = True
        self.runtime.bus.publish("guard.armed", "rivet-guard", {})

    def watch(self, name: str, timeout_s: float) -> None:
        self._heartbeats[name] = _Heartbeat(name, self._clock() + timeout_s)

    def heartbeat(self, name: str, timeout_s: float | None = None) -> None:
        current = self._heartbeats.get(name)
        if current is None:
            if timeout_s is None:
                raise KeyError(f"heartbeat is not registered: {name}")
            timeout = timeout_s
        else:
            timeout = timeout_s if timeout_s is not None else max(0.0, current.expires_at - self._clock())
        self._heartbeats[name] = _Heartbeat(name, self._clock() + timeout)
        self.runtime.bus.publish("guard.heartbeat", name, {"name": name})

    def emergency_stop(self, reason: str) -> list[str]:
        stopped: list[str] = []
        for path, device in self.runtime.devices.items():
            if hasattr(device, "safe"):
                device.safe()
                stopped.append(path)
        self.runtime.leases.revoke_all()
        self.runtime.authority.revoke_all()
        self.estop = True
        self.armed = False
        self.reason = reason
        self.runtime.bus.publish("guard.estop", "rivet-guard", {"reason": reason, "stopped": stopped})
        return stopped

    def reset_estop(self) -> None:
        self.estop = False
        self.reason = None
        self.runtime.bus.publish("guard.reset", "rivet-guard", {})

    def tick(self, now: float | None = None) -> GuardStatus:
        current = self._clock() if now is None else now
        expired = [heartbeat.name for heartbeat in self._heartbeats.values() if heartbeat.expires_at <= current]
        if expired and not self.estop:
            self.emergency_stop("heartbeat-expired:" + ",".join(sorted(expired)))
        if not self.estop:
            self.runtime.tick(current)
        return self.status()

    def status(self) -> GuardStatus:
        return GuardStatus(self.armed, self.estop, self.reason, len(self._heartbeats), "estop" if self.estop else "armed" if self.armed else "standby")
