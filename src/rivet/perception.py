from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class ClockStamp:
    host_timestamp_ns: int
    sensor_timestamp_ns: int | None
    synchronization_offset_ns: int | None
    sequence: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RivetClock:
    """Provides one monotonic robot timeline and preserves sensor timing evidence."""

    def __init__(self, clock_ns: Any | None = None) -> None:
        self._clock_ns = clock_ns or time.monotonic_ns
        self._sequence = 0

    def stamp(self, sensor_timestamp_ns: int | None = None) -> ClockStamp:
        self._sequence += 1
        host = self._clock_ns()
        offset = host - sensor_timestamp_ns if sensor_timestamp_ns is not None else None
        return ClockStamp(host, sensor_timestamp_ns, offset, self._sequence)


class SharedBuffer:
    """Reference-counted view over caller-owned bytes; no copy is made on retain."""

    def __init__(self, data: bytes | bytearray | memoryview, metadata: dict[str, Any] | None = None) -> None:
        self._view = memoryview(data)
        self.metadata = metadata or {}
        self._refcount = 1

    @property
    def view(self) -> memoryview:
        if self._refcount <= 0:
            raise RuntimeError("shared buffer has been released")
        return self._view

    @property
    def refcount(self) -> int:
        return self._refcount

    def retain(self) -> "SharedBuffer":
        if self._refcount <= 0:
            raise RuntimeError("cannot retain released buffer")
        self._refcount += 1
        return self

    def release(self) -> None:
        if self._refcount <= 0:
            raise RuntimeError("shared buffer released too many times")
        self._refcount -= 1

    def __enter__(self) -> "SharedBuffer":
        return self

    def __exit__(self, *_: Any) -> None:
        self.release()


class SharedFrame(SharedBuffer):
    pass


class SharedTensor(SharedBuffer):
    pass


class SharedPointCloud(SharedBuffer):
    pass


@dataclass(frozen=True)
class Observation:
    kind: str
    confidence: float
    sources: tuple[str, ...]
    clock: ClockStamp
    location: tuple[float, ...] | None = None
    evidence: dict[str, float] = field(default_factory=dict)
    observation_id: str = field(default_factory=lambda: "obs-" + uuid.uuid4().hex[:12])
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["clock"] = self.clock.to_dict()
        value["sources"] = list(self.sources)
        return value


class ObservationStore:
    def __init__(self) -> None:
        self._observations: dict[str, Observation] = {}

    def add(self, observation: Observation) -> Observation:
        self._observations[observation.observation_id] = observation
        return observation

    def get(self, observation_id: str) -> Observation:
        return self._observations[observation_id]

    def explain(self, observation_id: str) -> dict[str, Any]:
        observation = self.get(observation_id)
        return {
            "observation_id": observation.observation_id,
            "classification": observation.kind,
            "confidence": observation.confidence,
            "evidence": observation.evidence,
            "sources": list(observation.sources),
            "clock": observation.clock.to_dict(),
            "inference": "sensor fusion" if len(observation.sources) > 1 else "direct observation",
        }

    def all(self) -> list[Observation]:
        return list(self._observations.values())


class InsightEngine:
    def __init__(self, clock: RivetClock | None = None, store: ObservationStore | None = None) -> None:
        self.clock = clock or RivetClock()
        self.store = store or ObservationStore()

    def fuse(self, kind: str, location: Iterable[float], evidence: dict[str, float], metadata: dict[str, Any] | None = None) -> Observation:
        if not evidence:
            raise ValueError("sensor fusion requires evidence")
        confidence = round(sum(evidence.values()) / len(evidence), 4)
        observation = Observation(kind, confidence, tuple(evidence), self.clock.stamp(), tuple(location), dict(evidence), metadata=metadata or {})
        return self.store.add(observation)


class RadiographyGate:
    """Interlock and operator authorization gate; it never controls radiation hardware."""

    def __init__(self) -> None:
        self.active = False

    def activate(self, interlock_ok: bool, operator_authorized: bool) -> None:
        if not interlock_ok:
            raise PermissionError("radiography hardware interlock is not active")
        if not operator_authorized:
            raise PermissionError("radiography operator authorization is required")
        self.active = True

    def deactivate(self) -> None:
        self.active = False


@dataclass
class WorldObject:
    object_id: str
    kind: str
    position: tuple[float, ...]
    confidence: float
    sensors: tuple[str, ...]
    last_seen_ns: int
    velocity: tuple[float, ...] | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["sensors"] = list(self.sensors)
        return value


class WorldModel:
    """Small local scene graph keyed by stable object identifiers."""

    def __init__(self) -> None:
        self._objects: dict[str, WorldObject] = {}

    def upsert(self, obj: WorldObject) -> WorldObject:
        self._objects[obj.object_id] = obj
        return obj

    def get(self, object_id: str) -> WorldObject:
        return self._objects[object_id]

    def objects(self) -> list[WorldObject]:
        return sorted(self._objects.values(), key=lambda item: item.object_id)

    def as_dict(self) -> list[dict[str, Any]]:
        return [obj.to_dict() for obj in self.objects()]
