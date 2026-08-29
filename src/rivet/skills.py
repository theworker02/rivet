from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass
class SkillRecord:
    skill_id: str
    level: float = 0.0
    attempts: int = 0
    successes: int = 0
    simulator_runs: int = 0
    last_validated: str | None = None
    dependencies: tuple[str, ...] = ()
    history: list[dict[str, Any]] = field(default_factory=list)

    @property
    def failures(self) -> int:
        return self.attempts - self.successes

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["failures"] = self.failures
        value["dependencies"] = list(self.dependencies)
        return value


@dataclass(frozen=True)
class TrainingPlan:
    skill_id: str
    curriculum: tuple[str, ...]
    prerequisites: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"skill_id": self.skill_id, "curriculum": list(self.curriculum), "prerequisites": list(self.prerequisites)}


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_id: str
    skill_id: str
    score: float
    passed: bool
    evidence: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SkillGraph:
    """Evidence-backed, dependency-aware competency graph."""

    def __init__(self) -> None:
        self.records: dict[str, SkillRecord] = {}
        self.benchmarks: list[BenchmarkResult] = []

    def register(self, skill_id: str, dependencies: tuple[str, ...] = (), initial_level: float = 0.0) -> SkillRecord:
        if not 0.0 <= initial_level <= 1.0:
            raise ValueError("skill level must be between 0 and 1")
        record = self.records.get(skill_id)
        if record is None:
            record = SkillRecord(skill_id, initial_level, dependencies=dependencies)
            self.records[skill_id] = record
        else:
            record.dependencies = dependencies or record.dependencies
        return record

    def get(self, skill_id: str) -> SkillRecord:
        if skill_id not in self.records:
            raise KeyError(f"skill is not registered: {skill_id}")
        return self.records[skill_id]

    def level(self, skill_id: str) -> float:
        return self.get(skill_id).level

    def missing(self, skill_id: str, required_level: float = 0.0) -> list[dict[str, Any]]:
        record = self.get(skill_id)
        missing: list[dict[str, Any]] = []
        if record.level < required_level:
            missing.append({"skill": skill_id, "current": round(record.level, 4), "required": required_level})
        for dependency in record.dependencies:
            if dependency not in self.records:
                missing.append({"skill": dependency, "current": None, "required": 0.0, "status": "unavailable"})
            elif self.records[dependency].level < required_level:
                missing.extend(self.missing(dependency, required_level))
        return missing

    def explain(self, skill_id: str, required_level: float = 0.0) -> dict[str, Any]:
        record = self.get(skill_id)
        return {"skill": record.to_dict(), "required_level": required_level, "missing_prerequisites": self.missing(skill_id, required_level)}

    def curriculum(self, skill_id: str) -> TrainingPlan:
        record = self.get(skill_id)
        levels = ("stationary target", "irregular target", "variable orientation", "fragile target", "moving target", "occluded target")
        start = min(5, int(record.level * len(levels)))
        return TrainingPlan(skill_id, levels[start:], record.dependencies)

    def record_result(self, skill_id: str, success: bool, simulator: bool = False, evidence: dict[str, Any] | None = None) -> SkillRecord:
        record = self.get(skill_id)
        record.attempts += 1
        record.successes += int(success)
        record.simulator_runs += int(simulator)
        success_rate = record.successes / record.attempts
        experience = min(1.0, record.attempts / 100.0)
        record.level = round(success_rate * (0.5 + 0.5 * experience), 4)
        record.last_validated = date.today().isoformat()
        record.history.append({"success": success, "simulator": simulator, "evidence": evidence or {}, "timestamp": record.last_validated, "level": record.level})
        return record

    def decay(self, skill_ids: list[str], factor: float = 0.8, reason: str = "hardware-change") -> list[SkillRecord]:
        if not 0.0 < factor <= 1.0:
            raise ValueError("decay factor must be greater than 0 and at most 1")
        changed: list[SkillRecord] = []
        for skill_id in skill_ids:
            record = self.get(skill_id)
            record.level = round(record.level * factor, 4)
            record.history.append({"event": "confidence-decay", "factor": factor, "reason": reason, "timestamp": date.today().isoformat(), "level": record.level})
            changed.append(record)
        return changed

    def benchmark(self, benchmark_id: str, skill_id: str, score: float, passed: bool, evidence: dict[str, Any] | None = None) -> BenchmarkResult:
        if not 0.0 <= score <= 1.0:
            raise ValueError("benchmark score must be between 0 and 1")
        result = BenchmarkResult(benchmark_id, skill_id, score, passed, evidence or {}, date.today().isoformat())
        self.benchmarks.append(result)
        record = self.get(skill_id)
        if passed and score > record.level:
            record.level = score
            record.last_validated = result.timestamp
        record.history.append({"event": "benchmark", **result.to_dict()})
        return result

    def status(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in sorted(self.records.values(), key=lambda item: item.skill_id)]
