# Pico bridge frame boundary

`rivet.protocol.FrameCodec` implements the binary `RVT/1` frame boundary, and `frame.json` records a deterministic example payload. The repository does not claim a physical Pico firmware adapter: a deployment adapter must add transport framing, watchdog, reconnect, and hardware-in-the-loop validation before it can be qualified.

Exercise the implemented protocol and simulator paths with:

```bat
python -m pytest tests/protocol tests/hardware -q
python -m rivet verify
```
