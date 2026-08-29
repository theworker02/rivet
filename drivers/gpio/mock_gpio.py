from __future__ import annotations

class MockGPIO:
    """Deterministic GPIO backend for development machines and tests."""

    def __init__(self) -> None:
        self.values: dict[int, int] = {}

    def setup(self, pin: int, initial: int = 0) -> None:
        self.values[pin] = 1 if initial else 0

    def write(self, pin: int, value: int) -> None:
        if pin not in self.values:
            raise KeyError(f"GPIO pin is not configured: {pin}")
        self.values[pin] = 1 if value else 0

    def read(self, pin: int) -> int:
        return self.values[pin]
