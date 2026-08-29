<p align="center"><img src="assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# Rivet site

This is the dependency-free static documentation site for Rivet `1.2.0`, a verification-gated Beta release. `python tools/site/build.py` copies the source to `site-build/` for GitHub Pages deployment. The site uses the canonical Rivet SVG logo and generated simulator evidence under `assets/`; `tools/media/generate.py` regenerates the PNG and GIF visuals from real local runs.

The public pages describe the same bounded evidence as the package: `rivet verify` exercises the simulator and runtime seams, while physical adapters, production identity, process isolation, and certified safety hardware remain explicit integrations. No stock screenshots, fabricated hardware imagery, or unverified video is included.
