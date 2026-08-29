from __future__ import annotations

import json
import platform
import sys
import traceback
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .version import __version__

_SENSITIVE = {"password", "secret", "token", "credential", "private_key", "api_key", "signing_key"}


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items() if not any(secret in str(key).lower() for secret in _SENSITIVE)}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def system_info() -> dict[str, str]:
    return {
        "rivet_version": __version__,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "processor": platform.processor() or "unknown",
    }


@dataclass(frozen=True)
class CrashRecord:
    timestamp: str
    system: dict[str, str]
    active_drivers: tuple[str, ...]
    current_role: str | None
    current_mission: str | None
    recent_faults: tuple[dict[str, Any], ...]
    recent_commands: tuple[dict[str, Any], ...]
    resource_pressure: dict[str, Any]
    stack_trace: str

    def to_dict(self) -> dict[str, Any]:
        return sanitize(asdict(self))


class CrashReporter:
    """Persists sanitized crash records without raw sensor payloads or secrets."""

    def __init__(self, directory: str | Path | None = None) -> None:
        self.directory = Path(directory or (Path.home() / ".rivet" / "crashes"))
        self._recent: list[dict[str, Any]] = []

    def attach(self, bus: Any, limit: int = 50) -> None:
        def record(event: Any) -> None:
            self._recent.append({"type": event.type, "source": event.source, "sequence": event.sequence})
            del self._recent[:-limit]

        bus.subscribe("*", record)

    def capture(
        self,
        exception: BaseException,
        runtime: Any | None = None,
        role: str | None = None,
        mission: str | None = None,
        resources: dict[str, Any] | None = None,
    ) -> Path:
        faults = tuple(event for event in self._recent if "fault" in event.get("type", ""))
        commands = tuple(event for event in self._recent if event.get("type") == "command")
        drivers = tuple(sorted(getattr(getattr(runtime, "driver_registry", None), "_drivers", {}).keys())) if runtime else ()
        record = CrashRecord(
            datetime.now(timezone.utc).isoformat(),
            system_info(),
            drivers,
            role,
            mission,
            faults,
            commands,
            sanitize(resources or {}),
            "".join(traceback.format_exception(type(exception), exception, exception.__traceback__)),
        )
        self.directory.mkdir(parents=True, exist_ok=True)
        destination = self.directory / f"crash-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
        destination.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return destination

    def latest(self) -> Path | None:
        records = sorted(self.directory.glob("crash-*.json")) if self.directory.exists() else []
        return records[-1] if records else None

    def inspect(self, path: str | Path | None = None) -> dict[str, Any]:
        target = Path(path) if path and str(path) != "latest" else self.latest()
        if target is None or not target.exists():
            raise FileNotFoundError("no Rivet crash report exists")
        value = json.loads(target.read_text(encoding="utf-8"))
        value["path"] = str(target)
        return sanitize(value)


class SupportBundle:
    """Creates a portable sanitized diagnostics archive for issue reports."""

    def create(self, output: str | Path, runtime: Any | None = None, verification: dict[str, Any] | None = None) -> Path:
        destination = Path(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        diagnostics: dict[str, Any] = {"system": system_info(), "verification": verification or {}}
        if runtime is not None:
            diagnostics["capabilities"] = runtime.discover()
            health = getattr(runtime, "health", None)
            diagnostics["health"] = health.status() if health is not None else {}
            diagnostics["devices"] = sorted(runtime.devices)
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("diagnostics.json", json.dumps(sanitize(diagnostics), indent=2, sort_keys=True) + "\n")
        return destination
