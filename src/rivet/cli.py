from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

from .audit import ReleaseAuditor
from .capsule import Capsule, CapsuleInstaller, CapsuleValidator
from .cluster import OfflineCluster
from .compatibility import CompatibilityMatrix, ResourceTierTester, RuntimeBenchmark
from .configuration import CURRENT_CONFIG_SCHEMA, ConfigLoader
from .continuum import ContinuumRuntime, ResourceSnapshot
from .diagnostics import Doctor, Preflight
from .driver import DriverRegistry
from .echomap import EchoMark
from .errors import RivetError
from .faults import FaultInjector
from .guard import RivetGuard
from .hardware import HardwareGraph
from .hardware_certification import HardwareCertifier
from .mission import MissionSpec
from .mission_ops import MissionDryRunner
from .motion_ir import MotionOp
from .perception import InsightEngine
from .pulse import PulseFabric
from .recorder import Recorder, ReplaySession, load_events, summarize, timeline
from .runtime import RobotRuntime
from .simulator import SimulatedRobot, SimulatedRobotDriver
from .support import CrashReporter, SupportBundle, system_info
from .synapse import SynapsePackage, SynapseStage
from .team import TeamCoordinator, TeamMember
from .vocation import QualificationState
from .vocation_runtime import default_vocation
from .verification import verify_installation
from .version import __version__


def build_runtime() -> RobotRuntime:
    runtime = RobotRuntime()
    runtime.register_simulator(SimulatedRobot())
    return runtime


def cmd_discover(_: argparse.Namespace) -> int:
    print(json.dumps(build_runtime().discover(), indent=2))
    return 0


def cmd_tree(_: argparse.Namespace) -> int:
    print(json.dumps(build_runtime().registry.tree(), indent=2))
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    runtime = build_runtime()
    recorder = Recorder(args.record) if args.record else None
    if recorder:
        recorder.attach(runtime.bus)
    try:
        grant = runtime.acquire_control("motion", "demo-controller", priority=500, ttl_s=5)
        left = runtime.acquire_lease("motion.left-wheel", "demo-controller", grant.token, ttl_s=0.25)
        right = runtime.acquire_lease("motion.right-wheel", "demo-controller", grant.token, ttl_s=0.25)
        left_state = runtime.command("motion.left-wheel", "velocity", 0.45, "demo-controller", grant.token, left.token)
        right_state = runtime.command("motion.right-wheel", "velocity", 0.44, "demo-controller", grant.token, right.token)
        print(json.dumps({"status": "moving", "left": left_state.to_dict(), "right": right_state.to_dict()}, indent=2))
        stopped = runtime.tick(time.monotonic() + 1.0)
        print(json.dumps({"status": "leases_expired", "stopped": stopped}, indent=2))
    finally:
        if recorder:
            recorder.close()
    if args.record:
        print(json.dumps({"recording": str(Path(args.record)), **summarize(args.record)}, indent=2))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    events = load_events(args.path)
    if args.summary:
        print(json.dumps(summarize(args.path), indent=2))
        return 0
    for event in events:
        print(f"{event['sequence']:>4} {event['type']:<18} {event['source']}: {json.dumps(event['payload'], sort_keys=True)}")
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    entries = timeline(args.path)
    if args.json:
        print(json.dumps(entries, indent=2, sort_keys=True))
    else:
        for entry in ReplaySession.load(args.path).timeline():
            print(entry.line())
    return 0


def cmd_record_start(args: argparse.Namespace) -> int:
    runtime = build_runtime()
    recorder = Recorder(args.path, metadata={"rivet_version": __version__, "mode": "simulator"})
    recorder.attach(runtime.bus)
    try:
        runtime.bus.publish("record.started", "recorder", {"path": str(args.path)})
        grant = runtime.acquire_control("motion", "record-demo", priority=500, ttl_s=5.0)
        lease = runtime.acquire_lease("motion.left-wheel", "record-demo", grant.token, ttl_s=1.0)
        runtime.command("motion.left-wheel", "velocity", 0.2, "record-demo", grant.token, lease.token)
        runtime.tick(lease.expires_at + 0.01)
    finally:
        recorder.close()
        runtime.close()
    print(json.dumps({"recording": str(args.path), **summarize(args.path)}, indent=2))
    return 0


