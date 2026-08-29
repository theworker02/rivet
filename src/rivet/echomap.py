from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .perception import ClockStamp


@dataclass(frozen=True)
class EchoMark:
    location: tuple[float, ...]
    observation: str
    confidence: float
    sensor_sources: tuple[str, ...]
    clock: ClockStamp
    environment: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)
    note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["clock"] = self.clock.to_dict()
        value["sensor_sources"] = list(self.sensor_sources)
        return value


class EchoMap:
    """Temporal experience field that keeps physical-location evidence explainable."""

    def __init__(self) -> None:
        self.marks: list[EchoMark] = []

    def record(self, mark: EchoMark) -> EchoMark:
        if not 0.0 <= mark.confidence <= 1.0:
            raise ValueError("EchoMap confidence must be between 0 and 1")
        self.marks.append(mark)
        return mark

    def query(self, location: Iterable[float], radius: float = 0.5) -> list[EchoMark]:
        point = tuple(location)
        return [mark for mark in self.marks if len(mark.location) == len(point) and sum((a - b) ** 2 for a, b in zip(mark.location, point)) ** 0.5 <= radius]

    def explain(self, location: Iterable[float], radius: float = 0.5) -> list[dict[str, Any]]:
        return [mark.to_dict() for mark in self.query(location, radius)]

    def status(self) -> dict[str, Any]:
        return {"marks": len(self.marks), "observations": sorted({mark.observation for mark in self.marks})}
