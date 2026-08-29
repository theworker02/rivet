from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Iterable


class SynapseStage(str, Enum):
    IMPORTED = "imported"
    ADAPTED = "adapted"
    SIMULATED = "simulated"
    PHYSICALLY_VALIDATED = "physically-validated"
    CERTIFIED = "certified"


_STAGE_ORDER = list(SynapseStage)


@dataclass(frozen=True)
class SynapsePackage:
    package_id: str
    skill_id: str
    version: str
    intent: str
    motion_primitives: tuple[str, ...] = ()
    sensor_requirements: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()
    hardware_assumptions: tuple[str, ...] = ()
    validation_tests: tuple[str, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("motion_primitives", "sensor_requirements", "failure_modes", "hardware_assumptions", "validation_tests"):
            value[key] = list(value[key])
        return value


@dataclass
class SynapseTransfer:
    package_id: str
    stage: SynapseStage = SynapseStage.IMPORTED
    adaptation: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["stage"] = self.stage.value
        return value


class SynapseRegistry:
    """Stores transferable intent and enforces local validation stages."""

    def __init__(self) -> None:
        self.packages: dict[str, SynapsePackage] = {}
        self.transfers: dict[str, SynapseTransfer] = {}

    def import_package(self, package: SynapsePackage) -> SynapseTransfer:
        if package.package_id in self.packages:
            raise ValueError(f"Synapse package already imported: {package.package_id}")
        self.packages[package.package_id] = package
        transfer = SynapseTransfer(package.package_id)
        self.transfers[package.package_id] = transfer
        return transfer

    def adapt(self, package_id: str, hardware: Iterable[str]) -> SynapseTransfer:
        package = self.packages[package_id]
        transfer = self.transfers[package_id]
        hardware_set = set(hardware)
        missing = sorted(set(package.hardware_assumptions) - hardware_set)
        if missing:
            raise ValueError(f"Synapse adaptation missing hardware: {', '.join(missing)}")
        transfer.stage = SynapseStage.ADAPTED
        transfer.adaptation = {"hardware": sorted(hardware_set), "missing": []}
        return transfer

    def advance(self, package_id: str, stage: SynapseStage, evidence: dict[str, Any] | None = None) -> SynapseTransfer:
        transfer = self.transfers[package_id]
        if _STAGE_ORDER.index(stage) != _STAGE_ORDER.index(transfer.stage) + 1:
            raise ValueError(f"invalid Synapse stage transition: {transfer.stage.value} -> {stage.value}")
        transfer.stage = stage
        transfer.evidence.append(evidence or {})
        return transfer

    def status(self) -> list[dict[str, Any]]:
        return [transfer.to_dict() for transfer in sorted(self.transfers.values(), key=lambda item: item.package_id)]