def cmd_drivers(_: argparse.Namespace) -> int:
    registry = DriverRegistry()
    registry.register(SimulatedRobotDriver())
    print(json.dumps({"drivers": registry.infos(), "qualifications": registry.qualifications()}, indent=2, sort_keys=True))
    registry.close()
    return 0


def cmd_hardware_certify(args: argparse.Namespace) -> int:
    registry = DriverRegistry()
    registry.register(SimulatedRobotDriver())
    driver = registry.get(args.driver)
    report = HardwareCertifier().certify(driver)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.text())
    return 0 if report.passed else 1


def cmd_config_validate(args: argparse.Namespace) -> int:
    config = ConfigLoader().validate(args.path)
    print(json.dumps({"valid": True, "config": config.to_dict()}, indent=2, sort_keys=True))
    return 0


def cmd_config_migrate(args: argparse.Namespace) -> int:
    result = ConfigLoader().migrate(args.path, args.output)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


def cmd_pulse(_: argparse.Namespace) -> int:
    runtime = build_runtime()
    fabric = PulseFabric(runtime.bus)
    for path, health in runtime.health.capabilities.items():
        fabric.heartbeat(path, health=health.health)
    print(json.dumps(fabric.snapshot(), indent=2, sort_keys=True))
    runtime.close()
    return 0


def cmd_crash_inspect(args: argparse.Namespace) -> int:
    print(json.dumps(CrashReporter(args.directory).inspect(args.path), indent=2, sort_keys=True))
    return 0


def cmd_support_bundle(args: argparse.Namespace) -> int:
    runtime = build_runtime()
    report = verify_installation(scenarios=False)
    destination = SupportBundle().create(args.path, runtime, report.to_dict())
    runtime.close()
    print(json.dumps({"created": str(destination), "verification": report.ok}, indent=2))
    return 0 if report.ok else 1


def cmd_compatibility(_: argparse.Namespace) -> int:
    print(CompatibilityMatrix().text())
    return 0


def cmd_resources(_: argparse.Namespace) -> int:
    results = ResourceTierTester().run()
    print(json.dumps([result.to_dict() for result in results], indent=2, sort_keys=True))
    return 0 if all(result.passed for result in results) else 1


def cmd_benchmark(_: argparse.Namespace) -> int:
    results = RuntimeBenchmark().run(build_runtime())
    print(json.dumps([result.to_dict() for result in results], indent=2, sort_keys=True))
    return 0 if all(result.passed for result in results) else 1

def cmd_init(args: argparse.Namespace) -> int:
    config = ConfigLoader().write_default(args.path, args.robot_id)
    print(json.dumps({"created": str(args.path), "config": config.to_dict()}, indent=2))
    return 0


def cmd_version(args: argparse.Namespace) -> int:
    if not args.verbose:
        print(__version__)
        return 0
    details = system_info() | {
        "config_schema": CURRENT_CONFIG_SCHEMA,
        "protocol": "RVT/1",
        "driver_api": 1,
        "platform": platform.platform(),
    }
    print(json.dumps({"version": f"Rivet {__version__}", **details}, indent=2, sort_keys=True))
    return 0


def cmd_devices(_: argparse.Namespace) -> int:
    print(json.dumps(build_runtime().discover(), indent=2))
    return 0


