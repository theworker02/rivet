class MockSPI:
    """Echo SPI backend for protocol and driver tests."""

    def transfer(self, payload: bytes) -> bytes:
        return bytes(payload)
