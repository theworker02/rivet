from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Callable


@dataclass
class ClusterNode:
    node_id: str
    role: str
    address: str
    last_heartbeat: float
    health: str = "healthy"
    workloads: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OfflineCluster:
    """Local-first node registry; networking can later replace the heartbeat source."""

    def __init__(self, clock: Callable[[], float] | None = None, timeout_s: float = 3.0) -> None:
        self._clock = clock or time.monotonic
        self.timeout_s = timeout_s
        self.nodes: dict[str, ClusterNode] = {}
        self.assignments: dict[str, str] = {}

    def join(self, node_id: str, role: str, address: str) -> ClusterNode:
        node = ClusterNode(node_id, role, address, self._clock(), "healthy", [])
        self.nodes[node_id] = node
        return node

    def heartbeat(self, node_id: str) -> None:
        node = self.nodes[node_id]
        node.last_heartbeat = self._clock()
        node.health = "healthy"

    def expire(self, now: float | None = None) -> list[str]:
        current = self._clock() if now is None else now
        lost: list[str] = []
        for node in self.nodes.values():
            if current - node.last_heartbeat > self.timeout_s:
                node.health = "lost"
                lost.append(node.node_id)
        return lost

    def assign(self, workload: str, node_id: str) -> None:
        if node_id not in self.nodes or self.nodes[node_id].health != "healthy":
            raise ValueError(f"cluster node is unavailable: {node_id}")
        previous = self.assignments.get(workload)
        if previous:
            previous_workloads = self.nodes[previous].workloads
            if previous_workloads is not None and workload in previous_workloads:
                previous_workloads.remove(workload)
        self.assignments[workload] = node_id
        target_workloads = self.nodes[node_id].workloads
        if target_workloads is None:
            target_workloads = []
            self.nodes[node_id].workloads = target_workloads
        if workload not in target_workloads:
            target_workloads.append(workload)

    def migrate(self, workload: str, target_node: str) -> None:
        self.assign(workload, target_node)

    def status(self) -> list[dict[str, Any]]:
        self.expire()
        return [node.to_dict() for node in sorted(self.nodes.values(), key=lambda item: item.node_id)]
