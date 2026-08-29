# Skills

SkillGraph records competence as evidence rather than a boolean. Each record can contain attempts, successes, simulator runs, dependencies, validation date, benchmarks, and history.

```bat
python -m rivet skill explain construction.drilling
python -m rivet skill train manipulation.general
```

Hardware/calibration changes should call `SkillGraph.decay()` for affected capabilities and require revalidation.
