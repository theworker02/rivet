# Rivet Link codec

`src/rivet/protocol.py` provides a dependency-free frame codec for future UART/USB/CAN transports.

A frame contains magic `RVT1`, version, device/channel lengths, sequence, monotonic timestamp, payload length, UTF-8 device/channel names, payload bytes, and CRC32. Decoder length and CRC checks reject truncated, corrupt, or misrouted data before dispatch.
