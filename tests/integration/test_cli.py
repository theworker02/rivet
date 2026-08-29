from pathlib import Path

from rivet.cli import main


def test_version_command(capsys):
    assert main(["version"]) == 0
    assert capsys.readouterr().out.strip() == "1.2.0"


def test_init_writes_json_config(tmp_path: Path):
    target = tmp_path / "rivet.json"
    assert main(["init", str(target), "--robot-id", "test-rover"]) == 0
    assert '"test-rover"' in target.read_text(encoding="utf-8")


def test_simulation_command_reports_fault(capsys):
    assert main(["run", "--simulate", "--fault", "motion.left-wheel"]) == 0
    assert "SIMULATED" not in capsys.readouterr().out
