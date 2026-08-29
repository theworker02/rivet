# Roles

Roles describe what a robot is qualified and authorized to do. They do not grant actuator authority.

```text
candidate → trained → validated → authorized → active transition
```

Use:

```bat
python -m rivet role evaluate inspection
python -m rivet role adopt inspection
python -m rivet verify
```

`RoleManager` evaluates required skills and registered hardware, then requires separate training, validation, and operator authorization. Mission admission consumes the authorized state; authority grants, leases, Guard, health, and preflight remain independent. Restrictions and prohibited actions belong in the role policy and must be enforced by mission/action policy rather than treated as decoration.
