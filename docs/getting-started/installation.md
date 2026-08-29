# Installation

Rivet requires Python 3.10 or newer and imports without Raspberry Pi libraries.

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
python -m rivet version
```

Optional extras are separated by concern:

- `.[pi]` — Pi-oriented GPIO dependency.
- `.[vision]` — numerical vision dependency.
- `.[dev]` — tests and static tooling.
- `.[docs]` — documentation tooling.

The default installation remains dependency-light for constrained systems.
