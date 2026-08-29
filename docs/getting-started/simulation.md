# Simulation

Run the complete local backend without hardware:

```bat
python -m rivet run --simulate
python -m rivet run --simulate --fault motion.left-wheel
python -m rivet doctor --verbose
```

The simulator exposes motors, camera metadata, IMU metadata, and battery metadata. Fault injection disconnects a commandable device, invokes its safe state, publishes a fault event, and can restore the device in process. It is the supported development path on Windows, macOS, and Linux.
