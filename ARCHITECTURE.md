# Rivet architecture

Rivet is layered so high-level specialization cannot bypass low-level safety:

```text
Applications / AI / ROS / Web
             │
             ▼
      Vocation + Missions
             │
             ▼
 Continuum profiles + perception
             │
             ▼
       RobotRuntime + Bus
       │       │       │
   Guard   Leases   Authority
             │
             ▼
 Capability registry and driver contracts
             │
       GPIO / I²C / SPI / UART
```

The simulator and mock drivers implement the same observable contracts as the integration seams. See `docs/architecture.md` for the detailed Phase I–III model and `docs/architecture/overview.md` for the Phase IV repository map.
