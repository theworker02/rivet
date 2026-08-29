class MockI2CBus:
    """Register-based I2C test double."""

    def __init__(self) -> None:
        self.registers: dict[tuple[int, int], int] = {}

    def write_byte_data(self, address: int, register: int, value: int) -> None:
        self.registers[(address, register)] = value & 0xFF

    def read_byte_data(self, address: int, register: int) -> int:
        return self.registers.get((address, register), 0)
