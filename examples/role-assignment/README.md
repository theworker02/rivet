<p align="center"><img src="../../site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# Role assignment example

Run the default role evaluation and then inspect the prerequisite-aware skill graph:

```bat
set PYTHONPATH=src
python -m rivet role evaluate search-rescue
python -m rivet skill explain construction.drilling
```

Evaluation reports compatibility; it does not silently authorize a role.
