# Repository architecture

The `src/rivet` package remains the installable core. Top-level `drivers/` contains reference/mock adapters, `sdk/` contains application-facing examples and schemas, `tests/` verifies behavior, and `tools/` contains developer/release scripts.

```text
application
   │
   ▼
VocationRuntime → ContinuumRuntime → RobotRuntime
                                      │
                         Guard / authority / leases
                                      │
                         Device + Driver contracts
                                      │
                         mock or physical adapters
```

The simulator is a real backend used by CLI and tests; no Pi import is required for core startup.
