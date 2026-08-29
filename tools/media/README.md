<p align="center"><img src="../../site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# Media generation

This tool generates Rivet’s README and site visual evidence from real local simulator and diagnostic runs.

```bat
python tools\media\generate.py
```

It writes the following source assets to `site/assets/`:

- `rivet-doctor.png` — rendered output from `python -m rivet doctor --verbose`.
- `rivet-simulator.png` — rendered capability inventory from `python -m rivet run --simulate`.
- `rivet-fault-injection.gif` — an animation of nominal, disconnect, and restore states using the `FaultInjector` API.

Pillow is a tooling-only dependency. It is not imported by the Rivet runtime and is not required to run the simulator or package.
