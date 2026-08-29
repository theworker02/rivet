from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable

from .skills import SkillGraph


class QualificationState(str, Enum):
    CANDIDATE = "candidate"
    TRAINED = "trained"
    VALIDATED = "validated"
    AUTHORIZED = "authorized"


@dataclass(frozen=True)
class RoleSpec:
    role_id: str
    required_skills: dict[str, float] = field(default_factory=dict)
    optional_skills: dict[str, float] = field(default_factory=dict)
    required_hardware: tuple[str, ...] = ()
    permitted_actions: tuple[str, ...] = ()
    prohibited_actions: tuple[str, ...] = ()
    safety_policy: dict[str, Any] = field(default_factory=dict)
    mission_priorities: tuple[str, ...] = ()
    training_requirements: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["required_hardware"] = list(self.required_hardware)
        value["permitted_actions"] = list(self.permitted_actions)
        value["prohibited_actions"] = list(self.prohibited_actions)
        value["mission_priorities"] = list(self.mission_priorities)
        value["training_requirements"] = list(self.training_requirements)
        return value


@dataclass
class RoleAssessment:
    role_id: str
    score: float
    missing_skills: list[dict[str, Any]]
    missing_hardware: list[str]
    state: QualificationState = QualificationState.CANDIDATE

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        return value


class RoleCatalog:
    def __init__(self) -> None:
        self._roles: dict[str, RoleSpec] = {}

    def register(self, role: RoleSpec) -> None:
        if role.role_id in self._roles:
            raise ValueError(f"role already registered: {role.role_id}")
        self._roles[role.role_id] = role

    def get(self, role_id: str) -> RoleSpec:
        return self._roles[role_id]

    def list(self) -> list[RoleSpec]:
        return [self._roles[key] for key in sorted(self._roles)]


class RoleManager:
    """Evaluates and transitions roles without conflating competence with authority."""

    def __init__(self, catalog: RoleCatalog, skills: SkillGraph, hardware: Iterable[str], event_bus: Any | None = None) -> None:
        self.catalog = catalog
        self.skills = skills
        self.hardware = set(hardware)
        self.event_bus = event_bus
        self.assessments: dict[str, RoleAssessment] = {}
        self.active_role: str | None = None

    def evaluate(self, role_id: str) -> RoleAssessment:
        role = self.catalog.get(role_id)
        missing_skills: list[dict[str, Any]] = []
        ratios: list[float] = []
        for skill_id, required in role.required_skills.items():
            if skill_id not in self.skills.records:
                missing_skills.append({"skill": skill_id, "current": None, "required": required, "status": "unavailable"})
                ratios.append(0.0)
            else:
                current = self.skills.level(skill_id)
                ratios.append(min(1.0, current / required) if required else 1.0)
                if current < required:
                    missing_skills.append({"skill": skill_id, "current": current, "required": required})
        missing_hardware = sorted(set(role.required_hardware) - self.hardware)
        skill_score = sum(ratios) / len(ratios) if ratios else 1.0
        hardware_score = 1.0 - (len(missing_hardware) / len(role.required_hardware)) if role.required_hardware else 1.0
        score = round(0.75 * skill_score + 0.25 * hardware_score, 4)
        assessment = RoleAssessment(role_id, score, missing_skills, missing_hardware)
        previous = self.assessments.get(role_id)
        if previous:
            assessment.state = previous.state
        self.assessments[role_id] = assessment
        self._publish("role.evaluated", role_id, assessment.to_dict())
        return assessment

    def adopt(self, role_id: str) -> RoleAssessment:
        assessment = self.assessments.get(role_id) or self.evaluate(role_id)
        assessment.state = QualificationState.CANDIDATE
        self.active_role = role_id
        self._publish("role.adopted", role_id, assessment.to_dict())
        return assessment

    def train(self, role_id: str) -> RoleAssessment:
        assessment = self.assessments.get(role_id) or self.evaluate(role_id)
        if assessment.state not in (QualificationState.CANDIDATE, QualificationState.TRAINED):
            raise ValueError("training can only advance a candidate role")
        assessment.state = QualificationState.TRAINED
        self._publish("role.trained", role_id, assessment.to_dict())
        return assessment

    def validate(self, role_id: str) -> RoleAssessment:
        assessment = self.assessments.get(role_id) or self.evaluate(role_id)
        if assessment.missing_skills or assessment.missing_hardware:
            raise ValueError(f"role cannot be validated; missing skills or hardware: {role_id}")
        if assessment.state not in (QualificationState.TRAINED, QualificationState.VALIDATED):
            raise ValueError("role must be trained before validation")
        assessment.state = QualificationState.VALIDATED
        self._publish("role.validated", role_id, assessment.to_dict())
        return assessment

    def authorize(self, role_id: str, operator: str) -> RoleAssessment:
        assessment = self.assessments.get(role_id) or self.evaluate(role_id)
        if assessment.state != QualificationState.VALIDATED:
            raise ValueError("operator authorization requires validated role")
        assessment.state = QualificationState.AUTHORIZED
        self._publish("role.authorized", role_id, {**assessment.to_dict(), "operator": operator})
        return assessment

    def transition(self, role_id: str) -> RoleAssessment:
        assessment = self.assessments.get(role_id) or self.evaluate(role_id)
        if assessment.state != QualificationState.AUTHORIZED:
            raise ValueError("role transition requires an authorized role")
        self.active_role = role_id
        self._publish("role.transitioned", role_id, assessment.to_dict())
        return assessment

    def status(self) -> dict[str, Any]:
        return {"active_role": self.active_role, "roles": [assessment.to_dict() for assessment in self.assessments.values()]}

    def _publish(self, event_type: str, source: str, payload: dict[str, Any]) -> None:
        if self.event_bus is not None:
            self.event_bus.publish(event_type, source, payload)
