from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Callable

from .runtime import RobotRuntime


@dataclass(frozen=True)
class ResourceSnapshot:
    """Point-in-time host resources used to choose and govern a runtime profile."""

    ram_total_mb: int
    ram_used_percent: float = 0.0
    swap_used_percent: float = 0.0
    cpu_percent: float = 0.0
    temperature_c: float = 0.0
    storage_free_percent: float = 100.0
    gpu_memory_mb: int = 0
    network_latency_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    target_ram_mb: int
    dashboard: bool
    recorder: str
    vision: str
    telemetry: str
    perception_fusion: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


PROFILES = {
    "nano": RuntimeProfile("nano", 64, False, "ring-buffer", "disabled", "minimal", False),
    "core": RuntimeProfile("core", 256, False, "enabled", "lightweight", "standard", False),
    "full": RuntimeProfile("full", 1024, True, "full", "enabled", "full", True),
}


class RuntimeClassifier:
    """Selects the least constrained profile supported by detected RAM."""

    def classify(self, snapshot: ResourceSnapshot) -> RuntimeProfile:
        if snapshot.ram_total_mb < 128:
            return PROFILES["nano"]
        if snapshot.ram_total_mb < 768:
            return PROFILES["core"]
        return PROFILES["full"]


@dataclass(frozen=True)
class GovernorDecision:
    state: str
    actions: tuple[str, ...]
    reasons: tuple[str, ...]
    snapshot: ResourceSnapshot

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["actions"] = list(self.actions)
        value["reasons"] = list(self.reasons)
        value["snapshot"] = self.snapshot.to_dict()
        return value


class Governor:
    """Converts resource pressure into explicit, inspectable degradation actions."""

    def __init__(
        self,
        memory_warning: float = 75.0,
        memory_critical: float = 90.0,
        temperature_warning: float = 75.0,
        temperature_critical: float = 85.0,
    ) -> None:
        self.thresholds = {
            "memory_warning": memory_warning,
            "memory_critical": memory_critical,
            "temperature_warning": temperature_warning,
            "temperature_critical": temperature_critical,
        }
        self.last_decision: GovernorDecision | None = None

    def evaluate(self, snapshot: ResourceSnapshot) -> GovernorDecision:
        actions: list[str] = []
        reasons: list[str] = []
        memory_critical = snapshot.ram_used_percent >= self.thresholds["memory_critical"]
        temperature_critical = snapshot.temperature_c >= self.thresholds["temperature_critical"]
        memory_warning = snapshot.ram_used_percent >= self.thresholds["memory_warning"]
        temperature_warning = snapshot.temperature_c >= self.thresholds["temperature_warning"]
        if memory_critical:
            reasons.append("memory-critical")
        elif memory_warning:
            reasons.append("memory-warning")
        if temperature_critical:
            reasons.append("temperature-critical")
        elif temperature_warning:
            reasons.append("temperature-warning")
        if memory_critical or temperature_critical:
            state = "safety-only"
            actions = ["shrink_cache", "flush_logs", "disable_dashboard", "pause_noncritical_agents"]
        elif memory_warning or temperature_warning:
            state = "degraded"
            actions = ["shrink_cache", "lower_video_rate", "drop_optional_telemetry"]
            if temperature_warning:
                actions.append("throttle_perception")
        else:
            state = "normal"
        decision = GovernorDecision(state, tuple(dict.fromkeys(actions)), tuple(reasons), snapshot)
        self.last_decision = decision
        return decision


@dataclass
class LifecycleEntry:
    path: str
    active: bool = True
    last_used: float = 0.0
    optional: bool = True


class CapabilityLifecycle:
    """Tracks optional capability activity and reports idle unload candidates."""

    def __init__(self, idle_unload_s: float = 300.0, clock: Callable[[], float] | None = None) -> None:
        self.idle_unload_s = idle_unload_s
        self._clock = clock or time.monotonic
        self._entries: dict[str, LifecycleEntry] = {}

    def register(self, path: str, optional: bool = True) -> None:
        self._entries[path] = LifecycleEntry(path, True, self._clock(), optional)

    def touch(self, path: str) -> None:
        entry = self._entries[path]
        entry.active = True
        entry.last_used = self._clock()

    def unload_idle(self, now: float | None = None) -> list[str]:
        current = self._clock() if now is None else now
        unloaded: list[str] = []
        for entry in self._entries.values():
            if entry.optional and entry.active and current - entry.last_used >= self.idle_unload_s:
                entry.active = False
                unloaded.append(entry.path)
        return unloaded

    def restore(self, path: str) -> None:
        entry = self._entries[path]
        entry.active = True
        entry.last_used = self._clock()

    def status(self) -> list[dict[str, Any]]:
        return [asdict(entry) for entry in sorted(self._entries.values(), key=lambda item: item.path)]


class ContinuumRuntime:
    """Phase II composition layer around the original RobotRuntime."""

    def __init__(self, runtime: RobotRuntime | None = None, clock: Callable[[], float] | None = None) -> None:
        self.runtime = runtime or RobotRuntime(clock=clock)
        self.classifier = RuntimeClassifier()
        self.governor = Governor()
        self.lifecycle = CapabilityLifecycle(clock=clock)
        self.profile: RuntimeProfile | None = None

    def boot(self, snapshot: ResourceSnapshot) -> RuntimeProfile:
        self.profile = self.classifier.classify(snapshot)
        self.runtime.bus.publish("runtime.profile.selected", "continuum", {"profile": self.profile.to_dict(), "resources": snapshot.to_dict()})
        return self.profile

    def evaluate_resources(self, snapshot: ResourceSnapshot) -> GovernorDecision:
        decision = self.governor.evaluate(snapshot)
        self.runtime.bus.publish("governor.state", "continuum", decision.to_dict())
        return decision

    def register_lifecycle(self, path: str, optional: bool = True) -> None:
        self.lifecycle.register(path, optional)

    def request_capability(self, path: str) -> None:
        self.lifecycle.restore(path)
        self.runtime.bus.publish("capability.restored", path, {"path": path})

    def status(self) -> dict[str, Any]:
        return {
            "profile": self.profile.to_dict() if self.profile else None,
            "governor": self.governor.last_decision.to_dict() if self.governor.last_decision else None,
            "lifecycle": self.lifecycle.status(),
        }
