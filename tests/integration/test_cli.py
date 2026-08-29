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


def test_version_verbose_and_driver_commands(capsys):
    assert main(["version", "--verbose"]) == 0
    assert "Rivet 1.2.0" in capsys.readouterr().out
    assert main(["drivers"]) == 0
    assert "SIMULATED" in capsys.readouterr().out


def test_dry_run_command_does_not_emit_hardware_commands(capsys):
    assert main(["mission", "run", "inspect zone A", "--role", "inspection", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "No hardware commands were executed." in output
