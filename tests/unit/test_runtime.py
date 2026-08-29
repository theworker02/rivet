import pytest

from rivet.cli import build_runtime
from rivet.errors import AuthorityError, LeaseError


def test_motion_command_requires_authority_and_lease():
    runtime = build_runtime()
    with pytest.raises(AuthorityError):
        runtime.acquire_lease("motion.left-wheel", "tester", "missing")
    grant = runtime.acquire_control("motion", "tester", 500)
    lease = runtime.acquire_lease("motion.left-wheel", "tester", grant.token)
    state = runtime.command("motion.left-wheel", "velocity", 0.5, "tester", grant.token, lease.token)
    assert state.payload["rpm"] == 90.0


def test_expired_lease_brakes_motor():
    runtime = build_runtime()
    grant = runtime.acquire_control("motion", "tester", 500)
    lease = runtime.acquire_lease("motion.left-wheel", "tester", grant.token, ttl_s=0.1)
    runtime.command("motion.left-wheel", "velocity", 0.5, "tester", grant.token, lease.token)
    runtime.tick(lease.expires_at + 0.01)
    assert runtime.devices["motion.left-wheel"].rpm == 0.0
    with pytest.raises(LeaseError):
        runtime.leases.validate("motion.left-wheel", "tester", lease.token)
