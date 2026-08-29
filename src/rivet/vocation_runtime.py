from __future__ import annotations

from typing import Any

from .echomap import EchoMap
from .mission import MissionAdmission, MissionExplainer, MissionPlanner, MissionSpec
from .motion_ir import EmbodimentCompiler, MotionExecutor
from .passport import AgentPassport, PassportSigner
from .skills import SkillGraph
from .synapse import SynapseRegistry
from .team import TeamCoordinator
from .vocation import RoleCatalog, RoleManager, RoleSpec


class VocationRuntime:
    """Vocation composition layer above ContinuumRuntime."""

    def __init__(self, continuum: Any, catalog: RoleCatalog | None = None, skills: SkillGraph | None = None, signer: PassportSigner | None = None) -> None:
        self.continuum = continuum
        self.catalog = catalog or RoleCatalog()
        self.skills = skills or SkillGraph()
        hardware = [cap.path for cap in continuum.runtime.registry.list()]
        self.roles = RoleManager(self.catalog, self.skills, hardware, continuum.runtime.bus)
        self.synapses = SynapseRegistry()
        self.echo_map = EchoMap()
        self.planner = MissionPlanner()
        self.admission = MissionAdmission(self.skills, self.roles)
        self.explainer = MissionExplainer()
        self.motion_compiler = EmbodimentCompiler()
        self.motion_executor = MotionExecutor(continuum.runtime)
        self.team = TeamCoordinator()
        self.signer = signer or PassportSigner(b"rivet-development-signing-key")
        self.passports: dict[str, AgentPassport] = {}

    def register_role(self, role: RoleSpec) -> None:
        self.catalog.register(role)

    def passport(self, agent_id: str, platform: str, **kwargs: Any) -> AgentPassport:
        passport = AgentPassport(agent_id, platform, **kwargs)
        self.passports[agent_id] = passport
        return passport

    def mission_explain(self, mission: MissionSpec) -> dict[str, Any]:
        plan = self.planner.decompose(mission)
        admission = self.admission.check(mission)
        return self.explainer.explain(mission, admission, plan)

    def status(self) -> dict[str, Any]:
        return {"roles": self.roles.status(), "skills": self.skills.status(), "synapses": self.synapses.status(), "echo_map": self.echo_map.status(), "passports": [passport.export() for passport in self.passports.values()], "team": self.team.status()}


def default_vocation(continuum: Any) -> VocationRuntime:
    vocation = VocationRuntime(continuum)
    seeded = {
        "navigation.indoor": 0.94,
        "inspection.structural": 0.76,
        "manipulation.general": 0.81,
        "mapping.local": 0.82,
        "search.thermal": 0.86,
        "payload.transport": 0.68,
    }
    for skill_id, level in seeded.items():
        vocation.skills.register(skill_id, initial_level=level)
    vocation.skills.register("construction.drilling", ("manipulation.general", "tool_alignment", "force_estimation", "workspace_safety", "emergency_stop_response"))
    vocation.register_role(RoleSpec("search-rescue", {"navigation.indoor": 0.70, "search.thermal": 0.75, "inspection.structural": 0.65}, required_hardware=("vision.front-camera", "perception.imu"), permitted_actions=("search", "report"), prohibited_actions=("medical-procedure",), mission_priorities=("victim-safety",)))
    vocation.register_role(RoleSpec("inspection", {"navigation.indoor": 0.70, "inspection.structural": 0.75}, required_hardware=("vision.front-camera", "perception.imu"), permitted_actions=("inspect", "report"), mission_priorities=("coverage",)))
    vocation.register_role(RoleSpec("reconnaissance", {"navigation.indoor": 0.70, "mapping.local": 0.70}, required_hardware=("vision.front-camera", "perception.imu"), prohibited_actions=("covert-surveillance",)))
    vocation.register_role(RoleSpec("construction", {"navigation.indoor": 0.70, "manipulation.general": 0.75, "payload.transport": 0.70}, required_hardware=("motion.left-wheel", "motion.right-wheel"), permitted_actions=("transport", "tool-use"), safety_policy={"human_clearance_required": True}))
    return vocation
