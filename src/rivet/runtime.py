from __future__ import annotations

import time
from typing import Any, Callable

from .bus import EventBus
from .contracts import validate_contract
from .driver import DriverRegistry
from .errors import CommandError
from .health import HealthManager
from .models import AuthorityGrant, Capability, Event, Lease
from .registry import CapabilityRegistry
from .safety import AuthorityManager, LeaseManager


class RobotRuntime:
    """The local robot host: registry, bus, safety, and device command boundary."""

    def __init__(self, clock: Callable[[], float] | None = None) -> None:
        self._clock = clock or time.monotonic
        self.registry = CapabilityRegistry()
        self.bus = EventBus()
        self.authority = AuthorityManager(self._clock)
        self.leases = LeaseManager(self._clock)
        self.devices: dict[str, Any] = {}
        self.started = False
        self.driver_registry: DriverRegistry | None = None
        self.health = HealthManager(self.bus)

    def start(self) -> None:
        """Start the local runtime lifecycle without changing the command boundary."""
        if self.started:
            return
        self.started = True
        self.bus.publish("runtime.started", "runtime", {})

    def attach_driver_registry(self, registry: DriverRegistry) -> None:
        self.driver_registry = registry

    def close(self) -> None:
        """Put every commandable device in its safe state and close attached drivers."""
        if not self.started and not self.devices:
            return
        for device in self.devices.values():
            if hasattr(device, "safe"):
                device.safe()
        self.leases.revoke_all()
        self.authority.revoke_all()
        if self.driver_registry is not None:
            self.driver_registry.close()
        self.started = False
        self.bus.publish("runtime.stopped", "runtime", {})

    def register(self, capability: Capability, device: Any | None = None) -> None:
        self.registry.register(capability)
        self.health.register(capability.path)
        if device is not None:
            self.devices[capability.path] = device
        self.bus.publish("device.registered", capability.path, {"capability": capability.to_dict()})

    def register_simulator(self, simulated_robot: Any) -> None:
        for device in simulated_robot.devices.values():
            self.register(device.capability, device)
        for capability in simulated_robot.static_capabilities:
            self.register(capability)

    def discover(self) -> list[dict[str, Any]]:
        return [capability.to_dict() for capability in self.registry.list()]

    def acquire_control(self, domain: str, owner: str, priority: int, ttl_s: float = 5.0) -> AuthorityGrant:
        grant = self.authority.acquire(domain, owner, priority, ttl_s)
        self.bus.publish("authority.granted", domain, {"grant": grant.to_dict()})
        return grant

    def acquire_lease(self, target: str, owner: str, authority_token: str, ttl_s: float = 0.25) -> Lease:
        self.authority.validate(self._domain(target), owner, authority_token)
        self.registry.get(target)
        lease = self.leases.acquire(target, owner, ttl_s)
        self.bus.publish("lease.acquired", target, {"lease": lease.to_dict()})
        return lease

    def renew_lease(self, token: str, ttl_s: float = 0.25) -> Lease:
        lease = self.leases.renew(token, ttl_s)
        self.bus.publish("lease.renewed", lease.target, {"lease": lease.to_dict()})
        return lease

    def command(
        self,
        target: str,
        method: str,
        value: Any,
        owner: str,
        authority_token: str,
        lease_token: str,
    ) -> Event:
        self.authority.validate(self._domain(target), owner, authority_token)
        self.leases.validate(target, owner, lease_token)
        try:
            validate_contract(self.registry.get(target)).validate_command(method, value)
        except (TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        device = self.devices.get(target)
        if device is None or not hasattr(device, "command"):
            raise CommandError(f"capability is not commandable: {target}")
        try:
            telemetry = device.command(method, value)
        except (TypeError, ValueError) as exc:
            raise CommandError(str(exc)) from exc
        self.bus.publish("command", target, {"owner": owner, "method": method, "value": value})
        return self.bus.publish("state", target, telemetry)

    def tick(self, now: float | None = None) -> list[str]:
        """Expire safety leases and put affected actuators into their safe state."""
        current = self._clock() if now is None else now
        if current < self._clock():
            raise ValueError("tick time cannot move backward")
        expired = self.leases.expire(current)
        stopped: list[str] = []
        for lease in expired:
            device = self.devices.get(lease.target)
            if device is not None and hasattr(device, "safe"):
                telemetry = device.safe()
                stopped.append(lease.target)
                self.bus.publish("fault", lease.target, {"code": "LEASE_EXPIRED", "safe_state": "activated"})
                self.bus.publish("state", lease.target, telemetry)
        self.authority.expire(current)
        return stopped

    @staticmethod
    def _domain(target: str) -> str:
        return target.split(".", 1)[0]
