from __future__ import annotations

from collections import deque
from typing import Any

from ..models import Capability


class MockGPIO:
    def __init__(self) -> None:
        self.values: dict[int, int] = {}

    def setup(self, pin: int, initial: int = 0) -> None:
        self.values[pin] = int(bool(initial))

    def write(self, pin: int, value: int) -> None:
        if pin not in self.values:
            raise KeyError(pin)
        self.values[pin] = int(bool(value))

    def read(self, pin: int) -> int:
        return self.values[pin]


class MockI2CBus:
    def __init__(self) -> None:
        self.registers: dict[tuple[int, int], int] = {}

    def write_byte_data(self, address: int, register: int, value: int) -> None:
        self.registers[(address, register)] = value & 0xFF

    def read_byte_data(self, address: int, register: int) -> int:
        return self.registers.get((address, register), 0)


class MockSPI:
    def transfer(self, payload: bytes) -> bytes:
        return bytes(payload)


class MockUART:
    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self.received: deque[bytes] = deque()

    def write(self, payload: bytes) -> None:
        self.sent.append(bytes(payload))

    def feed(self, payload: bytes) -> None:
        self.received.append(bytes(payload))

    def read(self) -> bytes | None:
        return self.received.popleft() if self.received else None


class GenericPwmMotor:
    def __init__(self, path: str, max_rpm: float = 180.0) -> None:
        self.path = path
        self.max_rpm = max_rpm
        self.velocity = 0.0

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
