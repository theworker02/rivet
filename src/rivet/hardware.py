from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import Capability
from .runtime import RobotRuntime


@dataclass
class HardwareNode:
    node_id: str
    kind: str
    health: str = "healthy"
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HardwareGraph:
    """Live topology and health view for buses, devices, and affected capabilities."""

    def __init__(self) -> None:
        self.nodes: dict[str, HardwareNode] = {}
        self.links: dict[str, set[str]] = {}
        self.capabilities: dict[str, set[str]] = {}

    def add_node(self, node_id: str, kind: str, details: dict[str, Any] | None = None) -> None:
        self.nodes[node_id] = HardwareNode(node_id, kind, "healthy", details or {})

    def link(self, parent: str, child: str) -> None:
        self.links.setdefault(parent, set()).add(child)

    def attach_capability(self, node_id: str, capability: str) -> None:
        self.capabilities.setdefault(node_id, set()).add(capability)

    def set_health(self, node_id: str, health: str) -> list[str]:
        if node_id not in self.nodes:
            raise KeyError(node_id)
        self.nodes[node_id].health = health
        affected = sorted(self.capabilities.get(node_id, set()))
        return affected

    def affected(self, node_id: str) -> list[str]:
        return sorted(self.capabilities.get(node_id, set()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": {key: value.to_dict() for key, value in sorted(self.nodes.items())},
            "links": {key: sorted(value) for key, value in sorted(self.links.items())},
            "capabilities": {key: sorted(value) for key, value in sorted(self.capabilities.items())},
        }


@dataclass
class Provider:
    name: str
    capability: Capability
    device: Any
    priority: int
    node_id: str
    healthy: bool = True


class FailoverManager:
    """Promotes a healthy provider when the current hardware path is lost."""

    def __init__(self, runtime: RobotRuntime, graph: HardwareGraph) -> None:
        self.runtime = runtime
        self.graph = graph
        self.providers: dict[str, list[Provider]] = {}
        self.active: dict[str, str] = {}

    def add_provider(self, capability: Capability, name: str, device: Any, priority: int, node_id: str) -> None:
        provider = Provider(name, capability, device, priority, node_id)
        self.providers.setdefault(capability.path, []).append(provider)
        self.providers[capability.path].sort(key=lambda item: item.priority, reverse=True)
        if node_id not in self.graph.nodes:
            self.graph.add_node(node_id, "device")
        self.graph.attach_capability(node_id, capability.path)
        if capability.path not in self.active:
            self.active[capability.path] = name
            self.runtime.register(capability, device)

    def mark_failed(self, capability_path: str, provider_name: str, reason: str = "device-lost") -> str | None:
        providers = self.providers[capability_path]
        failed = next(provider for provider in providers if provider.name == provider_name)
        failed.healthy = False
        self.graph.set_health(failed.node_id, "lost")
        candidates = [provider for provider in providers if provider.healthy]
        if not candidates:
            self.active.pop(capability_path, None)
            self.runtime.bus.publish("device.lost", capability_path, {"provider": provider_name, "reason": reason, "affected": [capability_path]})
            return None
        promoted = max(candidates, key=lambda item: item.priority)
        self.active[capability_path] = promoted.name
        self.runtime.devices[capability_path] = promoted.device
        self.runtime.registry.register(promoted.capability)
        self.runtime.bus.publish("device.failover", capability_path, {"lost": provider_name, "promoted": promoted.name, "reason": reason})
        return promoted.name

    def status(self) -> list[dict[str, Any]]:
        return [
            {"capability": path, "active": self.active.get(path), "providers": [asdict(provider) | {"capability": provider.capability.path, "device": type(provider.device).__name__} for provider in providers]}
            for path, providers in sorted(self.providers.items())
        ]
