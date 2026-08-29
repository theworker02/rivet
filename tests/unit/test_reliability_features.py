import json
from pathlib import Path

import pytest

from rivet.capsule import Capsule, CapsuleValidator
from rivet.compatibility import ResourceTierTester
from rivet.configuration import ConfigLoader
from rivet.driver import DriverRegistry
from rivet.hardware_certification import HardwareCertifier
from rivet.mission import MissionSpec, MissionPlanner
from rivet.mission_ops import MissionCheckpoint, MissionCheckpointStore, MissionTransaction
from rivet.recorder import Recorder, ReplaySession, timeline
from rivet.simulator import SimulatedRobot, SimulatedRobotDriver
from rivet.units import Distance, Temperature


def test_units_contracts_and_driver_qualification():
    assert Distance(5, "m").to("cm").value == 500
    assert round(Temperature(0, "C").to("K").value, 2) == 273.15
    registry = DriverRegistry()
    registry.register(SimulatedRobotDriver())
    assert registry.qualify("simulator").status == "SIMULATED"
    report = HardwareCertifier().certify(registry.get("simulator"))
    assert not report.passed
    assert any(check.name == "hardware evidence" for check in report.checks)


def test_health_recovery_and_recorder_replay(tmp_path: Path):
    from rivet.runtime import RobotRuntime

    runtime = RobotRuntime()
    runtime.register_simulator(SimulatedRobot())
    runtime.health.mark_failed("perception.imu", "test fault")
    assert runtime.health.status()["perception.imu"]["state"] == "FAILED"
    runtime.health.mark_recovered("perception.imu")
    assert runtime.health.status()["perception.imu"]["state"] == "HEALTHY"
    path = tmp_path / "session.rvt"
    recorder = Recorder(path)
    recorder.attach(runtime.bus)
    runtime.bus.publish("mission.started", "mission", {"mission_id": "m-1"})
    recorder.close()
    replay = ReplaySession.load(path)
    assert replay.replay() == 1
    assert timeline(path)[0]["event"] == "mission.started"


def test_config_migration_and_mission_compensation(tmp_path: Path):
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({"robot": "legacy", "capabilities": {"motion.left-wheel": {}}}), encoding="utf-8")
    result = ConfigLoader().migrate(path)
    assert result.source_version == 1
    assert json.loads(path.read_text(encoding="utf-8"))["rivet"] == 2
    assert ConfigLoader().load(path).robot_id == "legacy"
    released: list[str] = []
    transaction = MissionTransaction()
    transaction.reserve("tool", lambda: released.append("tool"))
    assert transaction.rollback() == ("tool",)
    assert released == ["tool"]
    checkpoint = MissionCheckpoint("m-1", 2, 3, "env")
    store = MissionCheckpointStore(tmp_path / "checkpoint.json")
    store.save(checkpoint)
    assert store.load() == checkpoint


def test_capsule_resources_and_mission_plan():
    capsule = Capsule("rover", "1.0", {"robot_id": "r"}, {"motion.left-wheel"}, {"inspection"})
    assert CapsuleValidator().validate(capsule, {"motion.left-wheel", "inspection"}).ok
    assert all(result.passed for result in ResourceTierTester().run())
    plan = MissionPlanner().decompose(MissionSpec("m", "inspect zone", "inspection"))
    assert len(plan.steps) == 3


def test_malformed_recording_is_rejected(tmp_path: Path):
    path = tmp_path / "broken.rvt"
    path.write_text('{"type":"state"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="missing"):
        ReplaySession.load(path)
