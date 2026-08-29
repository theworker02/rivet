<p align="center"><img src="../site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# CLI architecture

The current public CLI is implemented in `src/rivet/cli.py` so the installed `rivet` entry point and `python -m rivet` remain identical. This directory documents the future extraction boundary for command handlers and formatters; new handlers should be moved only with compatibility tests.
