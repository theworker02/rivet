from __future__ import annotations

import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from .configuration import ConfigLoader, RobotConfig
from .continuum import ContinuumRuntime, ResourceSnapshot
from .driver import DriverRegistry
from .guard import RivetGuard
from .mission import MissionPlanner, MissionSpec
from .recorder import Recorder, load_events
from .runtime import RobotRuntime
from .scenarios import ScenarioResult, run_all_scenarios
from .simulator import SimulatedRobot, SimulatedRobotDriver
from .vocation_runtime import default_vocation


@dataclass(frozen=True)
class VerificationCheck:
    """One observable gate in the installation verification pipeline."""

    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerificationReport:
    """A truthful, machine-readable result of Rivet's end-to-end health check."""

    checks: tuple[VerificationCheck, ...]
    scenarios: tuple[ScenarioResult, ...] = ()

    @property
    def ok(self) -> bool:
        return all(check.ok for check in self.checks) and all(scenario.passed for scenario in self.scenarios)

    @property
    def scenarios_passed(self) -> int:
        return sum(scenario.passed for scenario in self.scenarios)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [check.to_dict() for check in self.checks],
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
            "scenario_count": {"passed": self.scenarios_passed, "total": len(self.scenarios)},
        }

    def text(self) -> str:
        lines = ["RIVET VERIFICATION", ""]
        for check in self.checks:
            status = "PASS" if check.ok else "FAIL"
            lines.append(f"{check.name:<28} {status}  {check.detail}")
        lines.extend(
            [
                "",
                f"End-to-end scenarios         {self.scenarios_passed} / {len(self.scenarios)}",
                "",
                "VERIFIED" if self.ok else "VERIFICATION FAILED",
            ]
        )
        if not self.ok:
            failed = [scenario for scenario in self.scenarios if not scenario.passed]
            if failed:
                lines.append("")
                lines.append("Failed scenarios:")
                lines.extend(f"- {scenario.name}: {scenario.detail}" for scenario in failed)
        return "\n".join(lines)


