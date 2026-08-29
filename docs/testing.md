# Testing and verification

Rivet 1.2.0 has separate unit, integration, simulator, hardware-mock, and end-to-end gates:

```bat
python -m pytest
python -m pytest tests/e2e -q
python -m compileall -q src drivers sdk tests
python -m ruff check src tests drivers sdk
python -m mypy src
```

The installation-health command exercises the actual local runtime path:

```bat
python -m rivet verify
python -m rivet verify --json
```

It validates configuration, startup, driver discovery, capability registration and health, safety initialization, roles, skills, mission parsing, simulation, command/telemetry, recording, replay, and graceful shutdown, then runs 18 named scenarios. The scenarios include sensor loss/recovery, motor watchdog expiry, low memory, overtemperature, role transition, multi-robot registration, dry runs, Reflex, Pulse, Capsule validation, and fault-domain isolation.

Before publishing:

```bat
rivet-dev audit-content
python -m rivet check-release
```

The release gate blocks on failing tests, stale package metadata, broken local links/assets, invalid examples/schemas, unfinished release code, or an unbuildable wheel/sdist. Physical hardware tests are never inferred from simulator PASS results.


## Developer tooling and evidence

The canonical developer entry points are executable rather than placeholder extraction folders:

```bat
python tools\dev.py check
rivet-dev audit-content
python tools\dev.py release-check
python -m rivet resource-test
python -m rivet benchmark runtime
python tools\site\build.py
```

`rivet-dev audit-content` scans source Python in `src/`, `drivers/`, and `sdk/` for unfinished markers and empty packages, with only explicit exceptions in `[tool.rivet.audit]`. `rivet check-release` additionally validates generated package metadata, the `rivet-dev` entry point, Markdown links, static-site HTML assets, examples, schemas, tests, and wheel/sdist creation. A skipped check is diagnostic output, not release evidence.