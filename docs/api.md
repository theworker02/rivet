# API surface

Rivet 1.2.0 has a small stable core and explicit Beta/experimental extensions. The public core imports are:

```python
from rivet import (
    Capability,
    CapabilityContract,
    Device,
    Distance,
    HealthState,
    RobotRuntime,
    SimulatedRobot,
    Velocity,
)
from rivet.capsule import Capsule
from rivet.protocol import FrameCodec, RivetFrame
from rivet.storage import JsonStore
```

Use dedicated modules for the other public seams:

- `rivet.units` — `Distance`, `Velocity`, `Angle`, `Force`, `Voltage`, `Current`, `Temperature`, `Duration`, and `Frequency`.
- `rivet.contracts` — typed command/telemetry descriptors and range validation.
- `rivet.health` — `HealthState`, capability health, and bounded recovery evidence.
- `rivet.recorder` — `Recorder`, `ReplaySession`, `timeline`, and recording validation.
- `rivet.configuration` — schema-v2 configuration validation and migration.
- `rivet.mission_ops` — dry-run reports, checkpoints, and compensation transactions.
- `rivet.capsule` — portable declarative bundles and compatibility validation.

API visibility is tracked in `rivet.api`: `PUBLIC` interfaces receive compatibility tests, `EXPERIMENTAL` interfaces may change during the 1.2 Beta line, and `INTERNAL` names are not supported imports. Version changes require a changelog entry and a passing `rivet check-release`.
