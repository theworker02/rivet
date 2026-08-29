# Simulation

Run the complete local backend without hardware:

```bat
python -m rivet verify
python -m rivet run --simulate
python -m rivet run --simulate --fault motion.left-wheel
python -m rivet mission run "inspect zone A" --role inspection --dry-run
python -m rivet record start rover.rvt
python -m rivet timeline rover.rvt
```

The simulator exposes two motors, a commandable IMU, camera metadata, and battery metadata. Fault injection disconnects a commandable device, invokes its safe state, marks capability health failed, publishes a fault event, and supports restoration in process. It is the supported development path on Windows, macOS, and Linux and is the source of the 18 end-to-end verification scenarios.
