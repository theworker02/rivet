# Safety model

Rivet 1.2 keeps safety below roles, missions, and AI:

1. typed capability contracts reject unsupported commands and out-of-range values;
2. preflight reports readiness before motion;
3. authority controls controller priority and ownership;
4. short actuator leases expire without refresh;
5. `RivetGuard` monitors heartbeats, invokes `safe()`, and revokes control;
6. Reflex can apply deterministic local stop/abort responses;
7. fault domains contain non-safety failures while a safety failure disables actuators;
8. device and hardware/MCU watchdogs remain independently required for physical deployments.

Health states are evidence, not permission. A `DEGRADED` camera may restrict a perception mission; it never grants motion authority. Bounded recovery may retry a driver, reset it, or promote a fallback, but actuator safety never depends on endless automatic retries.

Roles, passports, missions, Synapse packages, Capsules, and AI agents cannot bypass authority, leases, Guard, or physical interlocks. Rivet is not a certified safety controller.
