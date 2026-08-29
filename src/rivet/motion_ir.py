from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .runtime import RobotRuntime


@dataclass(frozen=True)
class MotionOp:
    action: str
    target: str | None = None
    object_id: str | None = None
    constraints: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MotionPlan:
    plan_id: str
    operations: tuple[MotionOp, ...]
    embodiment: str
    source_skill: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"plan_id": self.plan_id, "operations": [operation.to_dict() for operation in self.operations], "embodiment": self.embodiment, "source_skill": self.source_skill}


class EmbodimentCompiler:
    """Compiles intent-level operations into a body-specific plan without joint replay."""

    def compile(self, plan_id: str, operations: Iterable[MotionOp], embodiment: str, source_skill: str | None = None) -> MotionPlan:
        operations = tuple(operations)
        if not operations:
            raise ValueError("motion plan requires at least one operation")
        return MotionPlan(plan_id, operations, embodiment, source_skill)


class MotionExecutor:
    """The only Vocation adapter that can lower motion intent to RobotRuntime."""

    def __init__(self, runtime: RobotRuntime) -> None:
        self.runtime = runtime

    def execute_velocity(self, target: str, velocity: float, owner: str, authority_token: str, lease_token: str) -> dict[str, Any]:
        event = self.runtime.command(target, "velocity", velocity, owner, authority_token, lease_token)
        return event.to_dict()

    def validate(self, plan: MotionPlan, available_capabilities: Iterable[str]) -> list[str]:
        available = set(available_capabilities)
        missing = [operation.target for operation in plan.operations if operation.target and operation.target not in available]
        return [target for target in missing if target is not None]
