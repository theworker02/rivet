# Repository architecture

Rivet 1.2.0 is organized around executable boundaries rather than empty architectural names:

```text
application / SDK / mission authoring
              │
              ▼
Vocation + Mission operations + Capsules
              │
              ▼
Continuum + resources + perception + topology
              │
              ▼
RobotRuntime + EventBus + typed contracts
       │              │                │
  Guard / Reflex   Health / Pulse   Recorder / Replay
              │
              ▼
DriverRegistry → simulator, mocks, or qualified hardware adapters
              │
              ▼
Verification and release gates
```

`src/rivet` is the installable core. Top-level `drivers/` contains reference adapters and qualification metadata, `sdk/` contains schemas/examples, `tests/` contains unit/integration/e2e coverage, `site/` contains the generated evidence site, and `tools/` contains executable developer/release utilities. Core startup imports without Raspberry Pi hardware libraries.
