# API surface

Stable core imports currently include:

```python
from rivet import Capability, Device, RobotRuntime, ContinuumRuntime, SimulatedRobot
from rivet.protocol import FrameCodec, RivetFrame
from rivet.storage import JsonStore
```

Phase III domain types remain available from dedicated modules such as `rivet.skills`, `rivet.vocation`, `rivet.mission`, and `rivet.motion_ir`. Public exports should be expanded only with compatibility tests and changelog entries.