class VerificationRunner:
    """Runs the real local runtime path from configuration through shutdown."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        self.config_path = Path(config_path) if config_path else None

    def run(self, scenarios: bool = True) -> VerificationReport:
        checks: list[VerificationCheck] = []
        runtime: RobotRuntime | None = None
        driver_registry: DriverRegistry | None = None
        guard: RivetGuard | None = None
        continuum: ContinuumRuntime | None = None
        vocation: Any | None = None
        robot: SimulatedRobot | None = None
        discovered: list[tuple[Any, Any]] = []
        recorded_path: Path | None = None
        motion_grant: Any | None = None
        motion_left_lease: Any | None = None
        temporary: tempfile.TemporaryDirectory[str] | None = None

        def stage(name: str, operation: Callable[[], str]) -> None:
            try:
                checks.append(VerificationCheck(name, True, operation()))
            except Exception as exc:  # verification must report the failed gate, not hide it
                checks.append(VerificationCheck(name, False, f"{type(exc).__name__}: {exc}"))

        def validate_configuration() -> str:
            if self.config_path is None:
                config = RobotConfig("verification-rover")
            else:
                config = ConfigLoader().load(self.config_path)
            if not config.robot_id:
                raise ValueError("configuration has no robot id")
            return f"robot={config.robot_id}, platform={config.platform}"

        stage("Core Runtime", lambda: "verification pipeline ready")
        stage("Configuration", validate_configuration)

        def start_runtime() -> str:
            nonlocal runtime
            runtime = RobotRuntime()
            runtime.start()
            return "runtime started"

        stage("Runtime Startup", start_runtime)

        def discover_drivers() -> str:
            nonlocal driver_registry, robot, discovered
            if runtime is None:
                raise RuntimeError("runtime did not start")
            robot = SimulatedRobot()
            driver_registry = DriverRegistry()
            driver_registry.register(SimulatedRobotDriver(robot))
            discovered = driver_registry.discover("simulator")
            if len(discovered) != 3:
                raise RuntimeError(f"simulator driver discovered {len(discovered)} commandable devices; expected 3")
            return f"simulator driver discovered {len(discovered)} commandable devices"

        stage("Driver Discovery", discover_drivers)

        def register_capabilities() -> str:
            if runtime is None or robot is None:
                raise RuntimeError("driver discovery did not complete")
            for capability, device in discovered:
                runtime.register(capability, device)
            for capability in robot.static_capabilities:
                runtime.register(capability)
            count = len(runtime.registry.list())
            if count < 5:
                raise RuntimeError(f"only {count} capabilities registered")
            return f"{count} capabilities registered"

        stage("Capability Registry", register_capabilities)

        def initialize_safety() -> str:
            nonlocal guard
            if runtime is None:
                raise RuntimeError("runtime did not start")
            guard = RivetGuard(runtime)
            guard.arm()
            guard.watch("verification", 5.0)
            guard.heartbeat("verification")
            return "guard armed and heartbeat observed"

        stage("Safety Guard", initialize_safety)

        def load_roles() -> str:
            nonlocal continuum, vocation
            if runtime is None:
                raise RuntimeError("runtime did not start")
            continuum = ContinuumRuntime(runtime)
            continuum.boot(ResourceSnapshot(1024, ram_used_percent=20.0, temperature_c=42.0))
            vocation = default_vocation(continuum)
            if len(vocation.catalog.list()) < 4:
                raise RuntimeError("default role catalog is incomplete")
            return f"{len(vocation.catalog.list())} roles loaded"

        stage("Roles", load_roles)

        def validate_skills() -> str:
            if vocation is None:
                raise RuntimeError("roles did not load")
            records = vocation.skills.records
            if not records or any(not 0.0 <= record.level <= 1.0 for record in records.values()):
                raise RuntimeError("skill graph contains invalid levels")
            return f"{len(records)} skills validated"

        stage("Skills", validate_skills)

        def parse_mission() -> str:
            if vocation is None:
                raise RuntimeError("vocation did not load")
            mission = MissionSpec(
                "verification-mission",
                "inspect verification zone",
                "inspection",
                {"inspection.structural": 0.75},
            )
            plan = MissionPlanner().decompose(mission)
            if not plan.steps:
                raise RuntimeError("mission parser returned no steps")
            return f"{len(plan.steps)} mission steps parsed"

        stage("Mission Engine", parse_mission)

        def command_simulator() -> str:
            nonlocal motion_grant, motion_left_lease
            if runtime is None:
                raise RuntimeError("runtime did not start")
            motion_grant = runtime.acquire_control("motion", "verification", priority=900, ttl_s=5.0)
            motion_left_lease = runtime.acquire_lease("motion.left-wheel", "verification", motion_grant.token, ttl_s=1.0)
            right = runtime.acquire_lease("motion.right-wheel", "verification", motion_grant.token, ttl_s=1.0)
            runtime.command("motion.left-wheel", "velocity", 0.25, "verification", motion_grant.token, motion_left_lease.token)
            runtime.command("motion.right-wheel", "velocity", 0.25, "verification", motion_grant.token, right.token)
            return "both simulated motors accepted commands"

        stage("Simulation", command_simulator)

        def check_command_and_telemetry() -> str:
            nonlocal motion_left_lease
            if runtime is None or motion_grant is None or motion_left_lease is None:
                raise RuntimeError("simulation command stage did not complete")
            states: list[Any] = []
            runtime.bus.subscribe("state", states.append)
            motion_left_lease = runtime.renew_lease(motion_left_lease.token, ttl_s=1.0)
            state = runtime.command("motion.left-wheel", "velocity", 0.1, "verification", motion_grant.token, motion_left_lease.token)
            if not states or state.payload.get("rpm") != 18.0:
                raise RuntimeError("command did not produce expected telemetry")
            return f"command executed; {len(states)} state event(s) observed"

        stage("Command and Telemetry", check_command_and_telemetry)

        def record_events() -> str:
            nonlocal temporary, recorded_path
            if runtime is None:
                raise RuntimeError("runtime did not start")
            temporary = tempfile.TemporaryDirectory(prefix="rivet-verify-")
            recorded_path = Path(temporary.name) / "verification.rvt"
            recorder = Recorder(recorded_path)
            recorder.attach(runtime.bus)
            runtime.bus.publish("verification.marker", "verification", {"healthy": True})
            recorder.close()
            events = load_events(recorded_path)
            if not events:
                raise RuntimeError("recorder produced no events")
            return f"{len(events)} event(s) recorded"

        stage("Recorder", record_events)

        def replay_events() -> str:
            if recorded_path is None:
                raise RuntimeError("recording was not created")
            events = load_events(recorded_path)
            sequences = [int(event["sequence"]) for event in events]
            if sequences != sorted(sequences) or not any(event["type"] == "verification.marker" for event in events):
                raise RuntimeError("recording is not replayable in sequence order")
            return f"{len(events)} event(s) replay-ready"

        stage("Replay", replay_events)

        def shutdown_runtime() -> str:
            if runtime is None:
                raise RuntimeError("runtime did not start")
            runtime.close()
            if driver_registry is not None:
                driver_registry.close()
            if runtime.started:
                raise RuntimeError("runtime remained started after close")
            return "actuators safe; runtime and drivers closed"

        stage("Graceful Shutdown", shutdown_runtime)

        scenario_results = tuple(run_all_scenarios()) if scenarios else ()
        if temporary is not None:
            temporary.cleanup()
        return VerificationReport(tuple(checks), scenario_results)


def verify_installation(config_path: str | Path | None = None, scenarios: bool = True) -> VerificationReport:
    return VerificationRunner(config_path).run(scenarios=scenarios)
