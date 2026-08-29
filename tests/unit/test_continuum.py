from rivet.continuum import Governor, ResourceSnapshot, RuntimeClassifier


def test_profiles_classify_host_memory():
    classifier = RuntimeClassifier()
    assert classifier.classify(ResourceSnapshot(64)).name == "nano"
    assert classifier.classify(ResourceSnapshot(256)).name == "core"
    assert classifier.classify(ResourceSnapshot(1024)).name == "full"


def test_governor_escalates_thermal_pressure():
    decision = Governor().evaluate(ResourceSnapshot(256, temperature_c=88))
    assert decision.state == "safety-only"
    assert "pause_noncritical_agents" in decision.actions


def test_lifecycle_unloads_optional_capability():
    clock = iter([10.0, 10.0, 10.0])
    lifecycle = __import__("rivet.continuum", fromlist=["CapabilityLifecycle"]).CapabilityLifecycle(5, lambda: next(clock))
    lifecycle.register("vision.front-camera")
    assert lifecycle.unload_idle(16.0) == ["vision.front-camera"]
