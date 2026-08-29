from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Capability:
    """The stable contract an application sees for a robot component."""

    path: str
    type: str
    version: int = 1
    commands: dict[str, dict[str, Any]] = field(default_factory=dict)
    telemetry: dict[str, dict[str, Any]] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Event:
    """A timestamped message on the local Rivet Bus."""

    type: str
    source: str
    payload: dict[str, Any]
    timestamp_ns: int
    sequence: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthorityGrant:
    domain: str
    owner: str
    priority: int
    token: str
    expires_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Lease:
    target: str
    owner: str
    token: str
    expires_at: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
