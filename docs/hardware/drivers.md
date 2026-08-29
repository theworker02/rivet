# Drivers

Reference drivers are under `drivers/`. They are dependency-light test adapters, not universal physical board implementations.

To add a driver:

1. define a capability contract;
2. implement command and idempotent safe behavior;
3. isolate optional hardware imports;
4. add a mock backend and fault test;
5. document pins, buses, timing, and limits;
6. register through `DriverRegistry`.

A driver must not bypass the runtime authority and lease boundary.
