# Support

Use the documentation and simulator first:

```bat
python -m rivet doctor --verbose
python -m rivet run --simulate
python -m pytest
```

For a reproducible issue, include Rivet version, Python version, operating system, command, simulator output, and the smallest relevant configuration. Never include secrets or private robot telemetry.

Hardware support requests should include Pi model, OS image, bus, device/driver, wiring summary, and full error output. Real hardware support depends on the adapter matrix in `drivers/DRIVER_MATRIX.md`.
