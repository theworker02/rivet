# Contributing to Rivet

Thank you for contributing. Rivet is safety-oriented robotics infrastructure, so changes should be small, inspectable, and explicit about hardware assumptions. Rivet `1.2.0` is a verification-gated Beta: simulator evidence is executable, while physical support remains qualification- and deployment-review dependent.

## Development setup

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest
python tools\dev.py check
```

The core package must import without Raspberry Pi hardware or optional dependencies. Use the dependency-free simulator for local development and CI; do not make a physical adapter a prerequisite for a unit or integration test.

## Change expectations

- Preserve the existing `RobotRuntime` authority, lease, event, typed-contract, health, and safe-state boundaries.
- Add tests for behavior changes, especially fault, recovery, recorder, configuration, and safety behavior.
- Keep hardware dependencies optional and behind adapters.
- Do not claim physical hardware support without a driver contract, qualification evidence, safe-state behavior, and a mock or simulator test path.
- Do not add empty folders, placeholder modules, fake media, secrets, or fictional service links. Put executable logic in the canonical `src/`, `drivers/`, `sdk/`, `tests/`, `docs/`, `site/`, or `tools/` surfaces.
- Keep simulator evidence separate from hardware certification. A simulator PASS must never be labeled hardware-verified.
- Update `CHANGELOG.md` and the relevant user, safety, driver, mission, or deployment documentation for user-visible changes.

## Required validation

Before opening a pull request, run the checks that apply to the change:

```bat
python -m pytest
python -m ruff check src tests drivers sdk
python -m mypy src
python -m compileall -q src drivers sdk tests
python -m rivet verify
rivet-dev audit-content
python -m rivet check-release
python tools\site\build.py
```

The release gate checks tests, package metadata, generated `PKG-INFO`, entry points, schemas, examples, local Markdown links, static-site assets, and unfinished release code. `--skip-tests` and `--skip-build` are diagnostic switches only and must not be used as release evidence.

## Pull requests

Describe the behavior, validation commands, hardware assumptions, and safety implications. Include whether the change affects configuration schema, protocol identity (`RVT/1`), driver qualification, public API, or deprecation policy. A maintainer may request simulator or hardware-mock coverage before review.

## Release changes

Release changes must update the canonical source metadata in `pyproject.toml` and `src/rivet/version.py`, regenerate package metadata and `site-build/`, and keep `CHANGELOG.md`, README status, and workflow gates aligned. Do not manually claim physical certification, production identity, or certified emergency-stop behavior.
