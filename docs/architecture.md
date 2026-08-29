# Rivet Vocation architecture

## Composition boundary

Rivet is intentionally layered:

```text
VocationRuntime
├── RoleCatalog / RoleManager
├── SkillGraph / RivetBench
├── SynapseRegistry
├── Passport records
├── MissionPlanner / TeamCoordinator
└── ContinuumRuntime
    ├── profiles / Governor / lifecycle
    ├── perception / EchoMap / cluster
    └── RobotRuntime
        ├── capabilities / EventBus
        ├── authority / actuator leases
        └── RivetGuard / safe state
```

`RobotRuntime` remains the only low-level command boundary. `ContinuumRuntime` remains the Phase II resource/perception composition layer. `VocationRuntime` adds role, competence, transfer, mission, and team policy without turning those concepts into fake hardware capabilities.

## Roles and qualifications

`RoleSpec` declares required and optional skills, required hardware, permitted/prohibited actions, safety policy, and mission priorities. `RoleManager.evaluate()` scores the robot against actual registered capability paths and SkillGraph levels.

Role state is explicit:

```text
CANDIDATE → TRAINED → VALIDATED → AUTHORIZED
```

Adoption creates a candidate role. Training, validation, and operator authorization are separate transitions. A role state is not a `RobotRuntime` authority token and cannot bypass `RivetGuard`, preflight, actuator leases, or emergency stop.

Dynamic transitions use the same rule: only an authorized role can become active. A production role policy should add operator identity, environment constraints, and signed approval records.

## SkillGraph

`SkillRecord` retains level, attempts, successes, simulator runs, validation date, dependencies, and history. Prerequisites are resolved recursively and `SkillGraph.explain()` reports missing or unavailable nodes.

Training is represented as a curriculum rather than an unsafe automatic executor. `record_result()` updates evidence-backed confidence. `decay()` lowers affected levels after a hardware/calibration change and records why. `RivetBench` registers benchmark definitions and writes benchmark evidence back into the graph.

This prototype keeps graph state in memory. A persistent skill registry should version records, sign validation events, and preserve immutable history.

## Synapse and embodiment

`SynapsePackage` transfers intent-level knowledge:

- motion primitives;
- sensor requirements;
- failure modes;
- hardware assumptions;
- validation tests;
- provenance.

A receiving robot progresses through a strict sequence:

```text
IMPORTED → ADAPTED → SIMULATED → PHYSICALLY_VALIDATED → CERTIFIED
```

Import or adaptation never implies qualification. `MotionOp` and `MotionPlan` describe intent and constraints rather than joint angles. `EmbodimentCompiler` creates a body-specific plan, and `MotionExecutor` is the only Vocation adapter that can call the lower runtime; it uses the existing authority/lease command signature.

The prototype does not execute a training environment or infer arbitrary embodiment mappings. Those are future adapters.

## Passport and validation records

`AgentPassport` exports platform, roles, restrictions, and qualification records. `PassportSigner` uses HMAC-SHA256 in the dependency-free prototype. `PassportVerifier` validates the canonical record payload.

The signed record is an auditable validation statement, not a cryptographic replacement for operator authorization, hardware interlocks, or guard state. Production identity should use device keys, rotation, revocation, validity windows, and an external validation authority.

## Missions and teams

`MissionSpec` contains a goal, required role/skills, constraints, success criteria, and timeout. `MissionPlanner` decomposes common inspection, transport, and search goals into skill-bearing steps. `MissionAdmission` requires required skill levels and an authorized required role. `MissionExplainer` exposes the reasons, missing skills, and planned steps.

`TeamCoordinator` ranks available `TeamMember` records by competence, role fit, battery, and availability. When configured with `OfflineCluster`, it also places the mission workload on the member's healthy node. The coordinator does not mutate cluster node roles and does not replace heartbeat or Guard policy.

## EchoMap

`EchoMap` is a temporal spatial experience field, separate from Phase II `WorldModel`:

```text
Observation / sensor evidence
          │
          ▼
      EchoMark
  location + confidence
  source IDs + clock
  environment + evidence
          │
          ▼
      local query/explain
```

An EchoMark can describe wheel slip, radio quality, lighting, thermal interference, sensor reliability, or traversability. It preserves the originating `ClockStamp` and evidence fields so a robot can explain why a route was considered risky.

## Event and replay model

Vocation transitions use the existing synchronous `EventBus` when a `RoleManager` is given the runtime bus. New event domains include `role.evaluated`, `role.adopted`, `role.trained`, `role.validated`, `role.authorized`, and `role.transitioned`. Future Synapse, mission, team, and EchoMap mutations should use the same JSON-compatible event contract so the existing recorder can capture them.

## Current CLI surface

```text
rivet vocation-demo
rivet role evaluate [role]
rivet role adopt [role]
rivet skill explain [skill] [--required LEVEL]
rivet skill train [skill]
rivet passport export
rivet mission explain [goal] [--role ROLE]
rivet team organize
```

The existing `discover`, `tree`, `demo`, `replay`, `continuum-demo`, `doctor`, `preflight`, and `nodes` commands remain unchanged.

## Scope boundaries and future integration

The prototype is deliberately offline and dependency-free. It does not include:

- YAML manifest parsing or a remote role/skill registry;
- real training simulators or autonomous dangerous-skill certification;
- hardware-backed cryptographic identities;
- authenticated fleet scheduling;
- process-isolated Guard or mission workers;
- physical embodiment drivers;
- covert surveillance, medical-procedure execution, hazardous-material control, or radiation generation.

Those integrations must preserve the distinction between declared competence, validated qualification, operator authorization, and low-level safety authority.
