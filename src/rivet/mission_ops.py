from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from .mission import MissionPlan, MissionSpec


@dataclass(frozen=True)
class DryRunReport:
    mission_id: str
    role_requirements: bool
    skill_requirements: bool
    hardware: bool
    safety_policy: bool
    estimated_runtime_s: float
    estimated_battery_percent: float
    planned_actions: tuple[str, ...]
    admission: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.role_requirements and self.skill_requirements and self.hardware and self.safety_policy

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["planned_actions"] = list(self.planned_actions)
        value["ok"] = self.ok
        return value

    def text(self) -> str:
        status = "PASS" if self.ok else "BLOCKED"
        lines = ["MISSION DRY RUN", "", f"Readiness                  {status}"]
        for label, result in (
            ("Role requirement", self.role_requirements),
            ("Skill requirements", self.skill_requirements),
            ("Hardware", self.hardware),
            ("Safety policy", self.safety_policy),
        ):
            lines.append(f"{label:<28} {'PASS' if result else 'FAIL'}")
        lines.extend(
            [
                f"Estimated runtime           {self.estimated_runtime_s:.0f}s",
                f"Estimated battery use       {self.estimated_battery_percent:.1f}%",
                "",
                f"Planned actions: {len(self.planned_actions)}",
            ]
        )
        lines.extend(f"- {action}" for action in self.planned_actions)
        lines.append("")
        lines.append("No hardware commands were executed.")
        return "\n".join(lines)


class MissionDryRunner:
    def evaluate(self, mission: MissionSpec, plan: MissionPlan, admission: dict[str, Any], runtime: Any) -> DryRunReport:
        role_ok = bool(admission.get("admitted", False) or not mission.required_role)
        skills_ok = not admission.get("missing_skills")
        hardware_ok = all(path in {cap.path for cap in runtime.registry.list()} for path in self._hardware_requirements(runtime, mission))
        guard = getattr(runtime, "guard", None)
        safety_ok = bool(runtime.registry.list()) and not bool(getattr(guard, "estop", False))
        estimated_runtime = max(1.0, len(plan.steps) * 120.0)
        estimated_battery = min(100.0, len(plan.steps) * 6.0)
        return DryRunReport(
            mission.mission_id,
            role_ok,
            skills_ok,
            hardware_ok,
            safety_ok,
            estimated_runtime,
            estimated_battery,
            tuple(step.action for step in plan.steps),
            admission,
        )

    @staticmethod
    def _hardware_requirements(runtime: Any, mission: MissionSpec) -> tuple[str, ...]:
        declared = mission.constraints.get("requires_hardware", ())
        return tuple(declared)


@dataclass(frozen=True)
class MissionCheckpoint:
    mission_id: str
    step_index: int
    total_steps: int
    environment_fingerprint: str
    verified: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MissionCheckpointStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._checkpoint: MissionCheckpoint | None = None

    def save(self, checkpoint: MissionCheckpoint) -> None:
        self._checkpoint = checkpoint
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(checkpoint.to_dict(), indent=2) + "\n", encoding="utf-8")

    def load(self) -> MissionCheckpoint | None:
        if self.path is not None and self.path.exists():
            value = json.loads(self.path.read_text(encoding="utf-8"))
            self._checkpoint = MissionCheckpoint(**value)
        return self._checkpoint

    def clear(self) -> None:
        self._checkpoint = None
        if self.path is not None and self.path.exists():
            self.path.unlink()


class MissionTransaction:
    """Logical mission transaction with explicit compensating actions."""

    def __init__(self) -> None:
        self.reservations: list[str] = []
        self.compensations: list[tuple[str, Callable[[], None]]] = []
        self.committed = False

    def reserve(self, resource: str, compensate: Callable[[], None]) -> None:
        if self.committed:
            raise RuntimeError("cannot reserve after transaction commit")
        self.reservations.append(resource)
        self.compensations.append((resource, compensate))

    def commit(self) -> tuple[str, ...]:
        self.committed = True
        self.compensations.clear()
        return tuple(self.reservations)

    def rollback(self) -> tuple[str, ...]:
        released: list[str] = []
        for resource, compensate in reversed(self.compensations):
            compensate()
            released.append(resource)
        self.reservations.clear()
        self.compensations.clear()
        return tuple(released)


class MissionExecutor:
    def execute(
        self,
        plan: MissionPlan,
        action: Callable[[Any], None],
        checkpoint_store: MissionCheckpointStore | None = None,
        environment_check: Callable[[], bool] | None = None,
    ) -> MissionCheckpoint:
        store = checkpoint_store or MissionCheckpointStore()
        checkpoint = store.load()
        start = 0
        if checkpoint is not None:
            if checkpoint.mission_id != plan.mission.mission_id or not (environment_check or (lambda: True))():
                raise RuntimeError("interrupted mission environment requires revalidation before resume")
            start = checkpoint.step_index
        for index, step in enumerate(plan.steps[start:], start):
            if environment_check is not None and not environment_check():
                raise RuntimeError(f"environment changed before mission step {index + 1}")
            action(step)
            checkpoint = MissionCheckpoint(plan.mission.mission_id, index + 1, len(plan.steps), plan.mission.mission_id)
            store.save(checkpoint)
        return checkpoint or MissionCheckpoint(plan.mission.mission_id, 0, len(plan.steps), plan.mission.mission_id)
