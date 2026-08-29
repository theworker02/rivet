<p align="center"><img src="../../site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# Packaging tooling

`pyproject.toml` is the source of package metadata. `tools/dev.py release-check` compiles, tests, runs CLI smoke checks, and builds the distribution when the `build` package and the pinned `setuptools` backend are installed. The CI workflow bootstraps that backend explicitly because `python -m build --no-isolation` does not create an isolated build environment.