def cmd_roles(_args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    evaluations = [vocation.roles.evaluate(role.role_id).to_dict() for role in vocation.catalog.list()]
    print(json.dumps(evaluations, indent=2))
    return 0


def cmd_skills(_args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    print(json.dumps(vocation.skills.status(), indent=2))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    if not args.simulate:
        raise ValueError("hardware adapters must be explicitly registered; use --simulate for the dependency-free backend")
    runtime = build_runtime()
    injector = FaultInjector(runtime)
    fault = injector.disconnect(args.fault) if args.fault else None
    print(json.dumps({"mode": "simulate", "capabilities": runtime.discover(), "fault": fault.to_dict() if fault else None, "active_faults": injector.active()}, indent=2))
    return 0


def build_phase2() -> tuple[RobotRuntime, ContinuumRuntime, HardwareGraph, RivetGuard, ResourceSnapshot]:
    runtime = build_runtime()
    continuum = ContinuumRuntime(runtime)
    graph = HardwareGraph()
    graph.add_node("raspberry-pi", "compute", {"model": "simulated-pi-5"})
    graph.add_node("motion-bus", "bus", {"transport": "simulated"})
    graph.add_node("left-wheel-driver", "device")
    graph.add_node("right-wheel-driver", "device")
    graph.link("raspberry-pi", "motion-bus")
    graph.link("motion-bus", "left-wheel-driver")
    graph.link("motion-bus", "right-wheel-driver")
    graph.attach_capability("left-wheel-driver", "motion.left-wheel")
    graph.attach_capability("right-wheel-driver", "motion.right-wheel")
    guard = RivetGuard(runtime)
    resources = ResourceSnapshot(1024, ram_used_percent=18.0, cpu_percent=22.0, temperature_c=49.0, gpu_memory_mb=128)
    return runtime, continuum, graph, guard, resources


def cmd_continuum_demo(_: argparse.Namespace) -> int:
    runtime, continuum, graph, guard, resources = build_phase2()
    profile = continuum.boot(resources)
    decision = continuum.evaluate_resources(resources)
    continuum.register_lifecycle("vision.front-camera")
    unloaded = continuum.lifecycle.unload_idle(time.monotonic() + 301.0)
    continuum.request_capability("vision.front-camera")
    grant = runtime.acquire_control("motion", "continuum-demo", priority=500, ttl_s=5.0)
    lease = runtime.acquire_lease("motion.left-wheel", "continuum-demo", grant.token, ttl_s=2.0)
    runtime.command("motion.left-wheel", "velocity", 0.35, "continuum-demo", grant.token, lease.token)
    guard.arm()
    guard.watch("continuum-demo", 0.25)
    guard.heartbeat("continuum-demo")
    guard.tick(time.monotonic() + 1.0)
    insight_engine = InsightEngine()
    insight = insight_engine.fuse("possible-object", (1.42, 0.81, 0.38), {"mmwave": 0.91, "thermal_gradient": 0.74, "ultrasound": 0.67})
    cluster = OfflineCluster(timeout_s=3.0)
    cluster.join("pi-main", "coordinator", "offline://pi-main")
    cluster.join("pi-vision", "perception", "offline://pi-vision")
    cluster.assign("object_detection", "pi-vision")
    cluster.migrate("object_detection", "pi-main")
    print(json.dumps({
        "profile": profile.to_dict(),
        "governor": decision.to_dict(),
        "lifecycle_unloaded_then_restored": unloaded,
        "guard": guard.status().to_dict(),
        "hardware_graph": graph.as_dict(),
        "observation": insight.to_dict(),
        "explanation": insight_engine.store.explain(insight.observation_id),
        "cluster": cluster.status(),
    }, indent=2))
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    runtime, _, graph, guard, resources = build_phase2()
    print(json.dumps(Doctor().run(runtime, graph, resources, guard).to_dict(), indent=2))
    return 0


def cmd_preflight(_args: argparse.Namespace) -> int:
    runtime, _, graph, guard, resources = build_phase2()
    report = Doctor().run(runtime, graph, resources, guard)
    print(json.dumps(Preflight().run(runtime, report).to_dict(), indent=2))
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    report = verify_installation(args.config, scenarios=args.scenarios)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.text())
    return 0 if report.ok else 1


def cmd_check_release(args: argparse.Namespace) -> int:
    report = ReleaseAuditor(Path.cwd()).run(run_tests=not args.skip_tests, run_build=not args.skip_build)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.text())
    return 0 if report.ok else 1


def cmd_nodes(_: argparse.Namespace) -> int:
    cluster = OfflineCluster()
    cluster.join("pi-main", "coordinator", "offline://pi-main")
    cluster.join("pi-vision", "perception", "offline://pi-vision")
    cluster.join("pi-io", "hardware", "offline://pi-io")
    print(json.dumps(cluster.status(), indent=2))
    return 0


