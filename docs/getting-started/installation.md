# Installation

Rivet 1.2.0 requires Python 3.10 or newer and imports without Raspberry Pi libraries.

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m rivet version --verbose
python -m rivet verify
```

Optional extras are separated by concern:

- `.[pi]` — Pi-oriented GPIO dependency.
- `.[vision]` — numerical vision dependency.
- `.[dev]` — tests, lint, typing, and package build tooling.
- `.[docs]` — documentation tooling.

The default installation remains dependency-light for constrained systems. A successful installation is demonstrated by `rivet verify`, not by importing a package alone.
