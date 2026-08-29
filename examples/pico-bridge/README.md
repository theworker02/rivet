<p align="center"><img src="../../site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# Pico bridge extension point

`rivet.protocol.FrameCodec` provides the binary frame boundary for a future UART/USB/CAN bridge. The repository currently includes a deterministic `MockUART`; a physical Pico firmware adapter must add framing, watchdog, reconnect, and hardware-in-the-loop validation.
