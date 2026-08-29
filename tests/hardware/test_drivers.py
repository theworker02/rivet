from drivers.gpio.mock_gpio import MockGPIO
from drivers.i2c.mock_i2c import MockI2CBus
from drivers.motors.generic_pwm import GenericPwmMotor
from drivers.spi.mock_spi import MockSPI
from drivers.uart.mock_uart import MockUART


def test_mock_buses_are_deterministic():
    gpio = MockGPIO()
    gpio.setup(12)
    gpio.write(12, 1)
    assert gpio.read(12) == 1
    i2c = MockI2CBus()
    i2c.write_byte_data(0x40, 1, 255)
    assert i2c.read_byte_data(0x40, 1) == 255
    assert MockSPI().transfer(b"abc") == b"abc"
    uart = MockUART()
    uart.write(b"hello")
    uart.feed(b"reply")
    assert uart.sent == [b"hello"] and uart.read() == b"reply"


def test_generic_motor_contract_and_safe_state():
    motor = GenericPwmMotor("motion.test")
    assert motor.command("velocity", 0.5)["rpm"] == 90.0
    assert motor.safe()["rpm"] == 0.0
