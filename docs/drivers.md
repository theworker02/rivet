# Hardware support and driver qualification

Rivet 1.2.0 distinguishes declaration from evidence. `rivet drivers` shows registered driver metadata and qualification checks:

```bat
python -m rivet drivers
```

Qualification states are:

- `EXPERIMENTAL` — contract exists but evidence is incomplete.
- `SIMULATED` — deterministic simulator coverage exists; this is never hardware certification.
- `TESTED` — discovery, command/safe behavior, and integration checks pass for the declared environment.
- `HARDWARE-VERIFIED` — a reviewed hardware conformance report exists for a specific board, wiring, platform, and driver version.

Every driver should declare its capability types, version, platforms, buses, and evidence:

```python
DriverInfo(
    "bno085", "1", ("imu.9dof",), False,
    "TESTED", ("raspberry-pi",), ("i2c",),
    {"simulation": True, "integration": True, "hardware": False},
)
```

Use `rivet hardware certify <driver>` for the conformance runner. It checks detection, initialization, reads, safe behavior, invalid data handling, and shutdown. A simulator report is expected to remain `SIMULATED`; do not turn it into a hardware claim.

A driver must preserve typed capability contracts, the runtime authority/lease boundary, bounded recovery, and an idempotent safe state. Physical emergency-stop and watchdog behavior must be independently reviewed.
