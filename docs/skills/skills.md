# Skills

SkillGraph records competence as evidence rather than a boolean. Each record can contain attempts, successes, simulator runs, dependencies, validation date, benchmarks, confidence decay, and history.

```bat
python -m rivet skills
python -m rivet skill explain construction.drilling
python -m rivet skill train manipulation.general
```

Hardware/calibration changes should call `SkillGraph.decay()` for affected capabilities and require revalidation. A skill level never grants a runtime authority token. Benchmark evidence may move competence through the role lifecycle only through explicit validation and operator authorization.
