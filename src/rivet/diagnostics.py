from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .continuum import ResourceSnapshot
from .guard import RivetGuard
from .hardware import HardwareGraph
from .runtime import RobotRuntime


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiagnosticReport:
    ok: bool
    checks: tuple[CheckResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "checks": [check.to_dict() for check in self.checks]}


class Doctor:
    def run(self, runtime: RobotRuntime, graph: HardwareGraph | None = None, resources: ResourceSnapshot | None = None, guard: RivetGuard | None = None) -> DiagnosticReport:
        checks = [
            CheckResult("capability-registry", bool(runtime.registry.list()), f"{len(runtime.registry.list())} capabilities discovered"),
            CheckResult("command-boundary", all(hasattr(device, "command") and hasattr(device, "safe") for device in runtime.devices.values()), "commandable devices expose command and safe"),
        ]
        if graph is not None:
            lost = [node.node_id for node in graph.nodes.values() if node.health != "healthy"]
            checks.append(CheckResult("hardware-topology", not lost, "healthy" if not lost else "unhealthy: " + ", ".join(lost)))
        if resources is not None:
            checks.append(CheckResult("thermal", resources.temperature_c < 85.0, f"{resources.temperature_c:.1f}C"))
            checks.append(CheckResult("memory", resources.ram_used_percent < 90.0, f"{resources.ram_used_percent:.1f}% used"))
        if guard is not None:
            checks.append(CheckResult("safety-guard", not guard.estop, "ready" if not guard.estop else guard.reason or "estop"))
        return DiagnosticReport(all(check.ok for check in checks), tuple(checks))


class Preflight:
    def run(self, runtime: RobotRuntime, report: DiagnosticReport) -> DiagnosticReport:
        checks = list(report.checks)
        motion = [cap.path for cap in runtime.registry.list() if cap.path.startswith("motion.")]
        checks.append(CheckResult("motion-present", bool(motion), f"{len(motion)} motion capabilities"))
        checks.append(CheckResult("motion-enabled", report.ok and bool(motion), "MOTION ENABLED" if report.ok and motion else "MOTION BLOCKED"))
        return DiagnosticReport(all(check.ok for check in checks), tuple(checks))
