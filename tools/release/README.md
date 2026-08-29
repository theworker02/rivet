<p align="center"><img src="../../site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# Release tooling

Tagged releases use `.github/workflows/release.yml` to validate tests, build wheel/sdist artifacts, run `twine check`, and publish checksums as workflow artifacts. Package publication remains disabled until a verified package owner configures trusted publishing.

## Local release gate

Run the strict gate from the repository root:

```bat
python -m rivet check-release
```

It blocks on failed tests, invalid package metadata, broken local documentation links or assets, invalid schemas/examples, unfinished release code, and an unbuildable wheel or source distribution. Use `--skip-tests` or `--skip-build` only while diagnosing a local audit; they are not release-safe settings.

The developer content scan is also available as:

```bat
rivet-dev audit-content
```

Intentional marker classes must be listed explicitly in `[tool.rivet.audit]` in `pyproject.toml` and reviewed like code.
