# Roadmap

Rivet 1.2.0 is the current verification-gated Beta release. The shipped surface is intentionally broader than the original repository foundation, but physical hardware support remains evidence-specific.

## 1.2.0 — Verification-gated Beta (current)

- [x] Versioned schema-v2 configuration and migration
- [x] `rivet verify` and 18 executable end-to-end simulator scenarios
- [x] Strict release/content/documentation/package gates
- [x] Typed units and capability contracts
- [x] Driver qualification metadata and hardware certification reports
- [x] Capability health, Pulse, bounded recovery, and fault domains
- [x] Versioned recorder, deterministic replay, and timeline inspection
- [x] Dry runs, checkpoints, compensation transactions, Reflex, and Capsules
- [x] Compatibility matrix, resource tiers, performance budgets, support bundles, and crash inspection
- [x] CI separation for tests, end-to-end, documentation, package, security, Pi compatibility, benchmarks, and release

## 1.3 — Deployment hardening

- [ ] Maintained Raspberry Pi GPIO/I²C/SPI/UART production adapters with board-specific conformance evidence
- [ ] Hardware-in-the-loop fixtures and reviewed emergency-stop/watchdog integration
- [ ] Process-isolated Guard and supervisor service with restart/rollback validation
- [ ] Authenticated transport endpoint and fleet identity/key rotation
- [ ] Persistent signed role/skill/passport registry with revocation and audit retention

## Later integrations

- [ ] ROS adapter and additional SDKs
- [ ] Dashboard/UI backed by the same Pulse and recorder APIs
- [ ] A/B updates and signed package registry
- [ ] Independent safety certification where a deployment requires it

A roadmap item is not a release claim until it has an implementation, tests, documentation, and a passing release gate.
