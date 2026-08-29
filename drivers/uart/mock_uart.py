from collections import deque


class MockUART:
    """Deterministic in-memory UART endpoint for bridge tests."""

    def __init__(self) -> None:
        self._received: deque[bytes] = deque()
        self.sent: list[bytes] = []

    def write(self, payload: bytes) -> None:
        self.sent.append(bytes(payload))

    def feed(self, payload: bytes) -> None:
        self._received.append(bytes(payload))

    def read(self) -> bytes | None:
        return self._received.popleft() if self._received else None
