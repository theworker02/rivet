# Testing

Run the default suite:

```bat
python -m pytest
python -m compileall -q src drivers sdk tests
python tools\dev.py check
```

Tests cover runtime authority/lease safety, adaptive profiles, Vocation transitions, protocol CRC, mock buses and motors, fault injection, configuration/storage, driver registry, and CLI integration. Physical hardware tests are not claimed; hardware adapters must provide deterministic mock coverage first.
