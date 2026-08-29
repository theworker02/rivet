<p align="center"><img src="../site/assets/rivet-logo.svg" alt="Rivet robotics infrastructure" width="520"></p>

# Reference drivers

This directory contains dependency-light reference drivers used by examples and hardware-mock validation. They are not bundled as Raspberry Pi production drivers.

- `gpio/mock_gpio.py` provides deterministic pin state.
- `motors/generic_pwm.py` provides a commandable PWM motor contract.
- `motors/tb6612.py` adds TB6612 pin metadata while leaving GPIO injection to deployment code.
- `cameras/mock_camera.py` provides metadata-only frame capture.
- `sensors/mock_sensor.py` provides injectable scalar telemetry.

Real GPIO, I²C, SPI, camera, and serial dependencies must remain optional so `import rivet` works on machines without Pi hardware.
