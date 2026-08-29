from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Measurement:
    """Typed scalar with explicit dimensional units and deterministic conversion."""

    value: float
    unit: str
    dimension: ClassVar[str] = "scalar"
    factors: ClassVar[dict[str, float]] = {"": 1.0}

    def __post_init__(self) -> None:
        if self.unit not in self.factors:
            raise ValueError(f"unsupported {self.dimension} unit: {self.unit}")
        if not isinstance(self.value, (int, float)):
            raise TypeError("measurement value must be numeric")

    def to(self, unit: str) -> "Measurement":
        if unit not in self.factors:
            raise ValueError(f"unsupported {self.dimension} unit: {unit}")
        base = float(self.value) * self.factors[self.unit]
        return type(self)(base / self.factors[unit], unit)

    def __float__(self) -> float:
        return float(self.value)

    def to_dict(self) -> dict[str, object]:
        return {"value": self.value, "unit": self.unit, "dimension": self.dimension}


@dataclass(frozen=True)
class Distance(Measurement):
    dimension: ClassVar[str] = "distance"
    factors: ClassVar[dict[str, float]] = {"m": 1.0, "cm": 0.01, "mm": 0.001}


@dataclass(frozen=True)
class Velocity(Measurement):
    dimension: ClassVar[str] = "velocity"
    factors: ClassVar[dict[str, float]] = {"m/s": 1.0, "cm/s": 0.01}


@dataclass(frozen=True)
class Angle(Measurement):
    dimension: ClassVar[str] = "angle"
    factors: ClassVar[dict[str, float]] = {"rad": 1.0, "deg": 3.141592653589793 / 180.0}


@dataclass(frozen=True)
class Force(Measurement):
    dimension: ClassVar[str] = "force"
    factors: ClassVar[dict[str, float]] = {"N": 1.0}


@dataclass(frozen=True)
class Voltage(Measurement):
    dimension: ClassVar[str] = "voltage"
    factors: ClassVar[dict[str, float]] = {"V": 1.0, "mV": 0.001}


@dataclass(frozen=True)
class Current(Measurement):
    dimension: ClassVar[str] = "current"
    factors: ClassVar[dict[str, float]] = {"A": 1.0, "mA": 0.001}


@dataclass(frozen=True)
class Temperature(Measurement):
    dimension: ClassVar[str] = "temperature"
    factors: ClassVar[dict[str, float]] = {"C": 1.0, "K": 1.0}

    def to(self, unit: str) -> "Temperature":
        if unit not in self.factors:
            raise ValueError(f"unsupported temperature unit: {unit}")
        celsius = float(self.value) if self.unit == "C" else float(self.value) - 273.15
        converted = celsius if unit == "C" else celsius + 273.15
        return Temperature(converted, unit)


@dataclass(frozen=True)
class Duration(Measurement):
    dimension: ClassVar[str] = "duration"
    factors: ClassVar[dict[str, float]] = {"s": 1.0, "ms": 0.001}


@dataclass(frozen=True)
class Frequency(Measurement):
    dimension: ClassVar[str] = "frequency"
    factors: ClassVar[dict[str, float]] = {"Hz": 1.0, "kHz": 1000.0}
