from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rivet.models import Capability


@dataclass
class MockSensor:
    path: str
    sensor_type: str = "sensor.mock"
    value: float = 0.0

    @property
    def capability(self) -> Capability:
        return Capability(self.path, self.sensor_type, telemetry={"value": {"type": "float"}}, metadata={"simulated": True})

    def read(self) -> dict[str, Any]:
        return {"value": self.value}

    def safe(self) -> dict[str, Any]:
        return self.read()
