from __future__ import annotations

from typing import Any

from ..runtime import RobotRuntime


class LocalRobotClient:
    """Application facade over a local runtime; commands remain runtime-authorized."""

    def __init__(self, runtime: RobotRuntime) -> None:
        self.runtime = runtime

    def capabilities(self) -> list[dict[str, Any]]:
        return self.runtime.discover()

    def tree(self) -> dict[str, Any]:
        return self.runtime.registry.tree()

    def acquire_motion(self, owner: str, priority: int = 500, ttl_s: float = 5.0) -> dict[str, Any]:
        return self.runtime.acquire_control("motion", owner, priority, ttl_s).to_dict()
