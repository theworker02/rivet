from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import Event


@dataclass(frozen=True)
class ReflexRule:
    """A deterministic local condition/action pair below mission planning."""

    name: str
    event_type: str
    field: str
    operator: str
    threshold: Any
    action: str
    priority: str = "normal"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReflexAction:
    rule: str
    action: str
    event_sequence: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReflexEngine:
    """Evaluates small protective rules synchronously as events arrive."""

    _PRIORITY = {"normal": 0, "high": 1, "emergency": 2}

    def __init__(self, bus: Any, runtime: Any) -> None:
        self.bus = bus
        self.runtime = runtime
        self.rules: list[ReflexRule] = []
        self.last_action: ReflexAction | None = None
        bus.subscribe("*", self._on_event)

    def add(self, rule: ReflexRule) -> None:
        if rule.operator not in {"lt", "lte", "gt", "gte", "eq"}:
            raise ValueError(f"unsupported reflex operator: {rule.operator}")
        if rule.priority not in self._PRIORITY:
            raise ValueError(f"unsupported reflex priority: {rule.priority}")
        self.rules.append(rule)
        self.rules.sort(key=lambda item: self._PRIORITY[item.priority], reverse=True)

    def remove(self, name: str) -> None:
        self.rules = [rule for rule in self.rules if rule.name != name]

    def evaluate(self, event: Event) -> list[ReflexAction]:
        actions: list[ReflexAction] = []
        for rule in self.rules:
            if rule.event_type != event.type or not self._matches(event.payload.get(rule.field), rule.operator, rule.threshold):
                continue
            action = ReflexAction(rule.name, rule.action, event.sequence)
            self._execute(action)
            actions.append(action)
        return actions

    def _on_event(self, event: Event) -> None:
        self.evaluate(event)

    def _execute(self, action: ReflexAction) -> None:
        if action.action == "motion.stop":
            for device in self.runtime.devices.values():
                if hasattr(device, "safe"):
                    device.safe()
            self.runtime.leases.revoke_all()
            self.runtime.authority.revoke_all()
        elif action.action == "mission.abort":
            self.bus.publish("mission.aborted", "reflex", {"rule": action.rule})
        elif action.action != "notify":
            raise ValueError(f"unsupported reflex action: {action.action}")
        self.last_action = action
        self.bus.publish("reflex.action", "reflex", action.to_dict())

    @staticmethod
    def _matches(value: Any, operator: str, threshold: Any) -> bool:
        if value is None:
            return False
        return {
            "lt": value < threshold,
            "lte": value <= threshold,
            "gt": value > threshold,
            "gte": value >= threshold,
            "eq": value == threshold,
        }[operator]
