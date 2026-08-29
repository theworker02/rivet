## [1.2.0] - 2026-08-29

Rivet 1.2.0 moves the project from Alpha to a verification-gated Beta release. The release claim is bounded: the simulator, contracts, safety flows, diagnostics, documentation, and package gates are exercised; physical hardware certification remains evidence-driven and adapter-specific.

### Added

- `rivet verify` with configuration, runtime startup, driver discovery, capability registration, safety, roles, skills, missions, simulation, command/telemetry, recorder, replay, and graceful-shutdown gates.
- Eighteen executable end-to-end simulator scenarios covering boot, discovery, role assignment, mission admission, sensor loss/recovery, watchdogs, resource pressure, recording/replay, multi-robot coordination, dry runs, Reflex, Pulse, Capsules, and fault-domain isolation.
- Strict `rivet check-release` and `rivet-dev audit-content` gates for tests, documentation links/assets, metadata, schemas, examples, package builds, and unfinished release code.
- Capability health/Pulse signals, deterministic Reflex reactions, fault-domain containment, Capsule validation, and simulator recovery seams.
- Versioned release metadata and 1.2 documentation covering verification, safety boundaries, driver evidence, simulator-first workflows, and release policy.

### Changed

- Version is now `1.2.0`; package status is Beta rather than Alpha.
- README and the static site show executable verification evidence instead of prototype-only status claims.
- CI and release workflows treat verification, end-to-end scenarios, content audits, documentation checks, and package builds as release gates.

### Safety and scope

- Rivet still does not claim a certified emergency-stop implementation, universal Raspberry Pi hardware support, production device identity, or autonomous authorization of dangerous capabilities.
- Physical driver support must be marked with qualification evidence; simulator PASS results never imply hardware certification.

## [0.4.0] - 2026-08-29

### Added

- Expanded adaptive runtime, safety, perception, Vocation, mission, and cluster layers.
- Formal device and driver contracts with dependency-free reference drivers.
- CRC-protected Rivet Link frame codec.
- JSON configuration and atomic local state storage.
- Simulation fault injection and `rivet run --simulate`.
- CLI commands for initialization, version, devices, roles, skills, and simulation.
- Python SDK example and capability schema.
- Automated tests for runtime safety, protocol framing, drivers, simulation, storage, CLI, and Vocation.
- Release, security, documentation, and GitHub community scaffolding.

### Changed

- Version is sourced from `src/rivet/version.py`.
- Optional Pi, vision, developer, documentation, and all extras are declared in `pyproject.toml`.
- Existing simulator, authority, lease, and Vocation APIs remain compatible.

### Documentation

- Added getting-started, hardware, safety, protocol, deployment, testing, and troubleshooting guides.
- Added a static documentation site source and architecture SVG.

## [0.3.0] - Phase III

- Added Vocation roles, SkillGraph, Synapse, Motion IR, passports, missions, teams, and EchoMap.

## [0.2.0] - Phase II

- Added Continuum profiles, governor, lifecycle, guard, topology, failover, perception provenance, diagnostics, and offline cluster primitives.

## [0.1.0] - Phase I

- Added capability registry, event bus, authority, leases, simulator, recorder, replay, and initial CLI.
