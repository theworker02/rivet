from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, TextIO

from .models import Event

RECORDING_FORMAT = "RVT/1"


@dataclass(frozen=True)
class TimelineEntry:
    sequence: int
    timestamp_ns: int
    event_type: str
    source: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "timestamp_ns": self.timestamp_ns,
            "event": self.event_type,
            "source": self.source,
            "payload": self.payload,
        }

    def line(self) -> str:
        seconds = self.timestamp_ns / 1_000_000_000
        return f"{seconds:012.3f}  {self.event_type:<24} {self.source}"


class Recorder:
    """Append-only, versioned JSONL flight recorder for compact runtime evidence."""

    def __init__(self, path: str | Path, metadata: dict[str, Any] | None = None, max_events: int | None = None) -> None:
        self.path = Path(path)
        self.metadata = dict(metadata or {})
        self.max_events = max_events
        self._handle: TextIO | None = None
        self._events = 0

    def attach(self, bus: Any) -> None:
        if self._handle is not None:
            raise RuntimeError("recorder is already attached")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        bus.subscribe(None, self._record)
        self._handle = self.path.open("a", encoding="utf-8")
        self._write_metadata(bus)

    def _write_metadata(self, bus: Any) -> None:
        if self._events:
            return
        event = {
            "format": RECORDING_FORMAT,
            "type": "recording.started",
            "source": "recorder",
            "payload": self.metadata,
            "timestamp_ns": 0,
            "sequence": 0,
        }
        self._handle_write(event)

    def _record(self, event: Event) -> None:
        if self._handle is None:
            return
        if self.max_events is not None and self._events >= self.max_events:
            return
        self._handle_write(event.to_dict())

    def _handle_write(self, value: dict[str, Any]) -> None:
        if self._handle is None:
            return
        value = {"format": RECORDING_FORMAT, **value}
        self._handle.write(json.dumps(value, sort_keys=True) + "\n")
        self._handle.flush()
        self._events += 1

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def __enter__(self) -> "Recorder":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class ReplaySession:
    """Deterministically iterates recorded events and can publish them to an event bus."""

    def __init__(self, events: Iterable[dict[str, Any]]) -> None:
        self.events = tuple(event for event in events if event.get("type") != "recording.started")
        self._validate_order()

    @classmethod
    def load(cls, path: str | Path) -> "ReplaySession":
        return cls(load_events(path))

    def replay(self, bus: Any | None = None, handler: Callable[[dict[str, Any]], None] | None = None) -> int:
        for event in self.events:
            if handler is not None:
                handler(event)
            if bus is not None:
                bus.publish(event["type"], event["source"], dict(event["payload"]))
        return len(self.events)

    def timeline(self) -> list[TimelineEntry]:
        return [TimelineEntry(event["sequence"], event["timestamp_ns"], event["type"], event["source"], event["payload"]) for event in self.events]

    def _validate_order(self) -> None:
        sequences = [event["sequence"] for event in self.events]
        if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
            raise ValueError("recording event sequence is not deterministic")


def _validate_event(value: dict[str, Any], line_number: int) -> None:
    required = ("type", "source", "payload", "timestamp_ns", "sequence")
    missing = [key for key in required if key not in value]
    if missing:
        raise ValueError(f"recording line {line_number} is missing: {', '.join(missing)}")
    if not isinstance(value["type"], str) or not isinstance(value["source"], str) or not isinstance(value["payload"], dict):
        raise ValueError(f"recording line {line_number} has invalid event fields")
    if not isinstance(value["sequence"], int) or not isinstance(value["timestamp_ns"], int):
        raise ValueError(f"recording line {line_number} has invalid event timing")


def load_events(path: str | Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"recording line {line_number} must be an object")
            _validate_event(value, line_number)
            if value.get("format", RECORDING_FORMAT) != RECORDING_FORMAT:
                raise ValueError(f"unsupported recording format on line {line_number}")
            events.append(value)
    return events


def summarize(path: str | Path) -> dict[str, Any]:
    events = load_events(path)
    by_type: dict[str, int] = {}
    for event in events:
        by_type[event["type"]] = by_type.get(event["type"], 0) + 1
    sequences = [event["sequence"] for event in events]
    return {
        "format": RECORDING_FORMAT,
        "events": len(events),
        "by_type": dict(sorted(by_type.items())),
        "first_sequence": min(sequences) if sequences else None,
        "last_sequence": max(sequences) if sequences else None,
        "path": str(path),
    }


def timeline(path: str | Path) -> list[dict[str, Any]]:
    return [entry.to_dict() for entry in ReplaySession.load(path).timeline()]
