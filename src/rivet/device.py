from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from .contracts import validate_contract
from .models import Capability


@runtime_checkable
class Device(Protocol):
    """Minimum command/safe contract accepted by RobotRuntime."""

    @property
    def capability(self) -> Capability: ...

    def command(self, method: str, value: Any) -> dict[str, Any]: ...

    def safe(self) -> dict[str, Any]: ...


def validate_capability(capability: Capability) -> None:
    """Validate the stable parts of a capability before driver registration."""
    if not capability.path or "." not in capability.path:
        raise ValueError("capability path must contain a domain and name")
    if not capability.type or capability.version < 1:
        raise ValueError("capability type and positive version are required")
    for command, contract in capability.commands.items():
        if not isinstance(command, str) or not isinstance(contract, dict):
            raise ValueError("capability commands must map names to contracts")
    validate_contract(capability)
