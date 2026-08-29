from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class JsonStore:
    """Atomic, versioned JSON persistence for optional local state."""

    def __init__(self, path: str | Path, schema_version: int = 1) -> None:
        self.path = Path(path)
        self.schema_version = schema_version

    def save(self, value: dict[str, Any]) -> None:
        document = {"schema_version": self.schema_version, "value": value}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent, text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(document, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def load(self) -> dict[str, Any]:
        with self.path.open(encoding="utf-8") as handle:
            document = json.load(handle)
        if document.get("schema_version") != self.schema_version:
            raise ValueError("unsupported JSON state schema version")
        value = document.get("value")
        if not isinstance(value, dict):
            raise ValueError("stored value must be an object")
        return value
