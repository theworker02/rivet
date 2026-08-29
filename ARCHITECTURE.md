# Rivet architecture

Rivet `1.2.0` is layered so high-level specialization cannot bypass low-level command safety or release evidence:

```text
Applications / AI / SDKs
             │
             ▼
 VocationRuntime + mission operations + Capsules
             │
             ▼
 ContinuumRuntime + resources + perception + topology
             │
             ▼
 RobotRuntime + EventBus + typed contracts
       │                 │                  │
 Guard / Reflex      Health / Pulse     Recorder / Replay
             │
             ▼
 Capability registry and DriverRegistry contracts
             │
       simulator, mocks, or qualified adapters
```

`RobotRuntime` owns discovery, capability registration, typed command validation, authority grants, actuator leases, event publication, and shutdown. `RivetGuard` and Reflex provide bounded protective behavior; neither is a substitute for an independently reviewed hardware watchdog or emergency-stop circuit.

`ContinuumRuntime` makes resource profiles, lifecycle, perception provenance, topology, and offline cluster decisions explicit. `VocationRuntime` composes roles, SkillGraph evidence, missions, Synapse packages, Motion IR, passports, teams, and EchoMap records without minting command authority.

The simulator and mock drivers implement the observable contracts used by integration tests. Qualified physical adapters remain evidence-bearing integrations. The `rivet verify` pipeline and `rivet check-release` gate exercise startup, discovery, safety, mission, telemetry, recorder/replay, shutdown, documentation, metadata, and package-build paths. See `docs/architecture.md` for the detailed boundaries and `docs/architecture/overview.md` for the repository map.
