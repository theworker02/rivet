from rivet.cli import build_runtime
from rivet.faults import FaultInjector


def test_disconnect_removes_commandable_device_until_restore():
    runtime = build_runtime()
    injector = FaultInjector(runtime)
    injector.disconnect("motion.left-wheel")
    assert "motion.left-wheel" not in runtime.devices
    injector.restore("motion.left-wheel")
    assert "motion.left-wheel" in runtime.devices
