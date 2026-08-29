# Contributing to Rivet

Thank you for contributing. Rivet is safety-oriented robotics infrastructure, so changes should be small, inspectable, and explicit about hardware assumptions.

## Development setup

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m pytest
python tools\dev.py check
```

The core package must import without Raspberry Pi hardware or optional dependencies.

## Change expectations

- Preserve the existing `RobotRuntime` authority, lease, event, and safe-state boundaries.
- Add tests for behavior changes, especially fault and safety behavior.
- Keep hardware dependencies optional and behind adapters.
- Do not claim physical hardware support without a driver contract and mock/test backend.
- Do not add empty folders, placeholder modules, fake media, secrets, or fictional service links.
- Update `CHANGELOG.md` and relevant docs for user-visible changes.

## Pull requests

Describe the behavior, validation commands, hardware assumptions, and safety implications. A maintainer may request simulator or hardware-mock coverage before review.
