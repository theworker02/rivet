# Roles

Roles describe what a robot is qualified and authorized to do. They do not grant actuator authority.

```text
candidate → trained → validated → authorized
```

Use `rivet role evaluate` to inspect hardware and SkillGraph compatibility. Operator authorization remains a separate transition. Restrictions and prohibited actions belong in the role policy and must be enforced by the mission admission layer.
