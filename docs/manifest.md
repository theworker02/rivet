# Versioned configuration

Rivet 1.2.0 uses schema version 2. `rivet init` writes canonical JSON:

```bat
python -m rivet init rover.json --robot-id rover-01
python -m rivet config validate rover.json
```

The root marker is `"rivet": 2`:

```json
{
  "rivet": 2,
  "robot": {"id": "rover-01", "platform": "simulator"},
  "simulate": true,
  "devices": {},
  "safety": {},
  "role": {}
}
```

Legacy v1 documents with a string `robot` or `capabilities` are migrated explicitly:

```bat
python -m rivet config migrate legacy.json --output robot-v2.json
```

Core startup accepts JSON and `.rivet` files. YAML manifests require a maintained adapter with schema tests; the repository example is documentation input, not silently parsed by the core.
