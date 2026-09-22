# Acquisition Brief â€” rivet

**Date:** 2026-09-22  
**Repository:** https://github.com/theworker02/rivet  
**Default branch:** `main`  
**Primary language:** Python  
**Status:** Diligence briefing only. **No acquisition has occurred** by virtue of this file.  
**License:** Proprietary â€” sale, written commercial license, or completed asset transfer required (see root `LICENSE`).  
**Valuation:** Not stated.  
**Contact:** GitHub [@theworker02](https://github.com/theworker02) Â· [thanks.dev/u/gh/theworker02](https://thanks.dev/u/gh/theworker02)

> Cloning or forking this repository does **not** grant production, redistribution, SaaS, OEM, or commercial rights.

---

## 1. Executive thesis

<img src="site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="760"> <strong>Safety-first infrastructure for adaptive Raspberry Pi robotics.</strong><br> Discover hardware. Build capability. Keep authority explicit.

**Why a buyer cares:** rivet packages transferable product IP â€” source, docs, in-repo brand assets, and a diligence room under `docs/acquisition/` â€” under a clear proprietary posture so diligence can proceed without mistaking the repo for open source.

---

## 2. Product snapshot

| Item | Detail |
|------|--------|
| Product | rivet |
| Repo | `theworker02/rivet` |
| Language | Python |
| Open source? | **No** â€” proprietary |
| Rightsholder | theworker02 |
| Diligence pack | `docs/acquisition/` |

### Capability highlights (from current materials)

- **Verification pipeline:** `rivet verify` checks configuration, startup, driver discovery, capability registration and health, safety, roles, skills, missions, simulation, command/telemetry, recorder/replay, and graceful shutdown.
- **Executable reliability scenarios:** 18 simulator scenarios cover boot, discovery, role assignment, mission admission, sensor recovery, watchdogs, resource pressure, recording/replay, multi-robot coordination, dry runs, Reflex, Pulse, Capsules, and fault-domain isolation.
- **Operational signals:** capability health, Pulse heartbeats, bounded recovery, fault domains, typed units, configuration migration, mission checkpoints, compensation, sanitized support bundles, and compatibility/resource checks.
- **Release quality gates:** `rivet check-release` and `rivet-dev audit-content` validate tests, documentation links/assets, examples, schemas, metadata, package artifacts, and unfinished release content.
- **Documentation and packaging:** the README, static site, architecture material, driver evidence, simulator workflows, safety boundaries, and installable wheel/sdist were updated for the Beta release.
- **RobotRuntime** is the command boundary. It owns capability registration, authority grants, leases, command dispatch, event publication, and simulator integration.
- **RivetGuard** is the heartbeat and emergency-stop boundary. Expired heartbeats transition commandable devices to their safe state and revoke active control.
- **ContinuumRuntime** models resource profiles, lifecycle, perception provenance, hardware topology, offline nodes, and adaptation decisions.
- **VocationRuntime** composes roles, competency evidence, transfer packages, mission planning, passports, experience marks, and team assignment without replacing runtime safety.
- Formal `Device`, `CommandableDevice`, `Driver`, and `DriverRegistry` contracts.
- Mock GPIO, IÃ‚Â²C, SPI, UART, motor, camera, and sensor drivers for deterministic tests.
- Capability descriptors with command schemas, telemetry, safety policy, and metadata.

---

## 3. Problem / opportunity

Teams evaluating rivet typically need either (a) a commercial right to run or embed it, or (b) outright ownership of the Product IP for strategic build-out. Public GitHub visibility without a proprietary license creates false assumptions about free production use. This brief and the linked data room make the commercial path explicit.

---

## 4. What ships today

Honest maturity: treat repository contents, README claims, tests, and release tags as the source of truth. Do not assume production customers, ARR, filed patents, or SLAs unless separately evidenced in diligence.

Typical transferable surfaces:

- Source tree and build/test scripts present in-repo
- Documentation and design notes
- Acquisition / diligence markdown under `docs/acquisition/`
- Branding assets committed to the repository (if any)

---

## 5. Demo / evaluation path (buyer)

Minimal path (no secrets required unless README says otherwise):

```
```bat
python -m pip install --upgrade rivet-robot-runtime==1.2.0
rivet version --verbose
rivet verify
```
```bat
rivet --help
rivet-dev --help
rivet-dev audit-content
```
```bat
python -m pip install --upgrade rivet-robot-runtime
python -m rivet version
```
```text
rivet_robot_runtime-1.2.0-py3-none-any.whl
5ee535e3d61e802f71a37defdacf6e3dcb2a50ed8a846e2eab84ef5103e30040

rivet_robot_runtime-1.2.0.tar.gz
4845c873f25eeefde0f4d27663a165f5c3f731231c1f5309dadb829902a4b3e3
```
```bat
certutil -hashfile rivet_robot_runtime-1.2.0-py3-none-any.whl SHA256
certutil -hashfile rivet_robot_runtime-1.2.0.tar.gz SHA256
```
```bash
sha256sum rivet_robot_runtime-1.2.0-py3-none-any.whl
sha256sum rivet_robot_runtime-1.2.0.tar.gz
```
```text
Applications / AI / ROS / Web
              Ã¢â€â€š
              Ã¢â€“Â¼
 VocationRuntime Ã¢â‚¬â€ roles, skills, missions, teams
              Ã¢â€â€š
              Ã¢â€“Â¼
 ContinuumRuntime Ã¢â‚¬â€ profiles, perception, resources, cluster
              Ã¢â€â€š
              Ã¢â€“Â¼
 RobotRuntime Ã¢â‚¬â€ devices, capabilities, authority, leases
```

Extended evaluation: `docs/acquisition/BUYER_EVALUATION.md`. Written NDA / evaluation grants may be required for private materials.

---

## 6. What a transaction typically includes

Subject to definitive schedules:

| Included (typical) | Excluded (typical) |
|--------------------|--------------------|
| Repo materials + asserted original IP | Seller personal accounts / unrelated repos |
| Docs + diligence room at closing | Third-party dependency source under separate licenses |
| In-repo brand marks as assigned | Secrets without rotation plan |
| Know-how captured in docs | Fabricated revenue, user, or adoption metrics |

---

## 7. Suggested deal structures

| Structure | When it fits |
|-----------|--------------|
| Non-exclusive commercial license | Deploy/run under seat or environment terms |
| Exclusive field-of-use license | Buyer wants exclusivity; seller may retain entity |
| Asset / IP assignment | Buyer wants ownership of Materials outright |
| OEM / redistribution | Separate agreement â€” not implied here |

Commercial terms (price, earnouts, escrow) are negotiated under NDA with counsel.

---

## 8. Buyer diligence checklist

- [ ] Confirm Rightsholder identity and authority to sell/license
- [ ] Inventory Materials (`docs/acquisition/ASSET_INVENTORY.md`)
- [ ] Review IP posture (`IP_PROVENANCE.md`) and dependencies (`DEPENDENCY_INVENTORY.md`)
- [ ] Run evaluation script (`BUYER_EVALUATION.md`)
- [ ] Review risks (`RISK_REGISTER.md`)
- [ ] Agree transfer scope (`TRANSFER_MANIFEST.md`) and handoff (`HANDOFF_CHECKLIST.md`)
- [ ] Supersede root `LICENSE` at closing via definitive agreement

---

## 9. Related documents

| Document | Purpose |
|----------|---------|
| `LICENSE` | Proprietary â€” no default grant |
| `docs/acquisition/README.md` | Data-room index |
| `docs/acquisition/EXECUTIVE_SUMMARY.md` | One-page thesis |
| `README.md` | Product overview |
| `SECURITY.md` | Vulnerability reporting |
| `COMMERCIAL.md` | Licensing contact path |
| `.github/FUNDING.yml` | Sponsors / thanks.dev |

---

## 10. Disclaimer

This package is informational and **does not** create a binding offer, grant of rights, or investment advice. Engage counsel for any transaction.

---

*Document version: 2.0.0 / 2026-09-22 Â· Classification: acquisition briefing*
