# Rivet Link codec

`src/rivet/protocol.py` provides a dependency-free RVT/1 frame codec for UART/USB/CAN transport adapters. The codec is an implemented serialization boundary; a transport endpoint is still an explicit integration.

A frame contains magic `RVT1`, version, device/channel lengths, sequence, monotonic timestamp, payload length, UTF-8 device/channel names, payload bytes, and CRC32. Decoder length and CRC checks reject truncated, corrupt, or misrouted data before dispatch. Protocol behavior is covered by `tests/protocol/test_protocol.py` and is reported by `rivet version --verbose` as `RVT/1`.