def build_phase3() -> tuple[ContinuumRuntime, Any]:
    _, continuum, _, _, _ = build_phase2()
    return continuum, default_vocation(continuum)


def authorize_role(vocation: Any, role_id: str) -> Any:
    vocation.roles.evaluate(role_id)
    vocation.roles.adopt(role_id)
    vocation.roles.train(role_id)
    vocation.roles.validate(role_id)
    return vocation.roles.authorize(role_id, "operator-demo")


def cmd_vocation_demo(_: argparse.Namespace) -> int:
    continuum, vocation = build_phase3()
    role = authorize_role(vocation, "search-rescue")
    passport = vocation.passport("atlas-07", "raspberry-pi-5", primary_role="search-rescue", secondary_roles=("inspection", "mapping"), restrictions=("medical-procedures", "hazardous-materials"))
    qualification = passport.issue("navigation.indoor", vocation.skills.level("navigation.indoor"), QualificationState.VALIDATED, "RivetBench-NAV-01", vocation.signer, timestamp=None)
    package = SynapsePackage("grasp-cylinder.syn", "manipulation.general", "1.0", "grasp and lift a cylindrical object", ("approach", "align", "close", "verify-grip", "lift"), ("vision.front-camera",), ("slip", "occlusion"), ("motion.left-wheel",), ("SIM-MANIP-01",), {"source": "atlas-mentor"})
    vocation.synapses.import_package(package)
    vocation.synapses.adapt(package.package_id, ("motion.left-wheel", "vision.front-camera"))
    vocation.synapses.advance(package.package_id, SynapseStage.SIMULATED, {"runs": 40, "success_rate": 0.9})
    vocation.synapses.advance(package.package_id, SynapseStage.PHYSICALLY_VALIDATED, {"runs": 5, "operator": "operator-demo"})
    plan = vocation.motion_compiler.compile("grasp-demo", (MotionOp("grasp", object_id="obj-481", constraints={"max_force_n": 8, "clearance_mm": 20}, verification={"require_contact": True}),), "simulated-rover", package.skill_id)
    insight = InsightEngine().fuse("slippery-floor", (4.0, 2.0), {"wheel_encoder": 0.91, "imu": 0.87})
    vocation.echo_map.record(EchoMark((4.0, 2.0), "slippery-floor", 0.91, ("wheel_encoder", "imu"), insight.clock, {"wheel_slip": "high", "lighting": "normal"}, {"encoder_divergence": 0.91}))
    mission = MissionSpec("rescue-042", "search building sector B", "search-rescue", {"navigation.indoor": 0.7, "search.thermal": 0.75}, {"avoid": ["restricted_zones"]}, {"coverage": 0.95})
    mission_view = vocation.mission_explain(mission)
    cluster = OfflineCluster()
    cluster.join("pi-main", "coordinator", "offline://pi-main")
    vocation.team = TeamCoordinator(cluster)
    assignment = vocation.team.organize(mission, (TeamMember("atlas-07", ("search-rescue",), {"navigation.indoor": 0.94, "search.thermal": 0.86}, 83, True, "pi-main"), TeamMember("atlas-08", ("inspection",), {"navigation.indoor": 0.72, "search.thermal": 0.40}, 91, True, "pi-main")))
    print(json.dumps({"role": role.to_dict(), "passport": passport.export(), "qualification_verified": vocation.signer.verify({"skill_id": qualification.skill_id, "score": qualification.score, "state": qualification.state.value, "validator": qualification.validator, "timestamp": qualification.timestamp}, qualification.signature), "synapse": vocation.synapses.status(), "motion_plan": plan.to_dict(), "mission": mission_view, "echo_map": vocation.echo_map.explain((4.0, 2.0)), "team_assignment": assignment.to_dict()}, indent=2))
    return 0


