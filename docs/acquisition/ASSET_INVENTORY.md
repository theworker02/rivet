# Asset inventory â€” rivet

## Repository surfaces

| Asset | Location / notes |
|-------|------------------|
| Source tree | Repository root / language packages |
| Tests | `test/`, `tests/`, CI workflows if present |
| Docs | `README.md`, `docs/` |
| Diligence room | `docs/acquisition/` |
| License / notices | `LICENSE`, transition notices if present |
| Funding | `.github/FUNDING.yml` |
| CI | `.github/workflows/` if present |
| Branding | logos/assets folders if present |

## Capability highlights

- **Verification pipeline:** `rivet verify` checks configuration, startup, driver discovery, capability registration and health, safety, roles, skills, missions, simulation, command/telemetry, recorder/replay, and graceful shutdown.
- **Executable reliability scenarios:** 18 simulator scenarios cover boot, discovery, role assignment, mission admission, sensor recovery, watchdogs, resource pressure, recording/replay, multi-robot coordination, dry runs, Reflex, Pulse, Capsules, and fault-domain isolation.
- **Operational signals:** capability health, Pulse heartbeats, bounded recovery, fault domains, typed units, configuration migration, mission checkpoints, compensation, sanitized support bundles, and compatibility/resource checks.
- **Release quality gates:** `rivet check-release` and `rivet-dev audit-content` validate tests, documentation links/assets, examples, schemas, metadata, package artifacts, and unfinished release content.
- **Documentation and packaging:** the README, static site, architecture material, driver evidence, simulator workflows, safety boundaries, and installable wheel/sdist were updated for the Beta release.
- **RobotRuntime** is the command boundary. It owns capability registration, authority grants, leases, command dispatch, event publication, and simulator integration.
- **RivetGuard** is the heartbeat and emergency-stop boundary. Expired heartbeats transition commandable devices to their safe state and revoke active control.
- **ContinuumRuntime** models resource profiles, lifecycle, perception provenance, hardware topology, offline nodes, and adaptation decisions.
- **VocationRuntime** composes roles, competency evidence, transfer packages, mission planning, passports, experience marks, and team assignment without replacing runtime safety.
- Formal `Device`, `CommandableDevice`, `Driver`, and `DriverRegistry` contracts.
- Mock GPIO, IÃ‚Â²C, SPI, UART, motor, camera, and sensor drivers for deterministic tests.
- Capability descriptors with command schemas, telemetry, safety policy, and metadata.

## Usually excluded

Seller personal accounts, unrelated repos, and unreissued registry tokens â€” unless listed in the definitive agreement.

*Updated: 2026-09-22*
