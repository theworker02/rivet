from __future__ import annotations

from .generic_pwm import GenericPwmMotor


class Tb6612Motor(GenericPwmMotor):
    """TB6612 pin-aware wrapper; GPIO output is injected by deployment code."""

    def __init__(self, path: str, pwm_pin: int, direction_pin: int, max_rpm: float = 180.0) -> None:
        super().__init__(path, max_rpm)
        self.pwm_pin = pwm_pin
        self.direction_pin = direction_pin
