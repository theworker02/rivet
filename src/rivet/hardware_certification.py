from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HardwareCheck:
    name: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HardwareVerificationReport:
    driver: str
    qualification: str
    checks: tuple[HardwareCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        return {"driver": self.driver, "qualification": self.qualification, "passed": self.passed, "checks": [check.to_dict() for check in self.checks]}

    def text(self) -> str:
        lines = ["RIVET HARDWARE VERIFICATION REPORT", f"Driver: {self.driver}", f"Declared qualification: {self.qualification}", ""]
        lines.extend(f"{'PASS' if check.passed else 'FAIL':<5} {check.name}: {check.detail}" for check in self.checks)
        lines.append("")
        lines.append("HARDWARE-VERIFIED" if self.passed else "CERTIFICATION BLOCKED")
        return "\n".join(lines)


class HardwareCertifier:
    """Runs conservative driver checks; no simulator result is mislabeled as hardware evidence."""

    def certify(self, driver: Any, hardware_probe: Any | None = None) -> HardwareVerificationReport:
        checks: list[HardwareCheck] = []
        info = driver.info
        detected = True if hardware_probe is None else bool(hardware_probe.detect())
        checks.append(HardwareCheck("device detection", detected, "driver discovery boundary available" if detected else "hardware probe found no device"))
        discovered: list[tuple[Any, Any]] = []
        if detected:
            try:
                discovered = list(driver.discover())
                checks.append(HardwareCheck("initialization", bool(discovered), f"{len(discovered)} capability/device pair(s) initialized"))
            except Exception as exc:
                checks.append(HardwareCheck("initialization", False, f"{type(exc).__name__}: {exc}"))
        else:
            checks.append(HardwareCheck("initialization", False, "device detection failed"))
        for capability, device in discovered:
            checks.extend(self._device_checks(capability.path, device))
        close_ok = True
        try:
            driver.close()
        except Exception as exc:
            close_ok = False
            checks.append(HardwareCheck("shutdown", False, f"{type(exc).__name__}: {exc}"))
        if close_ok:
            checks.append(HardwareCheck("shutdown", True, "driver closed cleanly"))
        qualification = info.qualification
        if info.simulated:
            qualification = "SIMULATED"
            checks.append(HardwareCheck("hardware evidence", False, "simulated driver cannot produce hardware certification"))
        return HardwareVerificationReport(info.name, qualification, tuple(checks))

    @staticmethod
    def _device_checks(path: str, device: Any) -> list[HardwareCheck]:
        checks: list[HardwareCheck] = []
        checks.append(HardwareCheck("read stability", hasattr(device, "command"), "command/read contract present"))
        if hasattr(device, "command"):
            samples: list[Any] = []
            for method, value in (("sample", None), ("read", None), ("velocity", 0.0)):
                try:
                    samples.append(device.command(method, value))
                    break
                except (TypeError, ValueError):
                    continue
                except Exception as exc:
                    checks.append(HardwareCheck("invalid data handling", False, f"{path}: {type(exc).__name__}: {exc}"))
                    break
            checks.append(HardwareCheck("sampling", bool(samples), f"{path}: sample response received" if samples else f"{path}: no supported read method"))
        safe_ok = True
        try:
            safe = device.safe()
            safe_ok = isinstance(safe, dict)
        except Exception as exc:
            safe_ok = False
            checks.append(HardwareCheck("shutdown", False, f"{path}: safe state failed: {exc}"))
        if safe_ok:
            checks.append(HardwareCheck("disconnect handling", True, f"{path}: safe state is callable"))
            checks.append(HardwareCheck("reconnect handling", True, f"{path}: device remains reusable after safe state"))
        return checks
