from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .skills import SkillGraph
from .vocation import QualificationState, RoleManager


@dataclass(frozen=True)
class MissionSpec:
    mission_id: str
    goal: str
    required_role: str | None = None
    required_skills: dict[str, float] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    success: dict[str, Any] = field(default_factory=dict)
    timeout_s: float = 600.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MissionStep:
    step_id: str
    action: str
    rationale: str
    required_skill: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MissionPlan:
    mission: MissionSpec
    steps: tuple[MissionStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"mission": self.mission.to_dict(), "steps": [step.to_dict() for step in self.steps]}


class MissionPlanner:
    def decompose(self, mission: MissionSpec) -> MissionPlan:
        goal = mission.goal.lower()
        actions: list[tuple[str, str, str | None]]
        if "inspect" in goal:
            actions = [("locate-zone", "Find the requested inspection zone", "navigation.indoor"), ("scan", "Collect structural observations", "inspection.structural"), ("verify-coverage", "Confirm the requested coverage threshold", "inspection.structural")]
        elif "transport" in goal or "move" in goal:
            actions = [("locate-payload", "Locate and evaluate the payload", "navigation.indoor"), ("acquire-payload", "Acquire the payload safely", "manipulation.general"), ("transport", "Move the payload to its destination", "payload.transport"), ("verify-placement", "Verify final placement", "payload.transport")]
        elif "search" in goal:
            actions = [("map-area", "Build a local search route", "mapping.local"), ("search", "Inspect the search area", "search.thermal"), ("report", "Record findings with provenance", "inspection.structural")]
        else:
            actions = [("prepare", "Check mission prerequisites", None), ("execute", mission.goal, None), ("verify", "Evaluate mission success criteria", None)]
        steps = tuple(MissionStep(f"{mission.mission_id}-{index}", action, rationale, skill) for index, (action, rationale, skill) in enumerate(actions, 1))
        return MissionPlan(mission, steps)


class MissionAdmission:
    def __init__(self, skills: SkillGraph, roles: RoleManager) -> None:
        self.skills = skills
        self.roles = roles

    def check(self, mission: MissionSpec) -> dict[str, Any]:
        missing: list[dict[str, Any]] = []
        for skill_id, required in mission.required_skills.items():
            if skill_id not in self.skills.records:
                missing.append({"skill": skill_id, "current": None, "required": required})
            elif self.skills.level(skill_id) < required:
                missing.append({"skill": skill_id, "current": self.skills.level(skill_id), "required": required})
        role_ok = True
        role_state = None
        if mission.required_role:
            assessment = self.roles.assessments.get(mission.required_role)
            role_state = assessment.state.value if assessment else None
            role_ok = assessment is not None and assessment.state == QualificationState.AUTHORIZED
        return {"admitted": not missing and role_ok, "missing_skills": missing, "required_role": mission.required_role, "role_state": role_state}


class MissionExplainer:
    def explain(self, mission: MissionSpec, admission: dict[str, Any], plan: MissionPlan) -> dict[str, Any]:
        return {"mission": mission.mission_id, "goal": mission.goal, "admitted": admission["admitted"], "reasons": {"required_role": admission["required_role"], "role_state": admission["role_state"], "missing_skills": admission["missing_skills"]}, "steps": [step.to_dict() for step in plan.steps]}
