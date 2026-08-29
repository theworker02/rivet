from dataclasses import dataclass

from rivet.driver import DriverInfo, DriverRegistry
from rivet.models import Capability


@dataclass
class FakeDriver:
    info: DriverInfo = DriverInfo("fake", "1.0", ("sensor.fake",), True)

    def discover(self):
        return [(Capability("sensor.fake", "sensor.fake"), FakeDevice())]

    def close(self):
        pass


class FakeDevice:
    def command(self, method, value):
        return {}

    def safe(self):
        return {}


def test_driver_registry_discovers_and_validates():
    registry = DriverRegistry()
    registry.register(FakeDriver())
    assert registry.discover("fake")[0][0].path == "sensor.fake"
    assert registry.infos()[0]["simulated"] is True
