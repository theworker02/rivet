# Support

Rivet 1.2.0 support reports should include verified evidence, not only a stack trace:

```bat
python -m rivet version --verbose
python -m rivet verify --json > verification.json
python -m rivet doctor --verbose
python -m rivet support bundle rivet-support.zip
```

For a reproducible issue, include the sanitized support bundle, command, simulator output, and the smallest relevant configuration. `rivet crash inspect latest` reads persistent crash records under `~/.rivet/crashes/`.

Bundles include system/version information, schema/protocol identifiers, capability and health status, verification results, and non-sensitive diagnostics. They omit secrets, API credentials, private keys, raw camera footage, and private sensor content by default. Hardware reports should also include Pi model, OS, bus, device/driver, wiring summary, qualification metadata, and full error output.
