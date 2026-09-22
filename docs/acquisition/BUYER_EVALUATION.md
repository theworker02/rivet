# Buyer evaluation â€” rivet

## Goal

In 15â€“45 minutes, verify the Product builds or runs as documented and that proprietary notices are present.

## Steps

1. Confirm root `LICENSE` is proprietary and `ACQUISITION.md` exists.
2. Skim `README.md` install/run claims.
3. Execute:

```
```bat
python -m pip install --upgrade rivet-robot-runtime==1.2.0
rivet version --verbose
rivet verify
```
```bat
rivet --help
rivet-dev --help
rivet-dev audit-content
```
```bat
python -m pip install --upgrade rivet-robot-runtime
python -m rivet version
```
```text
rivet_robot_runtime-1.2.0-py3-none-any.whl
5ee535e3d61e802f71a37defdacf6e3dcb2a50ed8a846e2eab84ef5103e30040

rivet_robot_runtime-1.2.0.tar.gz
4845c873f25eeefde0f4d27663a165f5c3f731231c1f5309dadb829902a4b3e3
```
```bat
certutil -hashfile rivet_robot_runtime-1.2.0-py3-none-any.whl SHA256
certutil -hashfile rivet_robot_runtime-1.2.0.tar.gz SHA256
```
```bash
sha256sum rivet_robot_runtime-1.2.0-py3-none-any.whl
sha256sum rivet_robot_runtime-1.2.0.tar.gz
```
```text
Applications / AI / ROS / Web
              Ã¢â€â€š
              Ã¢â€“Â¼
 VocationRuntime Ã¢â‚¬â€ roles, skills, missions, teams
              Ã¢â€â€š
              Ã¢â€“Â¼
 ContinuumRuntime Ã¢â‚¬â€ profiles, perception, resources, cluster
              Ã¢â€â€š
              Ã¢â€“Â¼
 RobotRuntime Ã¢â‚¬â€ devices, capabilities, authority, leases
```

4. Run tests if present (`npm test`, `pytest`, `cargo test`, `go test ./...`, etc.).
5. Record README vs observed behavior gaps in workpapers.

## Pass criteria

- [ ] Clone succeeds
- [ ] Documented happy path works **or** failure is explained
- [ ] Minimal path needs no surprise secrets
- [ ] License notices intact

*Updated: 2026-09-22*
