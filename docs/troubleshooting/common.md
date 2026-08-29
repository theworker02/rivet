# Troubleshooting

## Import fails on a non-Pi machine

Use the core package without `.[pi]`; Pi-specific dependencies are optional. `python -c "import rivet"` must work without hardware.

## A motion command is rejected

Check `rivet preflight`, authority priority, owner identity, and actuator lease expiry. A role or passport does not replace either token.

## Simulator fault remains active

Create one `FaultInjector` per runtime and call `restore(target)` in the same process. CLI invocations are intentionally isolated and do not persist simulator state.

## Configuration cannot load

Core configuration currently accepts JSON. YAML is an explicit future adapter; the sample YAML manifest is documentation, not silently parsed by core startup.
