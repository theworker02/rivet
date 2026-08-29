from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rivet.models import Capability


@dataclass
class GenericPwmMotor:
    path: str
    max_rpm: float = 180.0
    velocity: float = 0.0

    @property
    def capability(self) -> Capability:
        return Capability(self.path, "motion.dc-motor", commands={"velocity": {"input": "float", "range": [-1.0, 1.0]}}, telemetry={"rpm": {"type": "float"}}, safety={"timeout_ms": 250, "fail_state": "brake"}, metadata={"driver": "generic-pwm"})

    def command(self, method: str, value: Any) -> dict[str, Any]:
        if method != "velocity":
            raise ValueError(f"unsupported motor command: {method}")
        self.velocity = float(value)
        if not -1.0 <= self.velocity <= 1.0:
            raise ValueError("velocity must be between -1 and 1")
        return {"velocity": self.velocity, "rpm": round(self.velocity * self.max_rpm, 2)}

    def safe(self) -> dict[str, Any]:
        self.velocity = 0.0
        return {"velocity": 0.0, "rpm": 0.0}
