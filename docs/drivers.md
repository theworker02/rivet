# Hardware support guide

Use `drivers/DRIVER_MATRIX.md` for the current reference adapter matrix. Core Rivet deliberately does not import `RPi.GPIO`, camera, serial, or numerical libraries at import time. Add hardware support behind a driver and preserve a mock path for unsupported hosts.
