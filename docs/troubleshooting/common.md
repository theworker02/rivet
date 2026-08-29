# Troubleshooting

## Import fails on a non-Pi machine

Use the core package without `.[pi]`; Pi-specific dependencies are optional. `python -c "import rivet"` must work without hardware, followed by `python -m rivet verify` for an installation check.

## A motion command is rejected

Check `rivet preflight`, `rivet pulse`, authority priority, owner identity, typed command ranges, capability health, and actuator lease expiry. A role or passport does not replace either token.

## Simulator fault remains active

Create one `FaultInjector` per runtime and call `restore(target)` in the same process. CLI invocations are intentionally isolated; use a recording or support bundle when diagnosing a separate process.

## Configuration cannot load

Core configuration is schema-v2 JSON. Validate or migrate it explicitly:

```bat
python -m rivet config validate robot.json
python -m rivet config migrate legacy.json --output robot-v2.json
```

YAML requires a maintained adapter and is not silently parsed by core startup.

## Release gate blocks

Run `python -m rivet check-release --skip-build --skip-tests` to inspect content, metadata, links, and examples first. Do not use skip flags for a release; rerun the full gate after fixing every issue.
