from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .skills import BenchmarkResult, SkillGraph


@dataclass(frozen=True)
class BenchmarkSpec:
    benchmark_id: str
    skill_id: str
    description: str
    passing_score: float = 0.75


class RivetBench:
    """Small benchmark catalog that feeds auditable evidence into SkillGraph."""

    def __init__(self, skills: SkillGraph) -> None:
        self.skills = skills
        self.specs: dict[str, BenchmarkSpec] = {}

    def register(self, spec: BenchmarkSpec) -> None:
        self.specs[spec.benchmark_id] = spec

    def run(self, benchmark_id: str, score: float, evidence: dict[str, Any] | None = None) -> BenchmarkResult:
        spec = self.specs[benchmark_id]
        return self.skills.benchmark(spec.benchmark_id, spec.skill_id, score, score >= spec.passing_score, evidence)

    def status(self) -> list[dict[str, Any]]:
        return [{"benchmark_id": spec.benchmark_id, "skill_id": spec.skill_id, "description": spec.description, "passing_score": spec.passing_score} for spec in self.specs.values()]
