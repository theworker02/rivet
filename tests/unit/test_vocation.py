from rivet.cli import build_phase3
from rivet.passport import PassportVerifier
from rivet.synapse import SynapsePackage, SynapseStage
from rivet.vocation import QualificationState


def test_role_requires_explicit_authorization():
    _, vocation = build_phase3()
    assessment = vocation.roles.evaluate("search-rescue")
    assert assessment.state == QualificationState.CANDIDATE
    vocation.roles.adopt("search-rescue")
    vocation.roles.train("search-rescue")
    vocation.roles.validate("search-rescue")
    assert vocation.roles.assessments["search-rescue"].state == QualificationState.VALIDATED
    vocation.roles.authorize("search-rescue", "operator")
    assert vocation.roles.active_role == "search-rescue"


def test_skill_explanation_reports_unavailable_prerequisites():
    _, vocation = build_phase3()
    missing = vocation.skills.explain("construction.drilling", 0.75)["missing_prerequisites"]
    assert any(item.get("status") == "unavailable" for item in missing)


def test_synapse_requires_ordered_local_validation():
    _, vocation = build_phase3()
    package = SynapsePackage("test.syn", "manipulation.general", "1", "grasp", hardware_assumptions=("motion.left-wheel",))
    vocation.synapses.import_package(package)
    vocation.synapses.adapt(package.package_id, ("motion.left-wheel",))
    vocation.synapses.advance(package.package_id, SynapseStage.SIMULATED)
    vocation.synapses.advance(package.package_id, SynapseStage.PHYSICALLY_VALIDATED)
    vocation.synapses.advance(package.package_id, SynapseStage.CERTIFIED)
    assert vocation.synapses.transfers[package.package_id].stage == SynapseStage.CERTIFIED


def test_passport_record_verifies():
    _, vocation = build_phase3()
    passport = vocation.passport("atlas-test", "simulator")
    record = passport.issue("navigation.indoor", 0.9, QualificationState.VALIDATED, "test-suite", vocation.signer, timestamp=123.0)
    assert PassportVerifier(vocation.signer).verify(record)
