from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CURRENT_CONFIG_SCHEMA = 2


@dataclass
class RobotConfig:
    robot_id: str
    platform: str = "simulator"
    simulate: bool = True
    devices: dict[str, dict[str, Any]] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    role: dict[str, Any] = field(default_factory=dict)
    schema_version: int = CURRENT_CONFIG_SCHEMA

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "RobotConfig":
        normalized, _ = migrate_document(value)
        robot = normalized.get("robot", {})
        robot_id = robot.get("id")
        if not robot_id:
            raise ValueError("configuration requires robot.id")
        return cls(
            str(robot_id),
            str(robot.get("platform", "simulator")),
            bool(normalized.get("simulate", True)),
            dict(normalized.get("devices", {})),
            dict(normalized.get("safety", {})),
            dict(normalized.get("role", {})),
            int(normalized.get("rivet", CURRENT_CONFIG_SCHEMA)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "rivet": self.schema_version,
            "robot": {"id": self.robot_id, "platform": self.platform},
            "simulate": self.simulate,
            "devices": self.devices,
            "safety": self.safety,
            "role": self.role,
        }


@dataclass(frozen=True)
class MigrationResult:
    source_version: int
    target_version: int
    changes: tuple[str, ...]
    document: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_version": self.source_version,
            "target_version": self.target_version,
            "changes": list(self.changes),
            "document": self.document,
        }


def migrate_document(value: dict[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    if not isinstance(value, dict):
        raise ValueError("configuration root must be an object")
    source_version = value.get("rivet", value.get("schema_version", 1))
    if not isinstance(source_version, int) or source_version < 1:
        raise ValueError("configuration schema version must be a positive integer")
    if source_version > CURRENT_CONFIG_SCHEMA:
        raise ValueError(f"configuration schema {source_version} is newer than supported schema {CURRENT_CONFIG_SCHEMA}")
    document = dict(value)
    changes: list[str] = []
    if source_version == 1:
        robot = document.get("robot", {})
        if isinstance(robot, str):
            document["robot"] = {"id": robot, "platform": document.pop("platform", "simulator")}
            changes.append("converted robot string to robot.id")
        if "devices" not in document and "capabilities" in document:
            document["devices"] = document.pop("capabilities")
            changes.append("renamed capabilities to devices")
        document.pop("schema_version", None)
        document["rivet"] = CURRENT_CONFIG_SCHEMA
        changes.append("migrated configuration schema v1 to v2")
    elif "rivet" not in document:
        document["rivet"] = CURRENT_CONFIG_SCHEMA
        document.pop("schema_version", None)
        changes.append("normalized configuration schema marker")
    return document, tuple(changes)


class ConfigLoader:
    """Versioned dependency-free JSON configuration loader and migrator."""

    def load(self, path: str | Path) -> RobotConfig:
        source = Path(path)
        if source.suffix.lower() not in (".json", ".rivet"):
            raise ValueError("core configuration uses JSON; use a maintained adapter before loading YAML manifests")
        with source.open(encoding="utf-8") as handle:
            value = json.load(handle)
        return RobotConfig.from_dict(value)

    def validate(self, path: str | Path | None = None, value: dict[str, Any] | None = None) -> RobotConfig:
        if path is not None and value is not None:
            raise ValueError("provide either a path or an in-memory configuration")
        if path is not None:
            return self.load(path)
        if value is None:
            raise ValueError("configuration path or value is required")
        return RobotConfig.from_dict(value)

    def migrate(self, path: str | Path, destination: str | Path | None = None) -> MigrationResult:
        source = Path(path)
        with source.open(encoding="utf-8") as handle:
            value = json.load(handle)
        normalized, changes = migrate_document(value)
        config = RobotConfig.from_dict(normalized)
        target = Path(destination) if destination is not None else source
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(config.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        source_version = value.get("rivet", value.get("schema_version", 1))
        return MigrationResult(int(source_version), CURRENT_CONFIG_SCHEMA, changes, config.to_dict())

    def write_default(self, path: str | Path, robot_id: str = "rover-demo") -> RobotConfig:
        config = RobotConfig(robot_id)
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(config.to_dict(), indent=2) + "\n", encoding="utf-8")
        return config
