from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rivet.models import Capability


@dataclass
class MockCamera:
    path: str = "vision.front-camera"
    frames: int = 0

    @property
    def capability(self) -> Capability:
        return Capability(self.path, "camera.rgb", telemetry={"frames": {"type": "integer"}}, metadata={"simulated": True})

    def capture(self) -> dict[str, Any]:
        self.frames += 1
        return {"frame": self.frames, "format": "metadata-only"}

    def safe(self) -> dict[str, Any]:
        return {"streaming": False}
