import pytest

from rivet.scenarios import (
    capsule_validation,
    dry_run,
    fault_domain_isolation,
    pulse_health,
    reflex_protection,
)
from .assign_role import run as assign_role_run
from .boot_robot import run as boot_robot_run
from .discover_devices import run as discover_devices_run
from .execute_mission import run as execute_mission_run
from .lose_sensor import run as lose_sensor_run
from .low_memory import run as low_memory_run
from .motor_watchdog import run as motor_watchdog_run
from .multi_robot import run as multi_robot_run
from .overtemperature import run as overtemperature_run
from .record_replay import run as record_replay_run
from .recover_sensor import run as recover_sensor_run
from .role_transition import run as role_transition_run
from .skill_validation import run as skill_validation_run


SCENARIOS = (
    assign_role_run,
    boot_robot_run,
    discover_devices_run,
    execute_mission_run,
    lose_sensor_run,
    recover_sensor_run,
    motor_watchdog_run,
    low_memory_run,
    overtemperature_run,
    record_replay_run,
    role_transition_run,
    skill_validation_run,
    multi_robot_run,
    dry_run,
    reflex_protection,
    pulse_health,
    capsule_validation,
    fault_domain_isolation,
)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda scenario: scenario.__name__)
def test_end_to_end_scenario(scenario):
    result = scenario()
    assert result.passed, result.detail
