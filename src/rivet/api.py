from __future__ import annotations

import functools
import warnings
from dataclasses import dataclass
from typing import Any, Callable, TypeVar


class RivetWarning(DeprecationWarning):
    """Warning emitted for APIs scheduled for removal."""


@dataclass(frozen=True)
class ApiRecord:
    name: str
    visibility: str
    status: str = "stable"
    removal_target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "visibility": self.visibility, "status": self.status, "removal_target": self.removal_target}


API_REGISTRY = {
    "rivet.RobotRuntime": ApiRecord("rivet.RobotRuntime", "PUBLIC"),
    "rivet.Capability": ApiRecord("rivet.Capability", "PUBLIC"),
    "rivet.runtime.RobotRuntime._domain": ApiRecord("rivet.runtime.RobotRuntime._domain", "INTERNAL"),
    "rivet.capsule.Capsule": ApiRecord("rivet.capsule.Capsule", "EXPERIMENTAL", "beta"),
}

F = TypeVar("F", bound=Callable[..., Any])


def deprecated(message: str, removal_target: str) -> Callable[[F], F]:
    """Mark a compatibility API and make migration guidance visible at runtime."""

    def decorator(function: F) -> F:
        @functools.wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            warnings.warn(f"{function.__name__} is deprecated: {message}; removal target: {removal_target}", RivetWarning, stacklevel=2)
            return function(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    return decorator


def api_surface() -> list[dict[str, Any]]:
    return [record.to_dict() for record in sorted(API_REGISTRY.values(), key=lambda item: item.name)]
