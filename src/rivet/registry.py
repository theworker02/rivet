from __future__ import annotations

from .errors import NotFoundError
from .models import Capability


class CapabilityRegistry:
    """In-memory device tree and capability discovery registry."""

    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        if not capability.path or "." not in capability.path:
            raise ValueError("capability paths must look like 'domain.name'")
        self._capabilities[capability.path] = capability

    def get(self, path: str) -> Capability:
        try:
            return self._capabilities[path]
        except KeyError as exc:
            raise NotFoundError(f"capability not found: {path}") from exc

    def list(self) -> list[Capability]:
        return [self._capabilities[path] for path in sorted(self._capabilities)]

    def as_dict(self) -> dict[str, dict]:
        return {cap.path: cap.to_dict() for cap in self.list()}

    def tree(self) -> dict:
        root: dict = {}
        for capability in self.list():
            node = root
            parts = capability.path.split(".")
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = capability.to_dict()
        return root
