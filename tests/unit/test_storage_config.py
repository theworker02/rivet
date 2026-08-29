from pathlib import Path

from rivet.configuration import ConfigLoader
from rivet.storage import JsonStore


def test_config_and_atomic_store(tmp_path: Path):
    config_path = tmp_path / "rivet.json"
    config = ConfigLoader().write_default(config_path, "atlas-test")
    assert ConfigLoader().load(config_path).robot_id == config.robot_id
    store = JsonStore(tmp_path / "state.json")
    store.save({"skills": {"navigation.indoor": 0.9}})
    assert store.load()["skills"]["navigation.indoor"] == 0.9
