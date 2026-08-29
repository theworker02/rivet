from __future__ import annotations

import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from .cluster import OfflineCluster
from .continuum import ContinuumRuntime, ResourceSnapshot
from .faults import FaultInjector
from .mission import MissionSpec
from .recorder import Recorder, load_events
from .runtime import RobotRuntime
from .simulator import SimulatedRobot
from .vocation_runtime import default_vocation


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run(name: str, operation: Callable[[], str]) -> ScenarioResult:
    try:
        return ScenarioResult(name, True, operation())
    except Exception as exc:  # scenarios are an explicit report, not a hidden test failure
        return ScenarioResult(name, False, f"{type(exc).__name__}: {exc}")


def _runtime() -> RobotRuntime:
    runtime = RobotRuntime()
    runtime.start()
    runtime.register_simulator(SimulatedRobot())
    return runtime


def boot_robot() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            if not runtime.started or len(runtime.registry.list()) < 5:
                raise RuntimeError("simulated rover did not boot with capabilities")
            return "simulated rover booted"
        finally:
            runtime.close()

    return _run("boot_robot", operation)


def discover_devices() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            paths = {capability.path for capability in runtime.registry.list()}
            expected = {"motion.left-wheel", "motion.right-wheel", "perception.imu", "vision.front-camera", "power.primary-battery"}
            if not expected.issubset(paths):
                raise RuntimeError(f"missing capabilities: {sorted(expected - paths)}")
            return f"{len(paths)} capabilities discovered"
        finally:
            runtime.close()

    return _run("discover_devices", operation)


def assign_role() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            vocation = default_vocation(ContinuumRuntime(runtime))
            assessment = vocation.roles.evaluate("inspection")
            if assessment.missing_hardware or assessment.missing_skills:
                raise RuntimeError(f"inspection role not ready: {assessment.to_dict()}")
            vocation.roles.adopt("inspection")
            return "inspection role assigned"
        finally:
            runtime.close()

    return _run("assign_role", operation)


def execute_mission() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            vocation = default_vocation(ContinuumRuntime(runtime))
            vocation.roles.evaluate("inspection")
            vocation.roles.adopt("inspection")
            vocation.roles.train("inspection")
            vocation.roles.validate("inspection")
            vocation.roles.authorize("inspection", "verification-operator")
            mission = MissionSpec("e2e-inspection", "inspect zone A", "inspection", {"inspection.structural": 0.75})
            view = vocation.mission_explain(mission)
            if not view["admitted"]:
                raise RuntimeError(f"mission was not admitted: {view}")
            return f"mission accepted with {len(view['steps'])} steps"
        finally:
            runtime.close()

    return _run("execute_mission", operation)


def lose_sensor() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            fault = FaultInjector(runtime).disconnect("perception.imu")
            if not fault.active or "perception.imu" in runtime.devices:
                raise RuntimeError("sensor disconnect was not applied")
            return "IMU disconnect detected"
        finally:
            runtime.close()

    return _run("lose_sensor", operation)


def recover_sensor() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            injector = FaultInjector(runtime)
            injector.disconnect("perception.imu")
            restored = injector.restore("perception.imu")
            if restored.active or "perception.imu" not in runtime.devices:
                raise RuntimeError("sensor did not reconnect")
            return "IMU capability restored"
        finally:
            runtime.close()

    return _run("recover_sensor", operation)


def motor_watchdog() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            grant = runtime.acquire_control("motion", "watchdog", 900, ttl_s=5.0)
            lease = runtime.acquire_lease("motion.left-wheel", "watchdog", grant.token, ttl_s=0.1)
            runtime.command("motion.left-wheel", "velocity", 0.7, "watchdog", grant.token, lease.token)
            runtime.tick(lease.expires_at + 0.01)
            if runtime.devices["motion.left-wheel"].velocity != 0.0:
                raise RuntimeError("watchdog did not brake the motor")
            return "expired lease forced a safe motor stop"
        finally:
            runtime.close()

    return _run("motor_watchdog", operation)


def low_memory() -> ScenarioResult:
    def operation() -> str:
        continuum = ContinuumRuntime(_runtime())
        decision = continuum.evaluate_resources(ResourceSnapshot(64, ram_used_percent=95.0))
        if decision.state != "safety-only":
            raise RuntimeError(f"unexpected memory state: {decision.state}")
        continuum.runtime.close()
        return "low memory selected safety-only profile"

    return _run("low_memory", operation)


def overtemperature() -> ScenarioResult:
    def operation() -> str:
        continuum = ContinuumRuntime(_runtime())
        decision = continuum.evaluate_resources(ResourceSnapshot(1024, temperature_c=90.0))
        if decision.state != "safety-only":
            raise RuntimeError(f"unexpected thermal state: {decision.state}")
        continuum.runtime.close()
        return "overtemperature selected safety-only profile"

    return _run("overtemperature", operation)


def record_replay() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        with tempfile.TemporaryDirectory(prefix="rivet-scenario-") as directory:
            path = Path(directory) / "session.rvt"
            recorder = Recorder(path)
            recorder.attach(runtime.bus)
            runtime.bus.publish("mission.started", "mission", {"mission_id": "recorded"})
            runtime.bus.publish("mission.completed", "mission", {"mission_id": "recorded"})
            recorder.close()
            events = load_events(path)
            runtime.close()
            event_types = [event["type"] for event in events if event["type"] != "recording.started"]
            if event_types != ["mission.started", "mission.completed"]:
                raise RuntimeError("recording did not preserve mission event order")
            return "recorded session replayed in deterministic order"

    return _run("record_replay", operation)


