from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

from .models import Event


@dataclass
class Pulse:
    """Compact liveness and quality signal for one runtime component."""

    component: str
    health: float = 1.0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    last_event: str | None = None
    timestamp_ns: int = 0
    resource_use: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"health_percent": round(self.health * 100.0, 2)}


class PulseFabric:
    """Synchronous health/event fabric built on the existing Rivet event bus."""

    def __init__(self, bus: Any, clock_ns: Callable[[], int] | None = None) -> None:
        self.bus = bus
        self._clock_ns = clock_ns or time.monotonic_ns
        self._pulses: dict[str, Pulse] = {}
        bus.subscribe("*", self._observe)

    def heartbeat(
        self,
        component: str,
        latency_ms: float = 0.0,
        health: float = 1.0,
        error_rate: float = 0.0,
        resource_use: dict[str, float] | None = None,
    ) -> Pulse:
        if not 0.0 <= health <= 1.0:
            raise ValueError("pulse health must be between 0 and 1")
        if not 0.0 <= error_rate <= 1.0:
            raise ValueError("pulse error rate must be between 0 and 1")
        pulse = Pulse(component, health, max(0.0, latency_ms), error_rate, "heartbeat", self._clock_ns(), resource_use or {})
        self._pulses[component] = pulse
        self.bus.publish("pulse.heartbeat", component, pulse.to_dict())
        return pulse

    def fail(self, component: str, detail: str, error_rate: float = 1.0) -> Pulse:
        pulse = self._pulses.get(component) or Pulse(component)
        pulse.health = 0.0
        pulse.error_rate = min(1.0, max(0.0, error_rate))
        pulse.last_event = detail
        pulse.timestamp_ns = self._clock_ns()
        self._pulses[component] = pulse
        self.bus.publish("pulse.failed", component, {"detail": detail, **pulse.to_dict()})
        return pulse

    def get(self, component: str) -> Pulse:
        return self._pulses[component]

    def snapshot(self) -> dict[str, dict[str, Any]]:
        return {component: pulse.to_dict() for component, pulse in sorted(self._pulses.items())}

    def status(self) -> list[dict[str, Any]]:
        return list(self.snapshot().values())

    def _observe(self, event: Event) -> None:
        if event.type.startswith("pulse."):
            return
        component = event.source.split(".", 1)[0] if event.source else "runtime"
        pulse = self._pulses.get(component)
        if pulse is None:
            pulse = Pulse(component)
            self._pulses[component] = pulse
        pulse.last_event = event.type
        pulse.timestamp_ns = event.timestamp_ns
