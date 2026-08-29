# Drivers

Reference drivers are under `drivers/`. They are dependency-light test adapters, not universal physical board implementations. Qualification is visible through `rivet drivers` and `DriverInfo`; file presence alone is not support evidence.

To add a driver:

1. define a versioned capability contract with typed units, ranges, dependencies, health minimum, watchdog, and failure action;
2. implement command, telemetry, bounded recovery, and idempotent safe behavior;
3. isolate optional hardware imports;
4. add deterministic mock/simulation coverage and fault tests;
5. document pins, buses, timing, limits, platform, and wiring;
6. run `rivet hardware certify <driver>` against the actual device;
7. attach the generated report to the pull request and set only the qualification status supported by evidence.

A driver must not bypass the runtime authority and lease boundary. `SIMULATED` and `TESTED` are useful states, but neither means a board is hardware-certified.
