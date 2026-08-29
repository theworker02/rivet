from rivet.scenarios import ScenarioResult, discover_devices


def run() -> ScenarioResult:
    return discover_devices()