def cmd_role_evaluate(args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    print(json.dumps(vocation.roles.evaluate(args.role).to_dict(), indent=2))
    return 0


def cmd_role_adopt(args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    print(json.dumps(vocation.roles.adopt(args.role).to_dict(), indent=2))
    return 0


def cmd_skill_explain(args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    print(json.dumps(vocation.skills.explain(args.skill, args.required), indent=2))
    return 0


def cmd_skill_train(args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    print(json.dumps(vocation.skills.curriculum(args.skill).to_dict(), indent=2))
    return 0


def cmd_passport_export(_args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    passport = vocation.passport("atlas-07", "raspberry-pi-5", primary_role="inspection", secondary_roles=("mapping",), restrictions=("medical-procedures",))
    passport.issue("inspection.structural", vocation.skills.level("inspection.structural"), QualificationState.TRAINED, "RivetBench-INSPECT-01", vocation.signer)
    print(json.dumps(passport.export(), indent=2))
    return 0


def cmd_mission_explain(args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    authorize_role(vocation, args.role)
    mission = MissionSpec(args.mission_id, args.goal, args.role, {"navigation.indoor": 0.7}, {"avoid": ["humans"]}, {"coverage": 0.95})
    print(json.dumps(vocation.mission_explain(mission), indent=2))
    return 0


def cmd_mission_dry_run(args: argparse.Namespace) -> int:
    continuum, vocation = build_phase3()
    authorize_role(vocation, args.role)
    mission = MissionSpec(args.mission_id, args.goal, args.role, {"navigation.indoor": 0.7})
    plan = vocation.planner.decompose(mission)
    admission = vocation.admission.check(mission)
    report = MissionDryRunner().evaluate(mission, plan, admission, continuum.runtime)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(report.text())
    continuum.runtime.close()
    return 0 if report.ok else 1


def cmd_capsule_install(args: argparse.Namespace) -> int:
    capsule = Capsule.load(args.path)
    runtime = build_runtime()
    _, vocation = build_phase3()
    available = {capability.path for capability in runtime.registry.list()} | {role.role_id for role in vocation.catalog.list()}
    validation = CapsuleValidator().validate(capsule, available)
    if not validation.ok:
        print(json.dumps(validation.to_dict(), indent=2, sort_keys=True))
        runtime.close()
        return 1
    destination = CapsuleInstaller(args.directory).install(capsule, available)
    runtime.close()
    print(json.dumps({"installed": str(destination), "validation": validation.to_dict()}, indent=2, sort_keys=True))
    return 0

def cmd_team_organize(_args: argparse.Namespace) -> int:
    _, vocation = build_phase3()
    cluster = OfflineCluster()
    cluster.join("pi-main", "coordinator", "offline://pi-main")
    vocation.team = TeamCoordinator(cluster)
    mission = MissionSpec("beam-17", "move supplies to Area C", required_skills={"payload.transport": 0.8})
    members = (TeamMember("atlas-01", ("construction",), {"payload.transport": 0.61}, 74, True, "pi-main"), TeamMember("atlas-02", ("logistics",), {"payload.transport": 0.94}, 83, True, "pi-main"))
    print(json.dumps({"assignment": vocation.team.organize(mission, members).to_dict(), "cluster": cluster.status()}, indent=2))
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(prog="rivet", description="Rivet adaptive robot runtime and Vocation platform")
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="create a local JSON robot configuration").add_argument("path", nargs="?", type=Path, default=Path("rivet.json"))
    init_parser = commands.choices["init"]
    init_parser.add_argument("--robot-id", default="rover-demo")
    init_parser.set_defaults(func=cmd_init)
    version = commands.add_parser("version", help="print the Rivet version and runtime details")
    version.add_argument("--verbose", action="store_true", help="include Python, platform, schema, protocol, and driver API details")
    version.set_defaults(func=cmd_version)
    commands.add_parser("devices", help="list registered devices and capabilities").set_defaults(func=cmd_devices)
    commands.add_parser("roles", help="evaluate available default roles").set_defaults(func=cmd_roles)
    commands.add_parser("skills", help="list default skill evidence").set_defaults(func=cmd_skills)
    run = commands.add_parser("run", help="run a robot backend")
    run.add_argument("--simulate", action="store_true", help="use the dependency-free simulator")
    run.add_argument("--fault", help="inject a simulated device disconnect")
    run.set_defaults(func=cmd_run)
    commands.add_parser("discover", help="list registered capability contracts").set_defaults(func=cmd_discover)
    commands.add_parser("tree", help="show the device tree").set_defaults(func=cmd_tree)
    commands.add_parser("drivers", help="list drivers and qualification evidence").set_defaults(func=cmd_drivers)
    hardware = commands.add_parser("hardware", help="run hardware qualification checks")
    hardware_commands = hardware.add_subparsers(dest="hardware_command", required=True)
    certify = hardware_commands.add_parser("certify")
    certify.add_argument("driver", nargs="?", default="simulator")
    certify.add_argument("--json", action="store_true")
    certify.set_defaults(func=cmd_hardware_certify)
    config = commands.add_parser("config", help="validate and migrate versioned configuration")
    config_commands = config.add_subparsers(dest="config_command", required=True)
    config_validate = config_commands.add_parser("validate")
    config_validate.add_argument("path", type=Path)
    config_validate.set_defaults(func=cmd_config_validate)
    config_migrate = config_commands.add_parser("migrate")
    config_migrate.add_argument("path", type=Path)
    config_migrate.add_argument("--output", type=Path)
    config_migrate.set_defaults(func=cmd_config_migrate)
    demo = commands.add_parser("demo", help="run the simulator and safety demo")
    demo.add_argument("--record", metavar="PATH", help="write a JSONL black-box recording")
    demo.set_defaults(func=cmd_demo)
    replay = commands.add_parser("replay", help="inspect or replay a JSONL flight recording")
    replay.add_argument("path", type=Path)
    replay.add_argument("--summary", action="store_true")
    replay.set_defaults(func=cmd_replay)
    timeline_parser = commands.add_parser("timeline", help="inspect an ordered recording timeline")
    timeline_parser.add_argument("path", type=Path)
    timeline_parser.add_argument("--json", action="store_true")
    timeline_parser.set_defaults(func=cmd_timeline)
    record = commands.add_parser("record", help="create a deterministic simulator flight recording")
    record_commands = record.add_subparsers(dest="record_command", required=True)
    record_start = record_commands.add_parser("start")
    record_start.add_argument("path", type=Path)
    record_start.set_defaults(func=cmd_record_start)
    commands.add_parser("continuum-demo", help="run the adaptive Continuum runtime demo").set_defaults(func=cmd_continuum_demo)
    doctor = commands.add_parser("doctor", help="run Rivet system diagnostics")
    doctor.add_argument("--verbose", action="store_true", help="include detailed check output")
    doctor.set_defaults(func=cmd_doctor)
    commands.add_parser("preflight", help="validate the robot before enabling motion").set_defaults(func=cmd_preflight)
    commands.add_parser("pulse", help="show component heartbeat and health signals").set_defaults(func=cmd_pulse)
    commands.add_parser("compatibility", help="show platform support boundaries").set_defaults(func=cmd_compatibility)
    commands.add_parser("resource-test", help="exercise constrained resource profiles").set_defaults(func=cmd_resources)
    benchmark = commands.add_parser("benchmark", help="run bounded runtime performance checks")
    benchmark_commands = benchmark.add_subparsers(dest="benchmark_command", required=True)
    benchmark_commands.add_parser("runtime").set_defaults(func=cmd_benchmark)
    crash = commands.add_parser("crash", help="inspect persisted crash reports")
    crash_commands = crash.add_subparsers(dest="crash_command", required=True)
    crash_inspect = crash_commands.add_parser("inspect")
    crash_inspect.add_argument("path", nargs="?", default="latest")
    crash_inspect.add_argument("--directory", type=Path)
    crash_inspect.set_defaults(func=cmd_crash_inspect)
    support = commands.add_parser("support", help="create a sanitized support bundle")
    support_commands = support.add_subparsers(dest="support_command", required=True)
    support_bundle = support_commands.add_parser("bundle")
    support_bundle.add_argument("path", nargs="?", type=Path, default=Path("rivet-support.zip"))
    support_bundle.set_defaults(func=cmd_support_bundle)
    verify = commands.add_parser("verify", help="run the end-to-end installation verification pipeline")
    verify.add_argument("--config", type=Path, help="validate a specific JSON robot configuration")
    verify.add_argument("--json", action="store_true", help="emit a machine-readable report")
    verify.add_argument("--no-scenarios", dest="scenarios", action="store_false", help="skip the 18 simulator scenarios")
    verify.set_defaults(func=cmd_verify, scenarios=True)
    release = commands.add_parser("check-release", help="run the strict release quality gate")
    release.add_argument("--skip-tests", action="store_true", help="skip pytest only for local audit debugging")
    release.add_argument("--skip-build", action="store_true", help="skip package build only for local audit debugging")
    release.add_argument("--json", action="store_true", help="emit a machine-readable report")
    release.set_defaults(func=cmd_check_release)
    commands.add_parser("nodes", help="show the offline cluster node registry").set_defaults(func=cmd_nodes)
    commands.add_parser("vocation-demo", help="run the Vocation role, skill, mission, and passport demo").set_defaults(func=cmd_vocation_demo)

    role = commands.add_parser("role", help="evaluate or adopt a robot role")
    role_commands = role.add_subparsers(dest="role_command", required=True)
    role_evaluate = role_commands.add_parser("evaluate")
    role_evaluate.add_argument("role", nargs="?", default="search-rescue")
    role_evaluate.set_defaults(func=cmd_role_evaluate)
    role_adopt = role_commands.add_parser("adopt")
    role_adopt.add_argument("role", nargs="?", default="search-rescue")
    role_adopt.set_defaults(func=cmd_role_adopt)

    skill = commands.add_parser("skill", help="inspect or train a competency")
    skill_commands = skill.add_subparsers(dest="skill_command", required=True)
    skill_explain = skill_commands.add_parser("explain")
    skill_explain.add_argument("skill", nargs="?", default="construction.drilling")
    skill_explain.add_argument("--required", type=float, default=0.75)
    skill_explain.set_defaults(func=cmd_skill_explain)
    skill_train = skill_commands.add_parser("train")
    skill_train.add_argument("skill", nargs="?", default="manipulation.general")
    skill_train.set_defaults(func=cmd_skill_train)

    passport = commands.add_parser("passport", help="export the robot capability passport")
    passport_commands = passport.add_subparsers(dest="passport_command", required=True)
    passport_commands.add_parser("export").set_defaults(func=cmd_passport_export)

    mission = commands.add_parser("mission", help="plan and explain a mission")
    mission_commands = mission.add_subparsers(dest="mission_command", required=True)
    mission_explain = mission_commands.add_parser("explain")
    mission_explain.add_argument("goal", nargs="?", default="search building sector B")
    mission_explain.add_argument("--role", default="search-rescue")
    mission_explain.add_argument("--mission-id", default="mission-demo")
    mission_explain.set_defaults(func=cmd_mission_explain)
    mission_run = mission_commands.add_parser("run", help="run a mission only when explicit dry-run mode is selected")
    mission_run.add_argument("goal", nargs="?", default="inspect building sector B")
    mission_run.add_argument("--role", default="inspection")
    mission_run.add_argument("--mission-id", default="mission-dry-run")
    mission_run.add_argument("--dry-run", action="store_true", required=True)
    mission_run.add_argument("--json", action="store_true")
    mission_run.set_defaults(func=cmd_mission_dry_run)

    capsule = commands.add_parser("capsule", help="validate and install portable robot bundles")
    capsule_commands = capsule.add_subparsers(dest="capsule_command", required=True)
    capsule_install = capsule_commands.add_parser("install")
    capsule_install.add_argument("path", type=Path)
    capsule_install.add_argument("--directory", type=Path, default=Path(".rivet"))
    capsule_install.set_defaults(func=cmd_capsule_install)

    team = commands.add_parser("team", help="organize a qualified robot team")
    team_commands = team.add_subparsers(dest="team_command", required=True)
    team_commands.add_parser("organize").set_defaults(func=cmd_team_organize)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except (RivetError, OSError, ValueError) as exc:
        print(f"rivet: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
