# Rivet 1.2.0 architecture

Rivet `1.2.0` keeps the detailed runtime boundaries below the release verification plane:

```text
Applications / AI / SDKs
          │
          ▼
VocationRuntime — roles, skills, missions, teams
          │
          ▼
Operations — dry runs, checkpoints, compensation, Capsules
          │
          ▼
ContinuumRuntime — profiles, resources, perception, topology
          │
          ▼
RobotRuntime — capabilities, typed contracts, authority, leases, events
          │
          ├── RivetGuard / Reflex / fault domains
          ├── Pulse / health / bounded recovery
          └── DriverRegistry → simulator or qualified adapter

Verification and release plane
  configuration → startup → discovery → safety → mission → telemetry → recorder/replay → shutdown
  content audit → tests → documentation links → package metadata → wheel/sdist build
```

## Runtime boundaries

`RobotRuntime` owns capability registration, typed command validation, authority grants, actuator leases, command dispatch, telemetry/state events, capability health, and safe shutdown. `RivetGuard` monitors heartbeats and invokes device `safe()` behavior. Reflex rules are deterministic local reactions for small protective conditions; they do not replace Guard or a hardware watchdog.

`ContinuumRuntime` selects resource profiles and records governor decisions. `HealthManager` turns fault and restore events into explicit `HEALTHY`, `DEGRADED`, `UNSTABLE`, `FAILED`, or `UNKNOWN` states. `FaultDomainManager` contains UI, perception, network, missions, recording, and other non-safety failures; a safety failure disables actuators and revokes control instead of allowing degraded motion.

## Evidence paths

The simulator is a real backend, not a fake driver. `rivet verify` runs the runtime from configuration through graceful shutdown and then executes 18 end-to-end scenarios. `Recorder` writes versioned RVT/1 JSONL events; `ReplaySession` validates sequence order and `rivet timeline` exposes the event chronology. `rivet check-release` blocks publishing on failed tests, broken links/assets, invalid schemas/examples, unfinished release code, stale metadata, or an unbuildable package.

## Vocation and missions

Roles and SkillGraph evidence describe competence but never mint authority tokens. Mission admission checks role and skill requirements. `MissionDryRunner` reports role, skill, hardware, safety, estimates, and planned actions without issuing a command. `MissionCheckpointStore` persists verified progress, and `MissionTransaction` requires explicit compensation actions for logical reservations.

## Drivers and physical scope

`DriverInfo` records supported capability types, platform, bus, qualification status, and simulation/integration/hardware evidence. `DriverRegistry.qualify()` validates discovery and safe-state behavior. `HardwareCertifier` produces a report, but simulated results are deliberately marked `SIMULATED` and cannot become `HARDWARE-VERIFIED`. Electrical, mechanical, emergency-stop, identity, and regulatory reviews remain deployment responsibilities.
