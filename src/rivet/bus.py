from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from .models import Event

EventHandler = Callable[[Event], None]


class EventBus:
    """Small synchronous bus; transports can replace this boundary later."""

    def __init__(self, clock_ns: Callable[[], int] | None = None) -> None:
        import time

        self._clock_ns = clock_ns or time.monotonic_ns
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._sequence = 0

    def subscribe(self, event_type: str | None, handler: EventHandler) -> None:
        self._handlers[event_type or "*"].append(handler)

    def publish(self, event_type: str, source: str, payload: dict[str, Any]) -> Event:
        self._sequence += 1
        event = Event(event_type, source, payload, self._clock_ns(), self._sequence)
        for handler in [*self._handlers.get(event_type, []), *self._handlers.get("*", [])]:
            handler(event)
        return event
