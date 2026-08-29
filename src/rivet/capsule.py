from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Capsule:
    """Portable, declarative robot bundle; installation never implies certification."""

    name: str
    version: str
    robot_manifest: dict[str, Any]
    required_capabilities: set[str] = field(default_factory=set)
    required_roles: set[str] = field(default_factory=set)
    drivers: tuple[dict[str, Any], ...] = ()
    skills: tuple[dict[str, Any], ...] = ()
    missions: tuple[dict[str, Any], ...] = ()
    safety_rules: tuple[dict[str, Any], ...] = ()
    compatible_hardware: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for key in ("required_capabilities", "required_roles"):
            value[key] = sorted(value[key])
        for key in ("drivers", "skills", "missions", "safety_rules", "compatible_hardware"):
            value[key] = list(value[key])
        return {"format": "RVC/1", **value}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Capsule":
        if value.get("format", "RVC/1") != "RVC/1":
            raise ValueError("unsupported capsule format")
        if not value.get("name") or not value.get("version"):
            raise ValueError("capsule name and version are required")
        return cls(
            value["name"],
            value["version"],
            dict(value.get("robot_manifest", {})),
            set(value.get("required_capabilities", [])),
            set(value.get("required_roles", [])),
            tuple(value.get("drivers", [])),
            tuple(value.get("skills", [])),
            tuple(value.get("missions", [])),
            tuple(value.get("safety_rules", [])),
            tuple(value.get("compatible_hardware", [])),
        )

    def save(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return destination

    @classmethod
    def load(cls, path: str | Path) -> "Capsule":
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("capsule root must be an object")
        return cls.from_dict(value)


@dataclass(frozen=True)
class CapsuleValidation:
    ok: bool
    missing_capabilities: tuple[str, ...] = ()
    missing_roles: tuple[str, ...] = ()
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["missing_capabilities"] = list(self.missing_capabilities)
        value["missing_roles"] = list(self.missing_roles)
        return value


class CapsuleValidator:
    def validate(
        self,
        capsule: Capsule,
        available_capabilities: Iterable[str],
        available_roles: Iterable[str] | None = None,
    ) -> CapsuleValidation:
        available = set(available_capabilities)
        roles = set(available_roles or available)
        missing_capabilities = tuple(sorted(capsule.required_capabilities - available))
        missing_roles = tuple(sorted(capsule.required_roles - roles))
        ok = not missing_capabilities and not missing_roles
        if ok:
            detail = f"{capsule.name} {capsule.version} is compatible"
        else:
            detail = "missing requirements: " + ", ".join((*missing_capabilities, *missing_roles))
        return CapsuleValidation(ok, missing_capabilities, missing_roles, detail)


class CapsuleInstaller:
    """Validates a capsule before copying its declarative bundle into a store."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def install(self, capsule: Capsule, available: Iterable[str]) -> Path:
        result = CapsuleValidator().validate(capsule, available)
        if not result.ok:
            raise ValueError(result.detail)
        return capsule.save(self.directory / f"{capsule.name}-{capsule.version}.rvc")
