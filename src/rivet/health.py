from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable


class HealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNSTABLE = "UNSTABLE"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass
class CapabilityHealth:
    capability: str
    health: float = 1.0
    state: HealthState = HealthState.UNKNOWN
    metrics: dict[str, float] = field(default_factory=dict)
    last_event: str | None = None
    updated_ns: int = 0

    def __post_init__(self) -> None:
        if self.updated_ns == 0:
            self.updated_ns = time.monotonic_ns()
        self._refresh_state()

    def update(self, health: float, metrics: dict[str, float] | None = None, event: str | None = None) -> None:
        if not 0.0 <= health <= 1.0:
            raise ValueError("capability health must be between 0 and 1")
        self.health = health
        self.metrics = dict(metrics or self.metrics)
        self.last_event = event or self.last_event
        self.updated_ns = time.monotonic_ns()
        self._refresh_state()

    def _refresh_state(self) -> None:
        if self.health >= 0.9:
            self.state = HealthState.HEALTHY
        elif self.health >= 0.7:
            self.state = HealthState.DEGRADED
        elif self.health > 0.0:
            self.state = HealthState.UNSTABLE
        elif self.health == 0.0:
            self.state = HealthState.FAILED
        else:
            self.state = HealthState.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        value["health_percent"] = round(self.health * 100.0, 2)
        return value


@dataclass(frozen=True)
class RecoveryAttempt:
    target: str
    attempt: int
    action: str
    success: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RecoveryResult:
    target: str
    recovered: bool
    attempts: tuple[RecoveryAttempt, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"target": self.target, "recovered": self.recovered, "attempts": [attempt.to_dict() for attempt in self.attempts]}


class HealthManager:
    """Tracks capability quality and performs bounded, observable recovery."""

    def __init__(self, bus: Any, clock_ns: Callable[[], int] | None = None) -> None:
        self.bus = bus
        self._clock_ns = clock_ns or time.monotonic_ns
        self.capabilities: dict[str, CapabilityHealth] = {}
        self.recovery_history: list[RecoveryResult] = []
        bus.subscribe("fault", self._on_fault)
        bus.subscribe("device.restored", self._on_restored)

    def register(self, capability: str) -> CapabilityHealth:
        return self.capabilities.setdefault(capability, CapabilityHealth(capability, updated_ns=self._clock_ns()))

    def update(self, capability: str, health: float, metrics: dict[str, float] | None = None, event: str | None = None) -> CapabilityHealth:
        state = self.register(capability)
        state.update(health, metrics, event)
        self.bus.publish("capability.health", capability, state.to_dict())
        return state

    def mark_failed(self, capability: str, detail: str) -> CapabilityHealth:
        return self.update(capability, 0.0, {"availability": 0.0}, detail)

    def mark_recovered(self, capability: str, health: float = 1.0) -> CapabilityHealth:
        return self.update(capability, health, {"availability": 1.0}, "recovered")

    def recover(
        self,
        target: str,
        actions: tuple[tuple[str, Callable[[], bool]], ...],
        max_attempts: int = 3,
    ) -> RecoveryResult:
        if max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        attempts: list[RecoveryAttempt] = []
        for index, (name, action) in enumerate(actions[:max_attempts], 1):
            try:
                success = bool(action())
                detail = "recovery action succeeded" if success else "recovery action reported failure"
            except Exception as exc:  # recovery evidence must survive driver errors
                success = False
                detail = f"{type(exc).__name__}: {exc}"
            attempt = RecoveryAttempt(target, index, name, success, detail)
            attempts.append(attempt)
            self.bus.publish("capability.recovery", target, attempt.to_dict())
            if success:
                self.mark_recovered(target)
                result = RecoveryResult(target, True, tuple(attempts))
                self.recovery_history.append(result)
                return result
        self.mark_failed(target, "recovery-exhausted")
        result = RecoveryResult(target, False, tuple(attempts))
        self.recovery_history.append(result)
        return result

    def status(self) -> dict[str, dict[str, Any]]:
        return {path: health.to_dict() for path, health in sorted(self.capabilities.items())}

    def _on_fault(self, event: Any) -> None:
        if event.source in self.capabilities:
            self.mark_failed(event.source, event.payload.get("code", "fault"))

    def _on_restored(self, event: Any) -> None:
        if event.source in self.capabilities:
            self.mark_recovered(event.source)
