from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .driver import DriverInfo
from .models import Capability


@dataclass
class SimulatedMotor:
    path: str
    max_rpm: float = 180.0
    safe_state: str = "brake"
    velocity: float = 0.0
    rpm: float = 0.0
    temperature_c: float = 35.0

    @property
    def capability(self) -> Capability:
        return Capability(
            path=self.path,
            type="motion.dc-motor",
            commands={"velocity": {"input": "float", "range": [-1.0, 1.0]}},
            telemetry={"rpm": {"type": "float"}, "temperature_c": {"type": "float"}},
            safety={"timeout_ms": 250, "fail_state": self.safe_state},
            metadata={"max_rpm": self.max_rpm, "simulated": True},
        )

    def command(self, method: str, value: Any) -> dict[str, Any]:
        if method != "velocity":
            raise ValueError(f"unsupported motor command: {method}")
        requested = float(value)
        if not -1.0 <= requested <= 1.0:
            raise ValueError("motor velocity must be between -1.0 and 1.0")
        self.velocity = requested
        self.rpm = requested * self.max_rpm
        return self.telemetry()

    def safe(self) -> dict[str, Any]:
        self.velocity = 0.0
        self.rpm = 0.0
        return self.telemetry()

    def telemetry(self) -> dict[str, Any]:
        return {"velocity": round(self.velocity, 4), "rpm": round(self.rpm, 2), "temperature_c": self.temperature_c}


class SimulatedSensor:
    """A deterministic commandable sensor used to exercise disconnect/reconnect paths."""

    def __init__(self, path: str, sensor_type: str = "imu.9dof") -> None:
        self.path = path
        self.sensor_type = sensor_type
        self.samples = 0

    @property
    def capability(self) -> Capability:
        return Capability(
            self.path,
            self.sensor_type,
            commands={"sample": {"input": "null"}},
            telemetry={"orientation": {"type": "quaternion"}, "samples": {"type": "integer"}},
            metadata={"rate_hz": 100, "simulated": True},
        )

    def command(self, method: str, value: Any) -> dict[str, Any]:
        if method not in ("sample", "read"):
            raise ValueError(f"unsupported sensor command: {method}")
        self.samples += 1
        return {"orientation": [0.0, 0.0, 0.0, 1.0], "samples": self.samples}

    def safe(self) -> dict[str, Any]:
        return {"orientation": [0.0, 0.0, 0.0, 1.0], "samples": self.samples}


class SimulatedRobot:
    """A deterministic rover fixture used by the CLI and local development."""

    def __init__(self) -> None:
        self.devices: dict[str, SimulatedMotor | SimulatedSensor] = {
            "motion.left-wheel": SimulatedMotor("motion.left-wheel"),
            "motion.right-wheel": SimulatedMotor("motion.right-wheel"),
            "perception.imu": SimulatedSensor("perception.imu"),
        }
        self.static_capabilities = [
            Capability(
                "vision.front-camera",
                "camera.rgb",
                metadata={"resolution": "1280x720", "simulated": True},
                telemetry={"frames": {"type": "integer"}},
            ),
            Capability(
                "power.primary-battery",
                "battery.dc",
                telemetry={"voltage": {"type": "float"}, "percentage": {"type": "float"}},
                metadata={"simulated": True},
            ),
        ]


class SimulatedRobotDriver:
    """Driver boundary for the dependency-free simulated rover."""

    def __init__(self, robot: SimulatedRobot | None = None) -> None:
        self.robot = robot or SimulatedRobot()
        self.info = DriverInfo(
            "simulator",
            "1.0",
            ("motion.dc-motor", "imu.9dof"),
            True,
            "SIMULATED",
            ("simulator",),
            ("virtual",),
            {"simulation": True, "integration": True, "hardware": False},
        )
        self.closed = False

    def discover(self) -> list[tuple[Capability, SimulatedMotor | SimulatedSensor]]:
        if self.closed:
            raise RuntimeError("simulator driver is closed")
        return [(device.capability, device) for device in self.robot.devices.values()]

    def close(self) -> None:
        self.closed = True
