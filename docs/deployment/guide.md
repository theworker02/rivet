# Deployment

Rivet 1.2.0 is designed for simulator-first development and explicit deployment review. On a Raspberry Pi, install only the needed `pi` and device extras, validate the version and configuration, run the full verification path, then run preflight before motion:

```bat
python -m rivet version --verbose
python -m rivet config validate robot.json
python -m rivet verify --config robot.json
python -m rivet preflight
```

Keep Guard, hardware/MCU watchdogs, actuator power removal, and high-level perception in independently reviewable boundaries. Use `rivet support bundle` for sanitized diagnostics and never use the development HMAC signer for fleet identity. No cloud service is required; offline operation is an intentional design point.

The compatibility matrix and driver qualification report are deployment evidence, not a substitute for electrical, mechanical, emergency-stop, regulatory, and operational review.
