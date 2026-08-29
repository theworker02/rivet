# Robot arm intent example

The `motion-plan.json` file is an embodiment-neutral intent input. `EmbodimentCompiler` validates that a plan has operations before a runtime-specific executor lowers it to the existing command boundary. No physical arm is included or claimed; use simulator contracts and a qualified adapter before connecting hardware.

Validate the package and inspect the public motion surface with:

```bat
python -m rivet verify
python -m rivet discover
```
