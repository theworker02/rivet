# Driver matrix

| Area | Reference implementation | Hardware dependency |
|---|---|---|
| GPIO | `gpio/mock_gpio.py` | none |
| I²C | `i2c/mock_i2c.py` | none |
| SPI | `spi/mock_spi.py` | none |
| UART | `uart/mock_uart.py` | none |
| Motor | `motors/generic_pwm.py`, `tb6612.py` | injected GPIO |
| Camera | `cameras/mock_camera.py` | none |
| Sensors | `sensors/mock_sensor.py` | none |

The reference implementations provide test seams, not a claim that they can drive a specific physical board without a deployment adapter.
