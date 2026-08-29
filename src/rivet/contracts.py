from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .models import Capability


@dataclass(frozen=True)
class FieldContract:
    name: str
    type: str
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    required: bool = True

    @classmethod
    def from_dict(cls, name: str, value: dict[str, Any]) -> "FieldContract":
        bounds = value.get("range", [None, None])
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError(f"field range must contain two values: {name}")
        return cls(name, str(value.get("type", value.get("input", "object"))), value.get("unit"), bounds[0], bounds[1], bool(value.get("required", True)))

    def validate(self, value: Any) -> None:
        if value is None:
            if self.required:
                raise ValueError(f"contract field is required: {self.name}")
            return
        if self.type in {"float", "number"} and not isinstance(value, (int, float)):
            raise TypeError(f"{self.name} requires a numeric value")
        if self.type == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
            raise TypeError(f"{self.name} requires an integer")
        if self.type == "string" and not isinstance(value, str):
            raise TypeError(f"{self.name} requires a string")
        if self.minimum is not None and value < self.minimum:
            raise ValueError(f"{self.name} is below the minimum {self.minimum}")
        if self.maximum is not None and value > self.maximum:
            raise ValueError(f"{self.name} is above the maximum {self.maximum}")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["range"] = [self.minimum, self.maximum]
        del value["minimum"]
        del value["maximum"]
        return value


@dataclass(frozen=True)
class CapabilityContract:
    capability: str
    version: int
    inputs: dict[str, FieldContract] = field(default_factory=dict)
    telemetry: dict[str, FieldContract] = field(default_factory=dict)
    requires: tuple[str, ...] = ()
    minimum_health: float = 0.0
    watchdog_ms: int | None = None
    failure_action: str | None = None

    @classmethod
    def from_capability(cls, capability: Capability) -> "CapabilityContract":
        inputs = {name: FieldContract.from_dict(name, descriptor) for name, descriptor in capability.commands.items()}
        telemetry = {name: FieldContract.from_dict(name, descriptor) for name, descriptor in capability.telemetry.items()}
        health = capability.metadata.get("health", {})
        return cls(
            capability.path,
            capability.version,
            inputs,
            telemetry,
            tuple(capability.metadata.get("requires", ())),
            float(health.get("minimum", 0.0)),
            capability.safety.get("watchdog_ms", capability.safety.get("timeout_ms")),
            capability.safety.get("failure_action", capability.safety.get("fail_state")),
        )

    def validate_command(self, method: str, value: Any) -> None:
        if method not in self.inputs:
            raise ValueError(f"unsupported command for {self.capability}: {method}")
        self.inputs[method].validate(value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "version": self.version,
            "inputs": {name: field.to_dict() for name, field in self.inputs.items()},
            "telemetry": {name: field.to_dict() for name, field in self.telemetry.items()},
            "requires": list(self.requires),
            "health": {"minimum": self.minimum_health},
            "safety": {"watchdog_ms": self.watchdog_ms, "failure_action": self.failure_action},
        }


def validate_contract(capability: Capability) -> CapabilityContract:
    contract = CapabilityContract.from_capability(capability)
    if contract.minimum_health < 0.0 or contract.minimum_health > 1.0:
        raise ValueError(f"capability health minimum must be between 0 and 1: {capability.path}")
    if contract.watchdog_ms is not None and int(contract.watchdog_ms) <= 0:
        raise ValueError(f"capability watchdog must be positive: {capability.path}")
    for contract_field in (*contract.inputs.values(), *contract.telemetry.values()):
        if contract_field.minimum is not None and contract_field.maximum is not None and contract_field.minimum > contract_field.maximum:
            raise ValueError(f"invalid range for {capability.path}.{contract_field.name}")
    return contract