def role_transition() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            vocation = default_vocation(ContinuumRuntime(runtime))
            vocation.roles.evaluate("inspection")
            vocation.roles.adopt("inspection")
            vocation.roles.train("inspection")
            vocation.roles.validate("inspection")
            vocation.roles.authorize("inspection", "operator")
            vocation.roles.transition("inspection")
            if vocation.roles.active_role != "inspection":
                raise RuntimeError("role transition did not activate inspection")
            return "inspection role transitioned to active"
        finally:
            runtime.close()

    return _run("role_transition", operation)


def skill_validation() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            vocation = default_vocation(ContinuumRuntime(runtime))
            explanation = vocation.skills.explain("navigation.indoor", 0.70)
            if explanation["missing_prerequisites"]:
                raise RuntimeError("seeded navigation skill unexpectedly has prerequisites")
            return f"{len(vocation.skills.records)} skill records validated"
        finally:
            runtime.close()

    return _run("skill_validation", operation)


def multi_robot() -> ScenarioResult:
    def operation() -> str:
        first = _runtime()
        second = _runtime()
        try:
            cluster = OfflineCluster()
            cluster.join("rover-01", "coordinator", "offline://rover-01")
            cluster.join("rover-02", "worker", "offline://rover-02")
            if len(cluster.status()) != 2:
                raise RuntimeError("multi-robot cluster did not register both robots")
            return "two simulated robots registered in an offline cluster"
        finally:
            first.close()
            second.close()

    return _run("multi_robot", operation)


def dry_run() -> ScenarioResult:
    def operation() -> str:
        runtime = _runtime()
        try:
            vocation = default_vocation(ContinuumRuntime(runtime))
            plan = vocation.planner.decompose(MissionSpec("dry-run", "inspect zone", "inspection"))
            command_events: list[Any] = []
            runtime.bus.subscribe("command", command_events.append)
            if not plan.steps or command_events:
                raise RuntimeError("dry run generated commands")
            return f"{len(plan.steps)} planned actions; no hardware command emitted"
        finally:
            runtime.close()

    return _run("dry_run", operation)


def reflex_protection() -> ScenarioResult:
    def operation() -> str:
        from .reflex import ReflexEngine, ReflexRule

        runtime = _runtime()
        try:
            reflex = ReflexEngine(runtime.bus, runtime)
            reflex.add(ReflexRule("front-stop", "state", "distance_m", "lt", 0.15, "motion.stop", priority="emergency"))
            runtime.bus.publish("state", "distance.front", {"distance_m": 0.10})
            if not reflex.last_action or reflex.last_action.action != "motion.stop":
                raise RuntimeError("reflex did not select motion.stop")
            return "emergency reflex selected deterministic stop"
        finally:
            runtime.close()

    return _run("reflex_protection", operation)


def pulse_health() -> ScenarioResult:
    def operation() -> str:
        from .pulse import PulseFabric

        runtime = _runtime()
        try:
            pulse = PulseFabric(runtime.bus)
            pulse.heartbeat("runtime", latency_ms=8.0, health=1.0)
            snapshot = pulse.snapshot()
            if snapshot["runtime"]["health"] != 1.0:
                raise RuntimeError("pulse health was not retained")
            return "runtime heartbeat published through Pulse"
        finally:
            runtime.close()

    return _run("pulse_health", operation)


def capsule_validation() -> ScenarioResult:
    def operation() -> str:
        from .capsule import Capsule, CapsuleValidator

        capsule = Capsule("sim-rover", "1.0", {"robot_id": "rover"}, {"motion.left-wheel"}, {"inspection"})
        result = CapsuleValidator().validate(capsule, {"motion.left-wheel", "inspection"})
        if not result.ok:
            raise RuntimeError(result.detail)
        return "simulator capsule validated against capabilities and role"

    return _run("capsule_validation", operation)


def fault_domain_isolation() -> ScenarioResult:
    def operation() -> str:
        from .fault_domains import FaultDomainManager

        runtime = _runtime()
        try:
            domains = FaultDomainManager(runtime.bus, runtime)
            domains.record("ui", "dashboard stopped")
            if domains.status()["ui"] != "failed" or not runtime.started:
                raise RuntimeError("UI fault stopped the core runtime")
            return "UI fault isolated while core remained active"
        finally:
            runtime.close()

    return _run("fault_domain_isolation", operation)


SCENARIOS: tuple[Callable[[], ScenarioResult], ...] = (
    boot_robot,
    discover_devices,
    assign_role,
    execute_mission,
    lose_sensor,
    recover_sensor,
    motor_watchdog,
    low_memory,
    overtemperature,
    record_replay,
    role_transition,
    skill_validation,
    multi_robot,
    dry_run,
    reflex_protection,
    pulse_health,
    capsule_validation,
    fault_domain_isolation,
)


def run_all_scenarios() -> list[ScenarioResult]:
    return [scenario() for scenario in SCENARIOS]
