from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .cluster import OfflineCluster
from .mission import MissionSpec


@dataclass(frozen=True)
class TeamMember:
    agent_id: str
    roles: tuple[str, ...]
    skills: dict[str, float]
    battery_percent: float = 100.0
    available: bool = True
    node_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["roles"] = list(self.roles)
        return value


@dataclass(frozen=True)
class TeamAssignment:
    mission_id: str
    agent_id: str
    score: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["reasons"] = list(self.reasons)
        return value


class TeamCoordinator:
    """Assigns work from demonstrated competence, availability, and power state."""

    def __init__(self, cluster: OfflineCluster | None = None) -> None:
        self.cluster = cluster
        self.assignments: list[TeamAssignment] = []

    def organize(self, mission: MissionSpec, members: Iterable[TeamMember]) -> TeamAssignment:
        members = list(members)
        candidates: list[TeamAssignment] = []
        for member in members:
            if not member.available or member.battery_percent < 20.0:
                continue
            skill_scores = [min(1.0, member.skills.get(skill, 0.0) / required) if required else 1.0 for skill, required in mission.required_skills.items()]
            score = sum(skill_scores) / len(skill_scores) if skill_scores else 1.0
            role_match = not mission.required_role or mission.required_role in member.roles
            if not role_match:
                score *= 0.5
            if member.battery_percent < 40.0:
                score *= 0.8
            reasons = (f"competence={score:.2f}", f"battery={member.battery_percent:.0f}%", "role-match" if role_match else "role-mismatch")
            candidates.append(TeamAssignment(mission.mission_id, member.agent_id, round(score, 4), reasons))
        if not candidates:
            raise ValueError("no available team member satisfies mission constraints")
        assignment = max(candidates, key=lambda item: item.score)
        self.assignments.append(assignment)
        if self.cluster:
            member = next(member for member in members if member.agent_id == assignment.agent_id)
            if member.node_id:
                self.cluster.assign(mission.mission_id, member.node_id)
        return assignment

    def status(self) -> list[dict[str, Any]]:
        return [assignment.to_dict() for assignment in self.assignments]
