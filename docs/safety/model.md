# Safety model

Rivet safety is layered:

1. preflight checks readiness;
2. authority controls controller priority;
3. actuator leases expire without refresh;
4. `RivetGuard` monitors heartbeats and invokes safe state;
5. devices implement local idempotent `safe()` behavior;
6. hardware or MCU watchdogs remain the production target.

Roles, passports, missions, Synapse packages, and AI agents cannot bypass these controls.
