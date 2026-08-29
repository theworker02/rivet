from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any

from .continuum import Governor, ResourceSnapshot, RuntimeClassifier


@dataclass(frozen=True)
class CompatibilityRow:
    feature: str
    support: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {"feature": self.feature, "support": dict(self.support)}


class CompatibilityMatrix:
    platforms = ("Pi Zero 2 W", "Pi 3", "Pi 4", "Pi 5")
    rows = (
        CompatibilityRow("Core runtime", {"Pi Zero 2 W": "✓", "Pi 3": "✓", "Pi 4": "✓", "Pi 5": "✓"}),
        CompatibilityRow("GPIO drivers", {"Pi Zero 2 W": "✓", "Pi 3": "✓", "Pi 4": "✓", "Pi 5": "✓"}),
        CompatibilityRow("Recorder", {"Pi Zero 2 W": "Limited", "Pi 3": "✓", "Pi 4": "✓", "Pi 5": "✓"}),
        CompatibilityRow("Vision", {"Pi Zero 2 W": "Limited", "Pi 3": "Limited", "Pi 4": "✓", "Pi 5": "✓"}),
        CompatibilityRow("Sensor fusion", {"Pi Zero 2 W": "—", "Pi 3": "Limited", "Pi 4": "✓", "Pi 5": "✓"}),
        CompatibilityRow("Multi-model inference", {"Pi Zero 2 W": "—", "Pi 3": "—", "Pi 4": "Limited", "Pi 5": "✓"}),
    )

    def to_dict(self) -> dict[str, Any]:
        return {"platforms": list(self.platforms), "rows": [row.to_dict() for row in self.rows]}

    def text(self) -> str:
        lines = ["RIVET COMPATIBILITY", "", "Feature".ljust(24) + "".join(platform.ljust(16) for platform in self.platforms)]
        lines.append("-" * len(lines[-1]))
        for row in self.rows:
            lines.append(row.feature.ljust(24) + "".join(row.support[platform].ljust(16) for platform in self.platforms))
        lines.append("\nHardware-specific rows require the corresponding driver evidence; matrix entries are not certification.")
        return "\n".join(lines)


@dataclass(frozen=True)
class ResourceTierResult:
    tier: str
    budget_mb: int
    profile: str
    state: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResourceTierTester:
    budgets = {"nano": 64, "core": 128, "full": 512}

    def run(self) -> list[ResourceTierResult]:
        classifier = RuntimeClassifier()
        governor = Governor()
        results: list[ResourceTierResult] = []
        for tier, budget in self.budgets.items():
            snapshot = ResourceSnapshot(budget, ram_used_percent=50.0, temperature_c=45.0)
            profile = classifier.classify(snapshot)
            decision = governor.evaluate(snapshot)
            passed = profile.name in {"nano", "core", "full"} and decision.state == "normal"
            results.append(ResourceTierResult(tier, budget, profile.name, decision.state, passed, "profile and governor remained functional"))
        return results


@dataclass(frozen=True)
class PerformanceBudget:
    core_idle_rss_mb: float = 45.0
    cli_startup_ms: float = 500.0
    capability_lookup_ms: float = 2.0
    config_parse_ms: float = 100.0

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    elapsed_ms: float
    budget_ms: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RuntimeBenchmark:
    def run(self, runtime: Any | None = None) -> list[BenchmarkResult]:
        from .configuration import ConfigLoader
        from .runtime import RobotRuntime
        from .simulator import SimulatedRobot

        runtime = runtime or RobotRuntime()
        runtime.register_simulator(SimulatedRobot()) if not runtime.registry.list() else None
        budget = PerformanceBudget()
        results: list[BenchmarkResult] = []
        start = time.perf_counter()
        for _ in range(1000):
            runtime.registry.get("motion.left-wheel")
        lookup_ms = (time.perf_counter() - start) * 1000.0 / 1000.0
        results.append(BenchmarkResult("capability lookup", lookup_ms, budget.capability_lookup_ms, lookup_ms <= budget.capability_lookup_ms))
        start = time.perf_counter()
        ConfigLoader().validate(value={"rivet": 2, "robot": {"id": "benchmark"}})
        parse_ms = (time.perf_counter() - start) * 1000.0
        results.append(BenchmarkResult("configuration parse", parse_ms, budget.config_parse_ms, parse_ms <= budget.config_parse_ms))
        return results
